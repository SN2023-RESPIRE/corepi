# corepi

## Setup

1. Clonez ce dépôt
2. Créez un environnement virtuel Python (venv) (optionnel)
3. Installez les packages depuis `requirements.txt`
4. Créez un fichier .env
5. Créez une entrée `DATABASE_WEBSITE_URI` dans le fichier .env avec l'URI correcte pour l'envoi des données
6. Modifiez main.py si nécessaire pour utiliser le bon port série ainsi que la bonne base de données SQLite
7. Lancez

### Notes supplémentaires

- Ce programme a été conçu pour tourner sur une Raspberry Pi, il vous faut donc activer l'UART. Voici les étapes pour l'activer :
  - Modifiez le fichier `/boot/config.txt` et rajoutez la ligne `dtoverlay=pi3-disable-bt`
  - Modifiez le fichier `/boot/cmdline.txt` et enlevez `console=serial10,115200`
  - Redémarrez l'appareil
