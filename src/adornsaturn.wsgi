import sys
import os

# Caminho da pasta onde está index.py
app_folder = "/home/grow-control/apps_wsgi/adornsaturn"
if app_folder not in sys.path:
    sys.path.insert(0, app_folder)

# Adicionar paths do virtualenv (SE estiver usando)
venv_path = "/home/grow-control/apps_wsgi/grow/venv"
if venv_path not in sys.path:
    sys.path.insert(0, venv_path)

# Importar a aplicação Flask
from index import app as application
