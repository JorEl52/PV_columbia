import os
import requests
from resources.config import version_file, releases_url, github_token
import sys
import zipfile
import shutil
from kivy.config import Config

def get_current_version():
    with open(version_file, 'r') as f:
        return f.read().strip()

def get_latest_version():
    headers = {'Authorization': f'token{github_token}'} if github_token else {}
    response = requests.get(releases_url, headers=headers)
    if response.status_code == 200:
        releases = response.json()
        if releases:
            latest_releases = releases[0]
            return latest_releases['tag_name'].strip('v')
    return None

def check_for_updates():
    current_version = get_current_version()
    latest_version = get_latest_version()

    if latest_version and latest_version > current_version:
        return latest_version
    return None

def download_update(download_url, target_path):
    try:
        response = requests.get(download_url, stream=True)
        if response.status_code == 200:
            with open(target_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=1024):
                    file.write(chunk)
            return True
    except requests.exceptions.RequestException as e:
        print(f"Error downloading update: {e}")
    return False

def install_update(update_path):
    try:
        #extraer archivo zip de la actualizacion
        with zipfile.ZipFile(update_path, 'r') as zip_ref:
            zip_ref.extractall(os.path.dirname(update_path))
        #Obtener la ruta de la carpeta de la aplicacion
        app_path = os.path.dirname(os.path.abspath(sys.argv[0]))
        #Copiar los archivos actualizados a la carpeta de la aplicacion
        update_folder = os.path.join(os.path.dirname(update_path),'update')

        for root, dirs, files in os.walk(update_folder):
            for file in files:
                src_path = os.path.join(root, file)
                dst_path = os.path.join(app_path, os.path.relpath(src_path, update_folder))
                os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                shutil.copy2(src_path,dst_path)
        #Eliminar la carpeta de la actualizacion
        shutil.rmtree(update_folder)
        #Reiniciar la aplicacion
        Config.set('kivy', 'exit_on_escape','0')
        os.execl(sys.executable, sys.executable, *sys.argv)
    except Exception as e:
        print(f"Error al instalar la actualizacion: {e}")

def update_application():
    latest_version = check_for_updates()
    if latest_version:
        print(f"Hay una nueva versión disponible: {latest_version}")
        download_url = f'{releases_url}/download/v{latest_version}/update.zip'
        update_path = os.path.join(os.path.dirname(__file__), 'update.zip')
        if download_update(download_url, update_path):
            install_update(update_path)
    else:
        print("No hay actualizaciones disponibles")