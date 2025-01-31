from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from update import check_for_updates, download_update, install_update, releases_url
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.core.text import LabelBase
import os
import logging
import sys
from kivy.resources import resource_add_path

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

        #Verificar si hay versiones nuevas disponibles
        self.check_for_updates()

    def check_for_updates(self):
        logger.info('Verificando actualizaciones')
        latest_version = check_for_updates()
        if latest_version:
            logger.info(f'Nueva versión encontrada: {latest_version}')
            self.show_update_popup(latest_version)
    
    def show_update_popup(self, latest_version):
        logger.info('Mostrando popup de actualización')
        popup = Popup(title='Nueva Versión Disponible', content=Label(text=f'¡Hay una nueva versión disponible! (v{latest_version})'), size_hint=(0.6,0.3))

        update_button = Button(text='Actualizar', on_release=lambda x: self.update_application())
        popup.content.add_widget(update_button)
        popup.open()
    
    def update_application(self, *args):
        logger.info('Iniciando proceso de actualización')
        #Descargar actualizacion
        update_path = os.path.join(os.path.dirname(__file__), 'update.zip')
        if download_update(releases_url,update_path):
            logger.info('Actualización descargada correctamente')
            #instalar actualizacion
            install_update(update_path)
            logger.info('Actualización instalada')


class main(App):
    def build(self):
        logger.info('Construyendo la aplicación principal')
        return MainWindow()
    
    
if __name__ == "__main__":
    main().run()
    
    