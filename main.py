

import argparse
import time
import cv2
import signal
import sys
import os
import json
import datetime
import config
from src.acquisition.camera_stream import CameraStream
from src.acquisition.network_comm import NetworkServer, NetworkClient
from src.processing.tracker import PeopleTracker
from src.prediction.model import FlowPredictor
from src.visualization.dashboard import FlowDashboard, FrameAnnotator


class AeroFlowApp:
    """Application principale AeroFlow"""

    def __init__(self, mode: str, camera_id: int, master_ip: str = None):
        self.mode = mode
        self.camera_id = camera_id
        self.master_ip = master_ip

        self.camera = CameraStream(camera_id)
        self.tracker = PeopleTracker(use_yolo=True)

        if mode == "master":
            self.predictor = FlowPredictor()
            self.dashboard = FlowDashboard()
            self.server = NetworkServer(callback=self.on_remote_count)
            self.remote_count = 0
        else:
            self.client = NetworkClient(master_ip)

        self.is_running = False
        self.session_start_time = time.time()
        self.session_start_iso = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        self.session_records = []
        signal.signal(signal.SIGINT, self.signal_handler)

    def signal_handler(self, sig, frame):
        print("\nArret demande...")
        self.is_running = False

    def on_remote_count(self, count: int):
        self.remote_count = count

    def run_master(self):
        print("Demarrage en mode MAITRE (PC A)")

        if not self.camera.start():
            return

        self.server.start()
        self.is_running = True

        print(f"AeroFlow actif - Mode optimise")
        print(f"Resolution: {config.FRAME_WIDTH}x{config.FRAME_HEIGHT}")
        print(f"Appuyer sur 'q' pour quitter ou Ctrl+C")

        cv2.namedWindow(config.WINDOW_NAME_MASTER, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(config.WINDOW_NAME_MASTER, config.FRAME_WIDTH, config.FRAME_HEIGHT)

        last_sample_time = time.time()
        frame_count = 0
        dashboard_counter = 0

        # Variables pour les dernières valeurs (éviter recalculs)
        last_prediction = None
        last_trend = "stable"

        try:
            while self.is_running:
                frame = self.camera.get_frame()
                if frame is None:
                    time.sleep(0.01)
                    continue

                # Détection (avec skip frames intégré dans tracker)
                count_a, bboxes = self.tracker.detect_people(frame)

                # Échantillonnage périodique
                current_time = time.time()
                if current_time - last_sample_time >= config.SAMPLING_INTERVAL:
                    total_count = count_a + self.remote_count
                    self.predictor.add_measurement(total_count)
                    last_sample_time = current_time

                    # Calculer prédiction et tendance seulement lors de l'échantillonnage
                    last_prediction = self.predictor.predict("linear")
                    last_trend = self.predictor.get_trend()

                    self.session_records.append({
                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                        "local_count": int(count_a),
                        "remote_count": int(self.remote_count),
                        "total_count": int(total_count),
                        "prediction": None if last_prediction is None else float(last_prediction),
                        "trend": last_trend
                    })
                # Annotation simple et rapide
                annotated = self.tracker.draw_detections(frame, bboxes, count_a)
                annotated = FrameAnnotator.annotate_frame(
                    annotated, count_a, "A", "Maitre", last_prediction
                )

                # Afficher la frame
                cv2.imshow(config.WINDOW_NAME_MASTER, annotated)

                # Mettre à jour le dashboard MOINS SOUVENT
                dashboard_counter += 1
                update_interval = getattr(config, 'UPDATE_DASHBOARD_EVERY', 5)
                if dashboard_counter >= update_interval:
                    history = self.predictor.get_history()
                    self.dashboard.update(history, last_prediction, count_a, 
                                         self.remote_count, last_trend)
                    dashboard_counter = 0

                # Attendre moins longtemps pour plus de fluidité
                key = cv2.waitKey(10) & 0xFF
                if key == ord('q') or key == 27:
                    print("Arret demande...")
                    break

                frame_count += 1
                if frame_count > 10:
                    try:
                        if cv2.getWindowProperty(config.WINDOW_NAME_MASTER, cv2.WND_PROP_VISIBLE) < 1:
                            print("Fenetre fermee...")
                            break
                    except:
                        pass

        except KeyboardInterrupt:
            print("\nInterruption Ctrl+C")
        except Exception as e:
            print(f"Erreur: {e}")
        finally:
            self.cleanup()

    def run_slave(self):
        print(f"Demarrage en mode ESCLAVE (PC B)")
        print(f"Connexion au maitre: {self.master_ip}:{config.NETWORK_PORT}")

        if not self.camera.start():
            return

        self.is_running = True

        print(f"Camera B active - Mode optimise")
        print(f"Resolution: {config.FRAME_WIDTH}x{config.FRAME_HEIGHT}")
        print(f"Appuyer sur 'q' pour quitter")

        cv2.namedWindow(config.WINDOW_NAME_SLAVE, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(config.WINDOW_NAME_SLAVE, config.FRAME_WIDTH, config.FRAME_HEIGHT)

        last_send_time = time.time()
        frame_count = 0

        try:
            while self.is_running:
                frame = self.camera.get_frame()
                if frame is None:
                    time.sleep(0.01)
                    continue

                count_b, bboxes = self.tracker.detect_people(frame)

                current_time = time.time()
                if current_time - last_send_time >= config.SAMPLING_INTERVAL:
                    self.client.send_count(count_b)
                    last_send_time = current_time
                    self.session_records.append({
                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                        "local_count": int(count_b)
                    })

                annotated = self.tracker.draw_detections(frame, bboxes, count_b)
                annotated = FrameAnnotator.annotate_frame(
                    annotated, count_b, "B", "Esclave"
                )

                cv2.imshow(config.WINDOW_NAME_SLAVE, annotated)

                key = cv2.waitKey(10) & 0xFF
                if key == ord('q') or key == 27:
                    print("Arret demande...")
                    break

                frame_count += 1
                if frame_count > 10:
                    try:
                        if cv2.getWindowProperty(config.WINDOW_NAME_SLAVE, cv2.WND_PROP_VISIBLE) < 1:
                            print("Fenetre fermee...")
                            break
                    except:
                        pass

        except KeyboardInterrupt:
            print("\nInterruption Ctrl+C")
        except Exception as e:
            print(f"Erreur: {e}")
        finally:
            self.cleanup()

    def cleanup(self):
        print("\nNettoyage...")
        self.is_running = False
        self.camera.stop()

        if self.mode == "master":
            self.server.stop()
            self.dashboard.close()

        self.save_session_data()

        cv2.destroyAllWindows()
        for _ in range(5):
            cv2.waitKey(1)

        print("Programme termine.")

    def save_session_data(self):
        if not self.session_records:
            print("Aucune donnée de session à enregistrer.")
            return

        os.makedirs(config.DATA_DIR, exist_ok=True)

        filename = f"session_{self.mode}_{self.camera_id}_{self.session_start_iso.replace(':', '-')}.json"
        filepath = os.path.join(config.DATA_DIR, filename)

        session_data = {
            "mode": self.mode,
            "camera_id": self.camera_id,
            "master_ip": self.master_ip,
            "start_time": self.session_start_iso,
            "end_time": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "duration_seconds": round(time.time() - self.session_start_time, 2),
            "sample_count": len(self.session_records),
            "records": self.session_records,
        }

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            print(f"Données de session enregistrées dans : {filepath}")
        except Exception as e:
            print(f"Erreur lors de l'enregistrement des données de session : {e}")


def main():
    parser = argparse.ArgumentParser(description="AeroFlow - Version optimisee")
    parser.add_argument("--mode", choices=["master", "slave"], required=True)
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--master-ip", type=str, default=config.MASTER_IP)

    args = parser.parse_args()

    if args.mode == "slave" and not args.master_ip:
        print("Erreur: mode slave necessite --master-ip")
        return

    print("="*60)
    print("AeroFlow - Version Ultra-Optimisee")
    print("="*60)

    app = AeroFlowApp(args.mode, args.camera, args.master_ip)

    if args.mode == "master":
        app.run_master()
    else:
        app.run_slave()


if __name__ == "__main__":
    main()
