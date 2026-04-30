"""
Module de visualisation en temps réel
Dashboard optimisé avec panneau d'info repositionné
"""

import cv2
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from typing import List, Optional
from datetime import datetime
import config


class FlowDashboard:
    """
    Tableau de bord de visualisation des flux
    """

    def __init__(self):
        self.fig = None
        self.ax1 = None
        self.ax2 = None
        self.setup_plot()

    def setup_plot(self):
        """Configure le graphique matplotlib"""
        plt.ion()

        self.fig = plt.figure(figsize=(config.GRAPH_WIDTH, config.GRAPH_HEIGHT))
        self.fig.suptitle('AeroFlow - Dashboard de suivi des flux', 
                         fontsize=16, fontweight='bold')

        self.ax1 = plt.subplot(2, 1, 1)
        self.ax2 = plt.subplot(2, 1, 2)

        plt.tight_layout(rect=[0, 0, 1, 0.96])

    def update(self, history: List[int], prediction: Optional[float], 
               current_a: int, current_b: int, trend: str):
        """Met à jour le dashboard"""

        try:
            self.ax1.clear()
            self.ax2.clear()

            # Graphique 1: Historique et prédiction
            if len(history) > 0:
                x = list(range(len(history)))

                self.ax1.plot(x, history, 'b-', linewidth=3, label='Flux total observe')
                self.ax1.scatter(x, history, s=80, c='blue', zorder=5, alpha=0.6)

                if prediction is not None and len(history) >= 3:
                    steps_ahead = config.PREDICTION_HORIZON / config.SAMPLING_INTERVAL
                    pred_x = len(history) - 1 + steps_ahead

                    self.ax1.plot([len(history)-1, pred_x], [history[-1], prediction], 
                               'r--', linewidth=3, label=f'Prediction +{config.PREDICTION_HORIZON}s',
                               alpha=0.8)

                    self.ax1.scatter([pred_x], [prediction], 
                                   s=200, c='red', marker='*', 
                                   zorder=10, edgecolors='darkred', linewidth=2)

                    recent_std = max(np.std(history[-3:]), 0.5)
                    self.ax1.fill_between([len(history)-1, pred_x],
                                        [history[-1] - recent_std, prediction - recent_std],
                                        [history[-1] + recent_std, prediction + recent_std],
                                        alpha=0.2, color='red', label='Zone de confiance')

            self.ax1.set_xlabel('Mesures (intervalle: {}s)'.format(config.SAMPLING_INTERVAL), 
                              fontsize=12, fontweight='bold')
            self.ax1.set_ylabel('Nombre de personnes', fontsize=12, fontweight='bold')
            self.ax1.set_title('Evolution du flux et prediction', fontsize=13, pad=10)

            handles, labels = self.ax1.get_legend_handles_labels()
            if handles:
                self.ax1.legend(loc='upper left', fontsize=10)

            self.ax1.grid(True, alpha=0.3, linestyle='--')

            if len(history) > 0:
                y_max = max(max(history), prediction if prediction else 0) * 1.2
                self.ax1.set_ylim(0, max(y_max, 5))

            # Graphique 2: Répartition caméras
            cameras = ['Camera A', 'Camera B', 'Total']
            counts = [current_a, current_b, current_a + current_b]
            colors = ['#3498db', '#e74c3c', '#2ecc71']

            bars = self.ax2.bar(cameras, counts, color=colors, alpha=0.7, 
                               edgecolor='black', linewidth=2)

            for bar, count in zip(bars, counts):
                height = bar.get_height()
                self.ax2.text(bar.get_x() + bar.get_width()/2., height,
                            f'{int(count)}',
                            ha='center', va='bottom', fontsize=14, fontweight='bold')

            self.ax2.set_ylabel('Nombre de personnes', fontsize=12, fontweight='bold')
            self.ax2.set_title('Repartition actuelle par camera', fontsize=13, pad=10)
            self.ax2.grid(True, alpha=0.3, axis='y', linestyle='--')
            self.ax2.set_ylim(0, max(max(counts), 5) * 1.3)

            # Panneau d'informations déplacé en HAUT À DROITE du graphique
            info_text = self._format_info_panel(current_a, current_b, trend, prediction, history)

            # Positionner en haut à droite (x=0.98, y=0.98) au lieu d'en bas
            self.fig.text(0.98, 0.98, info_text, fontsize=10,
                         bbox=dict(boxstyle='round,pad=0.8', facecolor='lightblue', 
                                  alpha=0.9, edgecolor='black', linewidth=1.5),
                         verticalalignment='top',  # top au lieu de bottom
                         horizontalalignment='right',  # right pour aligner à droite
                         family='monospace')

            plt.tight_layout(rect=[0, 0.01, 1, 0.96])
            self.fig.canvas.draw()
            self.fig.canvas.flush_events()

        except Exception as e:
            print(f"Erreur mise a jour dashboard: {e}")

    def _format_info_panel(self, current_a, current_b, trend, prediction, history):
        """Formatte le panneau d'informations de manière compacte"""
        total = current_a + current_b

        info = f"STATISTIQUES\n"
        info += f"{'-'*30}\n"
        info += f"Cam A: {current_a:2d} | Cam B: {current_b:2d}\n"
        info += f"Total: {total:2d} personnes\n"
        info += f"{'-'*30}\n"
        info += f"Tendance: {trend.upper()}\n"

        if prediction is not None:
            info += f"Pred 30s: {prediction:3.0f}\n"
            variation = prediction - total
            info += f"Delta   : {variation:+.0f}\n"

        if len(history) >= 2:
            avg = np.mean(history)
            info += f"{'-'*30}\n"
            info += f"Moy: {avg:3.1f}\n"
            info += f"Min: {min(history)} Max: {max(history)}\n"

        return info

    def close(self):
        """Ferme le dashboard"""
        try:
            plt.close(self.fig)
        except:
            pass


class FrameAnnotator:
    """
    Ajoute des annotations sur les frames vidéo
    """

    @staticmethod
    def annotate_frame(frame: np.ndarray, count: int, camera_name: str, 
                      mode: str, prediction: Optional[float] = None) -> np.ndarray:
        """Ajoute des informations sur la frame"""
        if frame is None:
            return None

        annotated = frame.copy()
        h, w = annotated.shape[:2]

        # Fond semi-transparent
        overlay = annotated.copy()
        cv2.rectangle(overlay, (0, 0), (w, 100), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, annotated, 0.3, 0, annotated)

        # Texte principal
        text1 = f"Camera {camera_name} ({mode})"
        text2 = f"Personnes: {count}"

        cv2.putText(annotated, text1, (15, 35), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        cv2.putText(annotated, text2, (15, 75), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)

        # Prédiction
        if prediction is not None and mode == "Maitre":
            text3 = f"Prediction 30s: {prediction:.0f}"
            text_size = cv2.getTextSize(text3, cv2.FONT_HERSHEY_SIMPLEX, 0.9, 2)[0]
            cv2.putText(annotated, text3, (w - text_size[0] - 15, 75), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)

        # Timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")
        cv2.putText(annotated, timestamp, (w - 150, 35), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 2)

        return annotated
