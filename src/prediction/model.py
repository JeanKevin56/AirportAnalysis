"""
Module de prédiction de flux à 30 secondes
Utilise la régression linéaire sur l'historique récent
"""

import numpy as np
from typing import List, Optional
from collections import deque
import config


class FlowPredictor:
    """
    Prédit le flux de personnes à 30 secondes
    """

    def __init__(self, history_size: int = None):
        self.history_size = history_size or config.HISTORY_SIZE
        self.history = deque(maxlen=self.history_size)

    def add_measurement(self, count: int):
        """Ajoute une mesure à l'historique"""
        self.history.append(count)

    def predict(self, method: str = "linear") -> Optional[float]:
        """
        Prédit le flux à 30 secondes
        Retourne la prédiction ou None si pas assez de données
        """
        if len(self.history) < 3:
            return None

        if method == "linear":
            return self._linear_regression()
        elif method == "moving_average":
            return self._moving_average()
        else:
            return self._moving_average()

    def _linear_regression(self) -> float:
        """
        Régression linéaire sur l'historique
        Extrapole à 30 secondes
        """
        data = np.array(self.history)
        n = len(data)
        x = np.arange(n)

        x_mean = np.mean(x)
        y_mean = np.mean(data)

        numerator = np.sum((x - x_mean) * (data - y_mean))
        denominator = np.sum((x - x_mean) ** 2)

        if denominator == 0:
            return float(y_mean)

        slope = numerator / denominator
        intercept = y_mean - slope * x_mean

        steps_ahead = config.PREDICTION_HORIZON / config.SAMPLING_INTERVAL
        next_x = n + steps_ahead
        prediction = slope * next_x + intercept

        return max(0, prediction)

    def _moving_average(self) -> float:
        """Moyenne mobile simple"""
        return float(np.mean(self.history))

    def get_trend(self) -> str:
        """
        Analyse la tendance
        Retourne "hausse", "baisse", ou "stable"
        """
        if len(self.history) < 3:
            return "stable"

        recent = list(self.history)[-3:]

        if recent[-1] > recent[0] * 1.1:
            return "hausse"
        elif recent[-1] < recent[0] * 0.9:
            return "baisse"
        else:
            return "stable"

    def get_history(self) -> List[int]:
        """Retourne l'historique complet"""
        return list(self.history)
