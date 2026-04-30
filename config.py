"""
Configuration du projet AeroFlow - Ultra optimisée
"""

# Réseau
MASTER_IP = "192.168.1.100"
NETWORK_PORT = 5555
BUFFER_SIZE = 1024

# Caméras - Résolution réduite pour max performances
CAMERA_A_ID = 0
CAMERA_B_ID = 1
FRAME_WIDTH = 640   # Résolution standard
FRAME_HEIGHT = 480
FPS = 30

# Détection - Optimisations maximales
YOLO_MODEL = "yolov8n.pt"  # Nano = le plus rapide
CONFIDENCE_THRESHOLD = 0.5
DETECTION_CLASS = 0
YOLO_IMG_SIZE = 320  # Très petit pour vitesse max

# Prédiction
HISTORY_SIZE = 10
PREDICTION_HORIZON = 30
SAMPLING_INTERVAL = 3

# Visualisation
WINDOW_NAME_MASTER = "AeroFlow - PC A (Maitre)"
WINDOW_NAME_SLAVE = "AeroFlow - PC B (Esclave)"
PLOT_UPDATE_INTERVAL = 2  # Mettre à jour le graphique moins souvent

# Graphique matplotlib
GRAPH_WIDTH = 10  # Réduit pour moins de charge
GRAPH_HEIGHT = 6
GRAPH_DPI = 80

# Performance - Optimisations critiques
SKIP_FRAMES = 3  # Traiter 1 frame sur 3 au lieu de 2
UPDATE_DASHBOARD_EVERY = 5  # Mettre à jour le dashboard toutes les 5 frames seulement

# Données
DATA_DIR = "data"
HISTORY_FILE = "data/flux_history.csv"
