from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from update import check_for_updates, download_update, install_update, releases_url
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.core.text import LabelBase
import os,shutil, requests, subprocess
import logging
import sys, threading
from kivy.resources import resource_add_path
from kivy.uix.progressbar import ProgressBar

from databases.sqlqueries import QueriesSQLite
from signin.signin import SigninWindow
from admin.admin import AdminWindow
from ventas.ventas import WindowVentas

# Agregar el directorio de fuentes al path de recursos
if hasattr(sys, '_MEIPASS'):
    resource_add_path(os.path.join(sys._MEIPASS, 'fonts'))

#Configuracion del logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger('Columbia School')
current_dir = os.path.dirname(os.path.abspath(__file__))
version_file = os.path.join(current_dir, 'resources', 'version.txt')
class MainWindow(BoxLayout):
    QueriesSQLite.create_tables()
    def __init__(self, **kwargs):
        super().__init__(*kwargs)
        self.admin_widget = AdminWindow()
        self.ventas_widget = WindowVentas(self.admin_widget.actualizar_productos)
        self.signin_widget = SigninWindow(self.ventas_widget.poner_usuario)
        self.ids.screen_signin.add_widget(self.signin_widget)
        self.ids.screen_ventas.add_widget(self.ventas_widget)
        self.ids.screen_admin.add_widget(self.admin_widget)
        Clock.schedule_once(lambda dt: self.check_for_updates(),2)

        #Verificar si hay versiones nuevas disponibles
        #self.check_for_updates()

    def check_for_updates(self):
        logger.info('Verificando actualizaciones')
        latest_version = check_for_updates()#obtener version mas reciente en git
        installed_version = self.get_installed_version()#obtener version instalada

        if latest_version and latest_version==installed_version:
            logger.info('La aplicación está actualizada.')
            return
        if latest_version:
            logger.info(f'Nueva versión encontrada: {latest_version}')
            self.show_update_popup(latest_version)
    
    def get_installed_version(self):
        if os.path.exists(version_file):
            with open(version_file, 'r') as f:
                return f.read().strip()
        return None #si no hay archivo, significa que no hay version registrada
    
    def save_installed_version(self, version):
        with open(version_file, 'w') as f:
            f.write(version)

    def show_update_popup(self, latest_version):
        logger.info('Mostrando popup de actualización')
        # Crear layout para el contenido
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        #Anadir mensaje principal
        message = Label(
            text=f'¡Hay una nueva versión disponible! (v{latest_version})',
            size_hint_y = 0.6
        )
        content.add_widget(message)
        #Crear layout horizontal para botones
        buttons_layout = BoxLayout(
            orientation='horizontal',
            spacing=10,
            size_hint_y=0.4
        )
        #Crear botones
        update_button = Button(
            text='Actualizar',
            size_hint_x=0.5
        )
        cancel_button = Button(
            text='Cancelar',
            size_hint_x=0.5
        )
        #Anadir botones al layout
        buttons_layout.add_widget(update_button)
        buttons_layout.add_widget(cancel_button)
        content.add_widget(buttons_layout)
        #Crear popup
        self.update_popup = Popup(
            title='Nueva Versión Disponible',
            content=content,
            size_hint=(0.8,0.4),
            auto_dismiss=False
        )
        #Vincular acciones a los botones
        #update_button.bind(on_release=lambda x: self.download_and_install_update(latest_version))
        update_button.bind(on_release=lambda x: self.start_update_thread(latest_version))
        cancel_button.bind(on_release=self.update_popup.dismiss)
        #Mostrar popup
        self.update_popup.open()

    def start_update_thread(self, version):
        self.update_popup.dismiss()
        threading.Thread(target=self.download_and_install_update, args=(version,), daemon=True).start()

    def download_and_install_update(self, version):
        try:
            #Crear directorio temporal
            tem_dir = os.path.join(os.path.dirname(__file__), 'temp')
            os.makedirs(tem_dir, exist_ok=True)
            releases_url = "https://github.com/JorEl52/PV_columbia/releases/download"
            #Descargar actualizacion
            download_url = f"{releases_url}/v{version}/PV_columbia-{version}.zip"
            update_file = os.path.join(tem_dir, f'PV_columbia-{version}.zip')

            #Crear respaldo rapido
            Clock.schedule_once(lambda dt: self.show_progress_popup("Iniciando actualización..."))#Barra de progreso

            backup_dir = os.path.join(os.path.dirname(__file__), 'backup')
            os.makedirs(backup_dir, exist_ok=True)
            backup_path = os.path.join(backup_dir, f'backup_{version}')
            
            def exclude_files(dir, files):
                exclusions = {'temp', 'backup', '__pycache__', '.git', '.venv', '.dmg', 'dist', 'build', '.spec'}
                return [f for f in files if f in exclusions]

            logger.info('Creando respaldo...')
            Clock.schedule_once(lambda dt: self.increment_progress(10, "Creando respaldo..."))
            shutil.copytree(os.path.dirname(__file__), backup_path, ignore=exclude_files)
            shutil.make_archive(backup_path, 'zip', backup_path)
            shutil.rmtree(backup_path)#Elimina la copia temporal despues de comprimir

            Clock.schedule_once(lambda dt: self.increment_progress(30, "Respaldo creado. Descargando actualización..."))#Barra de progreso actualizada

            logger.info('Descargando actualización....')
            response = requests.get(download_url, stream=True)
            if response.status_code == 200:
                total_size = int(response.headers.get('content-length', 0))
                download = 0
                with open(update_file, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                        download += len(chunk)
                        progress = 30 + int((download/total_size)*40)
                        Clock.schedule_once(lambda dt, p=progress: self.increment_progress(p, "Descargando actualización..."))
                logger.info('Descarga completa.')
            else:
                logger.error(f"Error al descargar: {response.status_code}")
                Clock.schedule_once(lambda dt: self.show_error_popup("No se pudo descargar la actualización."))
                return

            Clock.schedule_once(lambda dt: self.increment_progress(75, "Instalando actualización..."))#Barra de progreso actualizada
            #extraer archivos
            extract_path = os.path.join(tem_dir, "extracted")
            os.makedirs(extract_path, exist_ok=True)
            shutil.unpack_archive(update_file, extract_path,'zip')
            #Copiar y reemplazar archivos
            self.copy_and_remplace_with_progress(extract_path, os.path.dirname(__file__))
            #Limpiar archivos temporales
            shutil.rmtree(tem_dir)
            self.save_installed_version(version)
            Clock.schedule_once(lambda dt: self.increment_progress(100, "Actualización completada. Reiniciando aplicación..."))#Barra de progreso actualizada
            #Programar reinicio
            Clock.schedule_once(self.close_popup, 2)
            Clock.schedule_once(self.restart_application, 3)
        except Exception as e:
            logger.error(f"Error en la actualización: {str(e)}")
            error_message = str(e)
            Clock.schedule_once(lambda dt: self.show_error_popup(error_message))

    def copy_and_remplace_with_progress(self, src_dir, dest_dir):
        file_to_copy = []
        for root, dirs, files in os.walk(src_dir):
            for file in files:
                file_to_copy.append(os.path.join(root, file))
        total_files = len(file_to_copy)
        if total_files == 0:
            return
        for i, src_file in enumerate(file_to_copy):
            relative_path = os.path.relpath(src_file, src_dir)
            dest_file = os.path.join(dest_dir, relative_path)
            dest_folder = os.path.dirname(dest_file)

            if not os.path.exists(dest_folder):
                os.makedirs(dest_folder)
            
            shutil.copy2(src_file, dest_file)
            progress = 75 + int((i/total_files)*25)
            Clock.schedule_once(lambda dt, p=progress: self.increment_progress(p, "Instalando actualización..."))

    def show_error_popup(self, error_message):
        content = BoxLayout(orientation='vertical')
        content.add_widget(Label(text=f'Error en la actualización:\n{error_message}'))
        popup = Popup(
            title='Error',
            content=content,
            size_hint=(0.6, 0.3)
        )
        popup.open()

    def restart_application(self, dt):
        python = sys.executable
        os.execl(python, python, *sys.argv)
        
    def show_progress_popup(self, message):
        self.progress_popup = Popup(
            title='Actualización en progreso',
            size_hint=(0.6, 0.3),
            auto_dismiss=False
        )

        layout = BoxLayout(orientation='vertical')
        self.progress_label  = Label(text=message)
        self.progress_bar = ProgressBar(max=100, value=0)

        layout.add_widget(self.progress_label)
        layout.add_widget(self.progress_bar)
        self.progress_popup.content = layout
        self.progress_popup.open()

    def increment_progress(self, value, message):
        if hasattr(self, 'progress_bar'):
            self.progress_bar.value = value
            self.progress_label.text = message

    def close_popup(self, dt):
        if self.progress_popup:
            self.progress_popup.dismiss()
    

class main(App):
    def build(self):
        logger.info('Construyendo la aplicación principal')
        return MainWindow()
    
    
if __name__ == "__main__":
    main().run()
    
    