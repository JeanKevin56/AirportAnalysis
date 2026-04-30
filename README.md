AeroFlow

Présentation du projet :
AeroFlow est un projet de suivi de flux de personnes à partir de deux webcams placées sur deux PC différents. L'idée de base vient du projet plus large présenté pour l'aéroport, où le but était de suivre les déplacements humains, de compter les personnes, puis d'anticiper les flux futurs pour mieux organiser les ressources​.

Dans notre version, on a volontairement simplifié le système pour avoir quelque chose de réaliste à faire tourner dans un cadre étudiant. Au lieu d'un grand réseau de caméras et de données Wi-Fi, on utilise seulement deux webcams, avec deux ordinateurs qui communiquent entre eux. Le PC A joue le rôle de machine principale, et le PC B envoie simplement ses comptages au PC A. L'objectif est de garder une architecture propre, compréhensible et assez simple à lancer.

Le projet repose sur quatre idées principales qu'on retrouve aussi dans la présentation d'origine : acquisition, comptage, prédiction et visualisation​. Ici, l'acquisition se fait par webcam, le comptage par vision par ordinateur, la prédiction sur une fenêtre très courte de 30 secondes, et la visualisation avec une interface locale simple.

Ce que fait concrètement le projet
Le système récupère les images des deux webcams en temps réel. Chaque PC analyse localement sa propre caméra pour estimer combien de personnes sont présentes dans le champ. Ensuite, le PC B n'envoie pas la vidéo au PC A : il envoie seulement un nombre, ce qui est beaucoup plus léger en réseau.

Le PC A récupère donc deux informations :

son propre comptage local 

le comptage envoyé par le PC B.

À partir de ça, il calcule un total, conserve un petit historique, puis estime le flux attendu dans 30 secondes. En parallèle, il affiche la vidéo annotée, les informations courantes et un graphique simple de l'évolution du comptage.

Pourquoi cette version est cohérente avec le projet de base ?

Dans la présentation de départ, la solution complète mélangeait caméras, traces Wi-Fi, modélisation Markov et interface web locale 

​. Cette version garde la logique globale, mais réduit la difficulté technique pour rester faisable et démontrable sur deux PC classiques.

Le choix de garder les caméras est cohérent avec la présentation, puisque la vision était déjà proposée comme moyen de détecter les personnes, d'analyser leurs déplacements et de prévoir les prochains flux 
​. En revanche, la partie Wi-Fi a été retirée dans cette implémentation parce qu'elle demande une infrastructure réseau plus lourde, des données réelles d'accès Wi-Fi et un cadre de test beaucoup plus complexe 
​.

Structure du projet
Le projet est organisé dans un seul dossier principal :

bash
AeroFlow_Projet/
├── main.py
├── config.py
├── requirements.txt
├── README.md
├── TROUBLESHOOTING.md
├── data/
└── src/
    ├── acquisition/
    │   ├── camera_stream.py
    │   └── network_comm.py
    ├── processing/
    │   └── tracker.py
    ├── prediction/
    │   └── model.py
    └── visualization/
        └── dashboard.py
L'idée de cette structure est de séparer proprement les responsabilités :

acquisition pour tout ce qui concerne les caméras et la communication réseau ;

processing pour la détection de personnes ;

prediction pour la logique de prévision ;

visualization pour l'affichage ;

main.py pour lancer et orchestrer le tout.


Technologies utilisées
Python
Le projet est codé en Python parce que c'est le langage le plus pratique ici pour combiner vision par ordinateur, traitement de données, réseau simple et visualisation. Il permet aussi d'écrire un code assez lisible, ce qui est utile pour un projet de cours.

OpenCV
OpenCV sert à récupérer le flux vidéo des webcams et à afficher les images annotées. C'est la base technique pour manipuler les frames de la caméra en direct. Sans OpenCV, il faudrait une solution plus lourde ou moins standard.

On l'utilise ici pour :

ouvrir la webcam ;

lire les images en continu ;

dessiner les boîtes de détection ;

afficher la vidéo dans une fenêtre locale.

Ultralytics / YOLO
Pour la détection de personnes, le projet utilise YOLO via la librairie ultralytics. Dans la présentation d'origine, YOLO faisait déjà partie des technologies envisagées pour la détection de personnes par caméra 
​. C'est donc logique de l'utiliser ici.

Pourquoi YOLO :

c'est un modèle connu et très documenté ;

il est rapide pour du temps réel ;

il détecte bien les personnes ;

il est facile à intégrer dans un projet Python.

Dans le code, YOLO ne sert qu'à une chose : repérer les objets de classe person dans chaque image et compter combien il y en a.

NumPy
NumPy sert à manipuler les tableaux numériques. Il est utilisé indirectement avec OpenCV et aussi pour les calculs du modèle prédictif. Par exemple, la régression linéaire simple du module de prédiction repose sur des opérations numériques très classiques que NumPy rend propres et rapides.

