"""
Module de gestion des flux vidéo
"""

import cv2
import numpy as np
from typing import Optional
import config

class CameraStream:
    """
    Gère la capture vidéo d'une webcam
    """

    def __init__(self, camera_id: int):
        self.camera_id = camera_id
        self.cap = None
        self.is_active = False

    def start(self) -> bool:
        """
        Démarre la capture vidéo
        Retourne True si succès, False sinon
        """
        try:
            self.cap = cv2.VideoCapture(self.camera_id)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
            self.cap.set(cv2.CAP_PROP_FPS, config.FPS)

            if not self.cap.isOpened():
                print(f"Erreur: impossible d'ouvrir la caméra {self.camera_id}")
                return False

            self.is_active = True
            print(f"Caméra {self.camera_id} démarrée")
            return True

        except Exception as e:
            print(f"Erreur lors du démarrage de la caméra: {e}")
            return False

    def get_frame(self) -> Optional[np.ndarray]:
        """
        Capture une frame
        Retourne la frame ou None en cas d'erreur
        """
        if not self.is_active or self.cap is None:
            return None

        ret, frame = self.cap.read()
        if not ret:
            return None

        return frame

    def stop(self):
        """Arrête la capture et libère les ressources"""
        if self.cap is not None:
            self.cap.release()
            self.is_active = False

    def __del__(self):
        self.stop()
