from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.lang import Builder
from kivy.core.text import LabelBase
import os
from databases.sqlqueries import QueriesSQLite


#obtener ruta del archivo
current_dir = os.path.dirname(os.path.abspath(__file__))
kv_file_path = os.path.join(current_dir,'..', 'signin', 'signin.kv')

Builder.load_file(kv_file_path)
#ruta de las fuentes
playwrite_font_path = os.path.join(current_dir,'..', 'fonts', 'playwrite-ca-light.ttf')
birthstone_font_path = os.path.join(current_dir,'..', 'fonts', 'birthstone-bounce-medium.ttf')
LabelBase.register(name='playwrite_light', fn_regular=playwrite_font_path)
LabelBase.register(name='birthstone', fn_regular=birthstone_font_path)
#ruta base de datos
db_path = os.path.join(current_dir,'..','databases','uniformes.sqlite')
#conexion con base de datos
connection = QueriesSQLite.create_connection(db_path)
users = QueriesSQLite.execute_read_query(connection, "SELECT * from usuarios")


crear_usuario = """
        INSERT INTO usuarios (username, nombre, password, tipo)
        VALUES (?, ?, ?, ?);
        """

class SigninWindow(BoxLayout):
    def __init__(self, poner_usuario_callback, **kwargs):
        super().__init__(*kwargs)
        self.poner_usuario = poner_usuario_callback
        self.checar_tabla_usuarios()

    def checar_tabla_usuarios(self):
        if not users:
            self.ids.signin_notificacion.text = 'No hay usuarios agregados. Agregue un usuario ADMINISTRADOR'
            self.ids.add_admin_button.opacity =1
            self.ids.add_admin_button.disabled = False
        else:
            self.ids.add_admin_button.opacity = 0
            self.ids.add_admin_button.disabled = True
    
    def agregar_admin(self):
        self.ids.add_admin_button.opacity = 0
        self.ids.add_admin_button.disabled = True
        usuario = {
            'username': 'admin',
            'nombre':'Administrador',
            'passwoord':'admin',
            'tipo':'admin'
        }

        QueriesSQLite.execute_query(connection, crear_usuario, tuple(usuario.values()))
        self.ids.signin_notificacion.text = 'Usuario Administrador agregado con exito'

    def verificar_usuario(self, username, password):

        if username == '' or password == '':
            self.ids.signin_notificacion.text = 'Falta nombre de usuario y/o contraseña'
        else:
            usuario = {}
            if users:
                for user in users:
                    if user[0] == username:
                        usuario['nombre'] = user[1]
                        usuario['username'] = user[0]
                        usuario['password'] = user[2]
                        usuario['tipo'] = user[3]
                        break
            if usuario:
                if usuario['password'] == password:
                    self.ids.username.text = ''
                    self.ids.password.text = ''
                    self.ids.signin_notificacion.text = ''
                    if usuario['tipo'] == 'trabajador':
                        self.parent.parent.current = 'screen_ventas'
                    else:
                        self.parent.parent.current = 'screen_admin'
                    self.poner_usuario(usuario)
                else:
                    self.ids.signin_notificacion.text = 'Usuario o contraseña incorrecta'
            else:
                self.ids.signin_notificacion.text = 'Usuario o contraseña incorrecta'

class signin(App):
    def build(self):
        return SigninWindow()
    
if __name__ == "__main__":
    signin().run()
    