Matplotlib
Matplotlib est utilisé pour afficher un graphique simple côté PC A. Ce choix est volontairement sobre. Le but n'est pas de faire une grosse interface web, mais d'avoir quelque chose de clair pour voir l'historique du flux et la prédiction à court terme.

Socket TCP
Pour connecter les deux PC, le projet utilise les sockets TCP de Python. C'est probablement la solution la plus simple et la plus propre dans ce contexte.

Pourquoi ce choix :

pas besoin d'installer un serveur externe ;

facile à comprendre ;

fiable pour envoyer de petites données ;

suffisant puisque le PC B envoie seulement un entier et pas un flux vidéo.

Concrètement :

le PC A lance un petit serveur ;

le PC B ouvre une connexion vers lui ;

le PC B envoie son comptage ;

le PC A reçoit ce nombre et l'intègre au total.

Deque et logique d'historique
Pour la prédiction, le système garde seulement les dernières mesures utiles. On ne cherche pas à stocker des milliers de lignes. On garde une petite fenêtre glissante, ce qui est plus simple et plus adapté à une prédiction sur 30 secondes.

Ce qu'il faut installer avant de lancer le projet
Avant de lancer le projet, il faut avoir :

Python installé ;

pip disponible ;

deux PC connectés au même réseau local si on veut faire tourner le mode maître / esclave ;

une webcam sur chaque PC ;

les droits pour autoriser l'accès à la caméra.

Version de Python conseillée
Le plus simple est d'utiliser une version stable de Python, par exemple Python 3.11 ou Python 3.12. C'est préférable à une version trop récente, car certaines bibliothèques comme OpenCV ou d'autres dépendances peuvent avoir des problèmes de compatibilité.

Si possible, éviter Python 3.14 pour ce projet. L'erreur rencontrée sur NumPy et OpenCV montre bien que certaines versions très récentes peuvent poser problème avec des bibliothèques compilées.

Création de l'environnement virtuel
L'environnement virtuel est très important. Il évite d'installer les dépendances n'importe où sur la machine, et il permet de garder un projet propre.

Sous Windows
Dans le terminal, place-toi dans le dossier du projet puis lance :

bash
python -m venv venv
Ensuite, pour activer l'environnement virtuel :

bash
venv\Scripts\activate
Si tout se passe bien, tu verras (venv) au début de la ligne du terminal.

Sous Linux ou Mac
bash
python3 -m venv venv
source venv/bin/activate
Installation des dépendances
Une fois le venv activé, installe les dépendances avec :

bash
pip install -r requirements.txt
Si jamais tu rencontres encore un problème avec NumPy et OpenCV, tu peux forcer une version compatible :

bash
pip uninstall numpy opencv-python
pip install "numpy<2.0.0"
pip install opencv-python
Le fichier requirements.txt a été préparé pour limiter ce genre de souci.

Vérifier que tout est bien installé
Tu peux faire quelques vérifications simples :

bash
python -c "import cv2; print(cv2.__version__)"
python -c "import numpy; print(numpy.__version__)"
python -c "from ultralytics import YOLO; print('YOLO OK')"
Si ces commandes passent sans erreur, c'est déjà bon signe.

Comment lancer le projet
Le projet fonctionne avec deux modes :

master pour le PC A ;

slave pour le PC B.

Étape 1 : trouver l'IP du PC A
Sur le PC A, il faut récupérer l'adresse IP locale.

Sous Windows :

bash
ipconfig
Il faut repérer l'adresse IPv4 du PC connecté au réseau local. Par exemple : 192.168.1.100.

Étape 2 : configurer l'IP
Tu peux soit modifier config.py, soit directement passer l'IP en argument au moment du lancement du PC B.

Étape 3 : lancer le PC A
Depuis le dossier du projet, avec le venv activé :

bash
python main.py --mode master --camera 0
Ici, --camera 0 signifie qu'on utilise la webcam principale détectée par OpenCV.

Étape 4 : lancer le PC B
Sur le deuxième PC, toujours depuis le dossier du projet :

bash
python main.py --mode slave --camera 0 --master-ip 192.168.1.100
Il faut remplacer l'adresse IP par celle du PC A.

Comment vérifier que la connexion entre les deux PC fonctionne
Si tout est bien configuré :

le PC A démarre sa caméra et son serveur réseau ;

le PC B démarre sa caméra puis envoie périodiquement son comptage ;

le PC A reçoit les données du PC B et met à jour le total.

Si les deux PC sont sur le même réseau local et que le pare-feu ne bloque pas la connexion, ça doit fonctionner directement.

En cas de problème, vérifier :

que les deux PC sont bien sur le même réseau ;

que l'IP du PC A est correcte ;

