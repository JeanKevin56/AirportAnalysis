"""
Module de détection et comptage de personnes avec YOLO
Version optimisée pour meilleures performances
"""

import cv2
import numpy as np
from typing import Tuple, List
import config

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("Warning: ultralytics non installé, mode simulation activé")


class PeopleTracker:
    """
    Détecte et compte les personnes dans une frame vidéo
    """

    def __init__(self, use_yolo: bool = True):
        self.use_yolo = use_yolo and YOLO_AVAILABLE
        self.model = None
        self.last_count = 0
        self.last_bboxes = []
        self.frame_counter = 0

        if self.use_yolo:
            try:
                print(f"Chargement du modèle {config.YOLO_MODEL}...")
                self.model = YOLO(config.YOLO_MODEL)
                print("Modèle chargé")
            except Exception as e:
                print(f"Erreur chargement YOLO: {e}")
                self.use_yolo = False

    def detect_people(self, frame: np.ndarray, force_detect: bool = False) -> Tuple[int, List[Tuple[int, int, int, int]]]:
        """
        Détecte les personnes dans une frame
        Utilise le skip_frames pour optimiser les performances

        Args:
            frame: Image numpy array
            force_detect: Force la détection même si on devrait skip

        Retourne (nombre_personnes, liste_bbox)
        """
        if frame is None:
            return 0, []

        # Optimisation: skip frames pour réduire la charge CPU
        if not force_detect and hasattr(config, 'SKIP_FRAMES'):
            self.frame_counter += 1
            if self.frame_counter % config.SKIP_FRAMES != 0:
                # Retourner les dernières détections
                return self.last_count, self.last_bboxes

        if self.use_yolo and self.model is not None:
            count, bboxes = self._detect_with_yolo(frame)
        else:
            count, bboxes = self._simulate_detection(frame)

        # Sauvegarder pour réutilisation
        self.last_count = count
        self.last_bboxes = bboxes

        return count, bboxes

    def _detect_with_yolo(self, frame: np.ndarray) -> Tuple[int, List[Tuple[int, int, int, int]]]:
        """Détection avec YOLO optimisée"""
        try:
            # Utiliser une taille d'image réduite pour accélérer
            img_size = getattr(config, 'YOLO_IMG_SIZE', 640)

            results = self.model(frame, verbose=False, imgsz=img_size)

            bboxes = []
            for result in results:
                boxes = result.boxes

                for box in boxes:
                    if int(box.cls[0]) == config.DETECTION_CLASS:
                        confidence = float(box.conf[0])

                        if confidence >= config.CONFIDENCE_THRESHOLD:
                            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                            bboxes.append((int(x1), int(y1), int(x2), int(y2)))

            return len(bboxes), bboxes

        except Exception as e:
            print(f"Erreur détection YOLO: {e}")
            return 0, []

    def _simulate_detection(self, frame: np.ndarray) -> Tuple[int, List[Tuple[int, int, int, int]]]:
        """Mode simulation sans YOLO"""
        import random
        count = random.randint(0, 5)

        h, w = frame.shape[:2]
        bboxes = []
        for _ in range(count):
            x1 = random.randint(0, w - 100)
            y1 = random.randint(0, h - 150)
            x2 = x1 + random.randint(50, 100)
            y2 = y1 + random.randint(100, 150)
            bboxes.append((x1, y1, x2, y2))

        return count, bboxes

    def draw_detections(self, frame: np.ndarray, bboxes: List[Tuple[int, int, int, int]], 
                       count: int) -> np.ndarray:
        """Dessine les détections sur la frame"""
        annotated = frame.copy()

        colors = [
            (0, 255, 0),
            (255, 0, 255),
            (0, 255, 255),
            (255, 255, 0),
            (255, 128, 0),
        ]

        for idx, (x1, y1, x2, y2) in enumerate(bboxes):
            color = colors[idx % len(colors)]

            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 3)

            label = f"#{idx+1}"
            font_scale = 0.8
            thickness = 2
            (text_width, text_height), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 
                                                          font_scale, thickness)

            cv2.rectangle(annotated, (x1, y1 - text_height - 10), 
                         (x1 + text_width + 10, y1), color, -1)

            cv2.putText(annotated, label, (x1 + 5, y1 - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 0), thickness)

        return annotated
