# Guide de résolution des problèmes

## Erreur NumPy / OpenCV

Si vous rencontrez l'erreur "AttributeError: _ARRAY_API not found", suivez ces étapes :

### Solution 1 : Réinstaller avec les bonnes versions
```bash
pip uninstall numpy opencv-python
pip install numpy<2.0.0
pip install opencv-python
```

### Solution 2 : Environnement virtuel propre (RECOMMANDÉ)
```bash
# Créer un environnement virtuel
python -m venv venv

# Activer l'environnement
# Windows :
venv\Scripts\activate
# Linux/Mac :
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt
```

### Solution 3 : Installation manuelle
```bash
pip install numpy==1.24.3
pip install opencv-python==4.8.1.78
pip install ultralytics
pip install matplotlib pandas scipy
pip install torch torchvision
```

## Mode test sans YOLO

Si vous voulez tester sans installer YOLO (plus rapide) :
```bash
pip install numpy<2.0.0
pip install opencv-python
pip install matplotlib
```

Le programme fonctionnera en mode simulation.

## Vérification de l'installation
```python
python -c "import cv2; print(cv2.__version__)"
python -c "import numpy; print(numpy.__version__)"
```