que le port choisi dans config.py n'est pas bloqué ;

que le pare-feu Windows n'empêche pas Python de communiquer.

Comment fonctionne la détection de personnes
Le principe est simple. À chaque frame de la webcam :

on récupère l'image ;

on la passe au modèle YOLO ;

YOLO renvoie des boîtes englobantes et des classes détectées ;

on filtre uniquement la classe person ;

on garde les détections dont la confiance est suffisante ;

on compte le nombre de personnes détectées.

Le résultat est donc un entier par image ou par période d'échantillonnage.

Dans le projet de départ, la partie caméra avait déjà pour rôle d'analyser et reconnaître les entités, suivre les déplacements et préparer une prédiction de flux 
​. Ici, on garde surtout la première étape : détecter et compter les personnes de manière propre et démontrable.

Pourquoi on n'envoie pas la vidéo entre les PC
C'est un choix très important. On pourrait imaginer que le PC B envoie directement son flux vidéo au PC A, mais ce serait beaucoup plus lourd.

Envoyer seulement le nombre de personnes détectées a plusieurs avantages :

beaucoup moins de bande passante ;

système plus simple ;

moins de latence ;

architecture plus propre ;

plus cohérent avec une logique de respect des données.

C'est aussi plus proche d'une idée de capteur intelligent : chaque poste traite localement sa caméra, puis partage seulement une information utile.

Comment fonctionne la prédiction
Idée générale
La prédiction ici est volontairement simple. Le but n'était pas de construire un énorme modèle de deep learning pour une démo courte, mais d'avoir quelque chose de cohérent, explicable et suffisant pour anticiper le flux à très court terme.

Le PC A garde un historique récent du nombre total de personnes observées. À intervalles réguliers, il ajoute une nouvelle mesure à cet historique. Ensuite, il regarde l'évolution des derniers points pour estimer ce qui va se passer dans 30 secondes.

Données utilisées
Les données utilisées par le modèle prédictif ne viennent pas d'un dataset téléchargé ni d'un apprentissage supervisé classique. Elles viennent directement du système lui-même en temps réel.

Autrement dit, le modèle prend comme entrée une série temporelle très courte du type :

text
[8, 9, 9, 10, 11, 11, 12]
Chaque valeur représente le total observé à un instant donné.

Modèle choisi
Le modèle principal du projet est une régression linéaire simple sur l'historique récent. C'est une méthode basique mais pertinente pour une prédiction à horizon très court.

L'idée est la suivante :

on prend les derniers points de l'historique ;

on calcule la tendance moyenne ;

on prolonge cette tendance vers l'avant ;

on lit la valeur estimée à 30 secondes.

Ce n'est donc pas un modèle entraîné sur des milliers d'exemples comme un réseau de neurones. C'est un modèle d'extrapolation locale.

Pourquoi ce choix est cohérent
Dans la présentation initiale, l'objectif de la prédiction était d'anticiper les flux futurs à court terme 
​. Pour une version mini avec seulement deux webcams et un horizon de 30 secondes, une approche simple est plus logique qu'un gros modèle.

Ce choix a plusieurs avantages :

très facile à expliquer ;

rapide à calculer ;

ne demande pas de base d'entraînement annotée ;

bien adapté aux petites variations récentes ;

robuste pour une démonstration.

Comment le modèle a été entraîné
Dans cette version, il faut être honnête : il n'y a pas eu un entraînement au sens classique du machine learning supervisé.

Le mot "entraînement" dans la présentation d'origine faisait référence à une idée plus large où l'on aurait un historique important de flux, potentiellement issu des capteurs, des caméras et éventuellement d'autres sources, pour apprendre à mieux prédire 
​. Dans notre version, ce n'est pas ce qui se passe.

Concrètement ici :

YOLO est déjà un modèle pré-entraîné ;

le module de prédiction, lui, n'est pas ré-entraîné ;

il calcule simplement une tendance à partir des dernières mesures enregistrées.

Donc si on veut être précis dans le README et dans une soutenance :

le modèle de détection est pré-entraîné ;

le modèle de prédiction n'est pas entraîné sur un dataset externe ;

il est basé sur une régression linéaire appliquée en direct aux données récentes.

Différence entre YOLO et le modèle prédictif
C'est important de bien distinguer les deux :

YOLO est un vrai modèle d'intelligence artificielle déjà entraîné sur de grandes bases d'images. Il sert à reconnaître les personnes dans la vidéo.

La prédiction de flux, elle, repose ici sur un calcul statistique simple appliqué à l'historique des comptages.

Cette distinction est utile parce que beaucoup de projets mélangent tout en disant juste "on fait de l'IA". Ici, on peut expliquer proprement ce qui relève vraiment d'un modèle entraîné et ce qui relève d'une logique prédictive simple.

Peut-on améliorer plus tard la prédiction
Oui, clairement. Cette version pose une base propre. Plus tard, on pourrait remplacer la régression linéaire par :

une moyenne mobile pondérée ;

un modèle ARIMA ;

une régression plus avancée ;

un LSTM ou un autre modèle de série temporelle.

Mais pour un projet étudiant démontrable en temps réel avec deux PC, la version actuelle est plus adaptée. Elle reste compréhensible, rapide et cohérente avec l'objectif.

Rôle de chaque fichier
main.py
C'est le point d'entrée. Il lit les arguments, crée les objets nécessaires et lance soit le mode maître, soit le mode esclave.

config.py
Ce fichier centralise les paramètres du projet : IP du maître, port réseau, taille de l'historique, fréquence d'échantillonnage, taille d'image, seuil de confiance de YOLO, etc.

C'est pratique parce qu'on évite de modifier des valeurs partout dans le code.

src/acquisition/camera_stream.py
Ce module gère la webcam : ouverture, lecture des frames, arrêt propre.

src/acquisition/network_comm.py
Ce module gère la communication réseau entre les deux PC.

côté maître : un petit serveur écoute ;

côté esclave : un client envoie le comptage.

src/processing/tracker.py
Ce fichier contient la logique de détection de personnes avec YOLO. C'est lui qui renvoie le nombre de personnes et les boîtes de détection.

src/prediction/model.py
Ce module stocke l'historique et calcule la prédiction. C'est lui qui applique la régression linéaire simple.

src/visualization/dashboard.py
Ce fichier gère l'affichage du graphique et les annotations ajoutées à l'image.

Mode simulation
Si YOLO n'est pas installé ou ne se charge pas correctement, le code peut passer en mode simulation. Dans ce cas, le comptage n'est plus réel : il est simulé aléatoirement.

Ce mode peut servir pour vérifier rapidement que l'architecture générale fonctionne, mais il ne faut évidemment pas le présenter comme une vraie détection.

Limites du projet
Comme tout prototype, ce projet a des limites.

Il compte les personnes visibles, mais ne fait pas de suivi d'identité d'une frame à l'autre.

Il ne fusionne pas plusieurs sources comme dans l'idée complète caméra + Wi-Fi évoquée dans la présentation 
​.

La prédiction est volontairement simple.

Les résultats dépendent fortement de la qualité de la caméra, de la lumière et de l'angle de vue, ce qui était déjà cité comme contrainte dans la présentation 
​.

La calibration des caméras reste importante, surtout si on veut des mesures plus fiables, ce qui avait aussi été noté dans le support initial 
​.

Conseils pratiques pour les tests
Pour tester le projet proprement :

placer les deux PC sur le même réseau Wi-Fi ;

vérifier l'IP du PC A avant le lancement ;

lancer d'abord le maître, puis l'esclave ;

s'assurer que chaque webcam pointe vers une zone différente ;

éviter un contre-jour trop fort ;

faire quelques essais avec une seule personne puis plusieurs.

Comme les deux PC sont espacés d'environ 3 mètres, il faut aussi éviter d'avoir exactement le même champ de vision si le but est de mesurer deux zones différentes. Sinon, on risque de compter plusieurs fois la même personne.

Ce qu'on peut dire à l'oral pour expliquer le projet
Une façon simple de présenter le projet serait de dire quelque chose comme ça :

AeroFlow est une version simplifiée d'un système de suivi de flux inspiré d'un contexte aéroportuaire. Deux PC avec webcam détectent localement les personnes présentes dans leur champ. Le deuxième PC envoie uniquement son comptage au premier via le réseau local. Le PC principal agrège les mesures, garde un historique court et applique une régression linéaire simple pour estimer le flux dans 30 secondes. L'intérêt du projet est surtout d'avoir une architecture modulaire, légère et compréhensible, qui reproduit à petite échelle la logique acquisition, comptage, prédiction et visualisation du projet global.

Commandes utiles
Créer le venv
bash
python -m venv venv
Activer le venv sous Windows
bash
venv\Scripts\activate
Installer les dépendances
bash
pip install -r requirements.txt
Lancer le maître
bash
python main.py --mode master --camera 0
Lancer l'esclave
bash
python main.py --mode slave --camera 0 --master-ip 192.168.1.100
Désactiver le venv
bash
deactivate
Dernière remarque importante
Le projet actuel est volontairement simple, et c'est justement ce qui fait sa force. Il est plus crédible de présenter un système petit mais bien compris, bien structuré et qui fonctionne, plutôt qu'un gros projet trop ambitieux mais flou.

Dans la version initiale, l'idée globale visait l'optimisation des flux aéroportuaires à partir de plusieurs sources de données 
​. Cette implémentation garde cet esprit, mais sous une forme réaliste, démontrable et adaptée à un cadre étudiant.