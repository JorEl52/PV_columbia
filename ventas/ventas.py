from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.properties import BooleanProperty
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.uix.popup import Popup
from datetime import datetime, timedelta
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.core.text import LabelBase
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os, sys
from databases.sqlqueries import QueriesSQLite

#obtener ruta del archivo
current_dir = os.path.dirname(os.path.abspath(__file__))
kv_file_path = os.path.join(current_dir,'..', 'ventas', 'ventas.kv')

Builder.load_file(kv_file_path)

#ruta a la fuente
fuente_path = os.path.join(current_dir,'..','fonts', 'birthstone-bounce-medium.ttf')
LabelBase.register(name='birthstone', fn_regular=fuente_path)
pdfmetrics.registerFont(TTFont('birthstone-bounce-medium',fuente_path))
#ruta base de datos
db_path = os.path.join(current_dir,'..','databases','uniformes.sqlite')
connection = QueriesSQLite.create_connection(db_path)

class SelectableRecycleBoxLayout(FocusBehavior, LayoutSelectionBehavior,RecycleBoxLayout):
    ''' Adds selection and focus behavior to the view. '''
    touch_deselect_last = BooleanProperty(True)


class SelectableBoxLayout(RecycleDataViewBehavior, BoxLayout):
    ''' Add selection support to the Label '''
    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)

    def refresh_view_attrs(self, rv, index, data):
        self.index = index
        self.ids['_hashtag'].text = str(1+index)
        self.ids['_articulo'].text = data['nombre'].capitalize()
        self.ids['_talla'].text = str(data['talla'])
        self.ids['_cantidad'].text = str(data['cantidad_carrito'])
        self.ids['_precio_por_articulo'].text = str("{:.2f}".format(data['precio']))
        self.ids['_precio'].text = str("{:.2f}".format(data['precio_total']))
        return super(SelectableBoxLayout, self).refresh_view_attrs(
            rv, index, data)

    def on_touch_down(self, touch):
        ''' Add selection on touch down '''
        if super(SelectableBoxLayout, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            return self.parent.select_with_touch(self.index, touch)

    def apply_selection(self, rv, index, is_selected):
        ''' Respond to the selection of items in the view. '''
        self.selected = is_selected
        if is_selected:
            rv.data[index]['seleccionado'] = True
        else:
            rv.data[index]['seleccionado'] = False

class SelectableBoxLayoutPopup(RecycleDataViewBehavior, BoxLayout):
    ''' Add selection support to the Label '''
    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)

    def refresh_view_attrs(self, rv, index, data):
        self.index = index
        self.ids['_codigo'].text = data['codigo']
        self.ids['_articulo'].text = data['nombre'].capitalize()
        self.ids['_talla'].text = data['talla']
        self.ids['_cantidad'].text = str(data['cantidad'])
        self.ids['_precio'].text = str("{:.2f}".format(data['precio']))
        return super(SelectableBoxLayoutPopup, self).refresh_view_attrs(
            rv, index, data)

    def on_touch_down(self, touch):
        ''' Add selection on touch down '''
        if super(SelectableBoxLayoutPopup, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            return self.parent.select_with_touch(self.index, touch)

    def apply_selection(self, rv, index, is_selected):
        ''' Respond to the selection of items in the view. '''
        self.selected = is_selected
        if is_selected:
            rv.data[index]['seleccionado'] = True
        else:
            rv.data[index]['seleccionado'] = False

class RV(RecycleView):
    def __init__(self, **kwargs):
        super(RV, self).__init__(**kwargs)
        self.data = []
        self.modificar_producto = None

    def agregar_articulo(self, articulo):
        articulo['seleccionado'] = False
        indice = -1
        if self.data:
            for i in range(len(self.data)):
                if articulo['codigo']==self.data[i]['codigo']:
                    indice = i
            if indice >= 0:
                self.data[indice]['cantidad_carrito'] += 1
                self.data[indice]['precio_total'] = self.data[indice]['precio']*self.data[indice]['cantidad_carrito']
                self.refresh_from_data()
            else:
                self.data.append(articulo)
        else:
            self.data.append(articulo)

    def eliminar_articulo(self):
        indice = self.articulo_seleccionado()
        precio = 0
        if indice >= 0:
            self._layout_manager.deselect_node(self._layout_manager._last_selected_node)
            precio = self.data[indice]['precio_total']
            self.data.pop(indice)
            self.refresh_from_data()
        return precio

    def modificar_articulo(self):
        indice = self.articulo_seleccionado()
        if indice >= 0:
            popup = cambiarCantidadPopup(self.data[indice],self.actualizar_articulo)
            popup.open()

    def actualizar_articulo(self, valor):
        indice = self.articulo_seleccionado()
        if indice >= 0:
            if valor == 0:
                self.data.pop(indice)
                self._layout_manager.deselect_node(self._layout_manager._last_selected_node)
            else:
                self.data[indice]['cantidad_carrito'] = valor
                self.data[indice]['precio_total'] = self.data[indice]['precio']*valor
            self.refresh_from_data()
            nuevo_total = 0
            for data in self.data:
                nuevo_total += data['precio_total']
            self.modificar_producto(False, nuevo_total)

    def articulo_seleccionado(self):
        indice = -1
        for i in range(len(self.data)):
            if self.data[i]['seleccionado']:
                indice = i
                break
        return indice
    
class cambiarCantidadPopup(Popup):
    def __init__(self, data, actualizar_articulo_callback, **kwargs):
        super(cambiarCantidadPopup, self).__init__(**kwargs)
        self.data = data
        self.actualizar_articulo = actualizar_articulo_callback
        self.ids.info_nueva_cant_1.text = "Producto: " + self.data['nombre'].capitalize()
        self.ids.info_nueva_cant_2.text = "Cantidad: " + str(self.data['cantidad_carrito'])

    def validar_input(self, texto_input):
        try:
            nueva_cantidad = int(texto_input)
            self.ids.notificacion_no_valido.text = ''
            self.actualizar_articulo(nueva_cantidad)
            self.dismiss()
        except:
            self.ids.notificacion_no_valido.text = 'Cantidad no válida'
        
class productoPorNombrePOPUP(Popup):
    def __init__(self, input_nombre, agregar_producto_callback, **kwargs):
        super(productoPorNombrePOPUP, self).__init__(**kwargs)
        self.input_nombre = input_nombre
        self.agregar_producto = agregar_producto_callback

    def mostrar_articulos(self):
        
        inventario_sql = QueriesSQLite.execute_read_query(connection, "SELECT * from uniformes")

        self.open()
        for nombre in inventario_sql:
            if nombre[1].lower().find(self.input_nombre) >= 0:
                producto = {'codigo': nombre[0], 'nombre': nombre[1], 'talla': nombre[2], 'precio': nombre[3], 'cantidad': nombre[4]}
                self.ids.rvs.agregar_articulo(producto)

    def seleccionar_articulo(self):
        indice = self.ids.rvs.articulo_seleccionado()
        if indice >= 0:
            _articulo = self.ids.rvs.data[indice]
            articulo = {}
            articulo['codigo'] = _articulo['codigo']
            articulo['nombre'] = _articulo['nombre']
            articulo['talla'] = _articulo['talla']
            articulo['precio'] = _articulo['precio']
            articulo['cantidad_carrito'] = 1
            articulo['cantidad_inventario'] = _articulo['cantidad']
            articulo['precio_total'] = _articulo['precio']
            if callable(self.agregar_producto):
                self.agregar_producto(articulo)
            self.dismiss()

class PagarPopup(Popup):
    def __init__(self, total, pagado_callaback, **kwargs):
        super(PagarPopup, self).__init__(**kwargs)
        self.total = total
        self.pagado = pagado_callaback
        self.ids.total.text = "$ {:.2f}".format(self.total)
        self.ids.boton_pagar.bind(on_release = self.dismiss)
    
    def mostrar_cambio(self):
        recibido = self.ids.recibido.text
        try:
            cambio = float(recibido) - float(self.total)
            if cambio >= 0:
                self.ids.cambio.text = "$ {:.2f}".format(cambio)
                self.ids.boton_pagar.disabled = False
            else:
                self.ids.cambio.text = "Pago menor a cantidad a pagar"
        except:
            self.ids.cambio.text = "Pago no válido"
    
        '''
        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        En esta función puedo agregar que me imprima un ticket o que abra la caja para el dinero
        ////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        '''
    def terminar_pago(self):
        self.pagado()
        self.dismiss()

class NuevaCompraPopup(Popup):
    def __init__(self,nueva_compra_callback, **kwargs):
        super(NuevaCompraPopup, self).__init__(**kwargs)
        self.nueva_compra = nueva_compra_callback
        self.ids.aceptar.bind(on_release = self.dismiss)

class WindowVentas(BoxLayout):
    usuario = None
    def __init__(self, actualizar_productos_callback, **kwargs):
        super().__init__(*kwargs)
        self.total = 0.0
        self.ids.rvs.modificar_producto = self.modificar_producto
        self.actualizar_productos = actualizar_productos_callback
        # Presentar hora
        self.ahora = datetime.now()
        self.ids.fecha.text = self.ahora.strftime("%d/%m/%y")
        Clock.schedule_interval(self.actualizar_hora, 1)

    
    def actualizar_hora(self, *args):
        self.ahora = self.ahora + timedelta(seconds = 1)
        self.ids.hora.text = self.ahora.strftime("%H:%M:%S")

    def admin(self):
        self.parent.parent.current = 'screen_admin'
    
    def signout(self):
        if self.ids.rvs.data:
            self.ids.notificacion_falla.text = 'Compra abierta'
        else:
            self.parent.parent.current = 'screen_signin'

    def eliminar_producto(self):#Eliminar producto de la lista
        menos_precio = self.ids.rvs.eliminar_articulo()
        self.total -= menos_precio
        self.ids.sub_total.text = '$ ' + "{:.2f}".format(self.total)

    def modificar_producto(self, cambio=True, nuevo_total = None):#Modificar la cantidad de productos
        if cambio:
            self.ids.rvs.modificar_articulo()
        else:
            self.total = nuevo_total
            self.ids.sub_total.text = '$ ' + "{:.2f}".format(self.total)

    def agregar_producto_codigo(self, codigo):#Agregar producto por codigo
        inventario_sql = QueriesSQLite.execute_read_query(connection, "SELECT * from uniformes")

        for producto in inventario_sql:
            if codigo==producto[0]:
                articulo={}
                articulo['codigo'] = producto[0]
                articulo['nombre'] = producto[1]
                articulo['talla'] = producto[2]
                articulo['precio'] = producto[3]
                articulo['cantidad_carrito'] = 1
                articulo['cantidad_inventario'] = producto[4]
                articulo['precio_total'] = producto[3]
                self.agregar_producto(articulo)
                self.ids.buscar_codigo.text = ''
                break
            
    def agregar_producto_nombre(self, nombre):#Agregar roducto por nombre
        self.ids.buscar_nombre.text = ''
        pop_up = productoPorNombrePOPUP(nombre, self.agregar_producto)
        pop_up.mostrar_articulos()

    def agregar_producto(self,articulo):#Agregar producto a la lista
        self.total += articulo['precio']
        self.ids.sub_total.text = '$ ' + "{:.2f}".format(self.total)
        self.ids.total.text = "$ {:.2f}".format(self.total)
        self.ids.rvs.agregar_articulo(articulo)
    
    def pagar(self):
        if self.ids.rvs.data:
            popup = PagarPopup(self.total, self.pagado)
            popup.open()
        else:
            self.ids.notificacion_falla.text = 'No hay nada que pagar'
    
    def actualizar_total_vendidos(self, connection, producto, cantidad):
        #verificamos si el producto ya existe
        existencia = """SELECT id, total FROM total_vendidos WHERE producto = ? AND talla =?"""
        resultado = QueriesSQLite.execute_read_query(connection, existencia,(producto['codigo'],producto['talla']))

        if resultado:#Si existe, actualizamos el total
            actualizar = """UPDATE total_vendidos SET total = total + ? WHERE producto = ? AND talla = ?"""
            QueriesSQLite.execute_query(connection,actualizar, (cantidad,producto['codigo'],producto['talla']))
        else:
            #encontramos el ultimo ID utilizado
            ultimo_id_query = """SELECT COALESCE(MAX(id),0) FROM total_vendidos"""
            ultimo_id = QueriesSQLite.execute_read_query(connection, ultimo_id_query,())[0][0]

            #Si no existe, creamos un nuevo registro
            insertar = """INSERT INTO total_vendidos (id,producto, talla, total) VALUES (?,?,?,?)"""
            QueriesSQLite.execute_query(connection,insertar,(ultimo_id + 1,producto['codigo'],producto['talla'],cantidad))
        #Reordenamos los IDs,creando una lista temporal de ID ordenado
        obtener_orden = """SELECT id,producto,talla FROM total_vendidos ORDER BY total DESC"""
        productos_ordenados = QueriesSQLite.execute_read_query(connection,obtener_orden,())

        #Actualizamos los ID uno por uno para evitar conflicto
        try:
            for i, (id_actual, prod, talla) in enumerate(productos_ordenados):
                QueriesSQLite.execute_query(connection,"UPDATE total_vendidos SET id=? WHERE producto=? AND talla=?",(-i-1,prod,talla))
            #Asignamos ID finales
            for i,(_,prod,talla) in enumerate(productos_ordenados):
                QueriesSQLite.execute_query(connection,"UPDATE total_vendidos SET id=? WHERE producto=? AND talla=?", (i+1, prod, talla))
        except Exception as e:
            print("Error en la ordenacion")
            connection.rollback()
            raise e

    def generar_ticket(self, numero_venta):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        ticket_path = os.path.join(current_dir,'..','tickets')
        #Asegurar que la carpeta tickets existe
        os.makedirs(ticket_path, exist_ok=True)

        #nombre del ticket
        fecha_actual = self.ahora.strftime("%Y-%m-%d")
        hora_actual = self.ahora.strftime("%H:%M:%S")
        pdf_filename = os.path.join(ticket_path,f'ticket_venta_{fecha_actual}_{numero_venta}.pdf')

        #Generar ticket
        c = canvas.Canvas(pdf_filename, pagesize=letter)
        logo_path = os.path.join(current_dir,'logo_columbia_ticket.png')
        c.drawImage(logo_path, 256, 680, width=100, height=100)#Posicion y tamaño del logo
        c.setFont("birthstone-bounce-medium", 20)
        c.drawString(230, 650, "Discovering Knowledge")
        c.setFont("Helvetica", 15)
        c.drawString(100, 630, f'Ticket de venta')
        c.drawString(100, 610, f'Fecha: {fecha_actual}, Hora: {hora_actual}')
        c.drawString(100,590, f'Vendedor: {self.usuario["nombre"]}')
        c.drawString(100,570, f'Número de venta: {numero_venta}')
        #Presentar los productos
        c.setFont("Helvetica", 12)
        y = 550
        c.drawString(100,y, 'Productos')
        c.drawString(200,y, 'Cant.')
        c.drawString(260,y,'Talla')
        c.drawString(300,y, '$/Artículo')
        c.drawString(380,y,'Total')
        y -= 20
        c.line(100, y + 10, 500, y + 10)
        y -= 10
        c.setFont("Helvetica", 10)
        for producto in self.ids.rvs.data:
            c.drawString(100, y, producto['nombre'].capitalize())  
            c.drawString(200,y,str(producto['cantidad_carrito']))
            c.drawString(260, y, producto['talla'])
            c.drawString(300,y,f"${producto['precio']:.2f}")
            total_precio = producto['cantidad_carrito']*producto['precio']
            c.drawString(380,y,f"${total_precio:.2f}")
            y -= 20
        c.setFont("Helvetica", 12)
        c.drawString(340, y-20, f'Total: ${self.total:.2f}')

        c.setFont("Helvetica", 8)
        y = 100
        c.drawString(230, y-15, f'Camino Molino de las Flores S/N')
        c.drawString(245, y - 30, f'Texcoco, Edo. de México')
        c.drawString(255, y - 45, f'Tel. (595) 95 424 95')
        c.save()

        return pdf_filename

    def enviar_email(self, numero_venta, pdf_filename):
        email_sender = 'uniformescolumbia@gmail.com'
        sender_password = 'vjao qrmv dlai ybdo'
        email_destino = 'jahef5181@gmail.com'
        smtp_server = 'smtp.gmail.com'
        smtp_port = 465

        #Enviar el archivo pdf por email
        msg = MIMEMultipart()
        msg['From'] = email_sender
        msg['To'] = email_destino
        fecha_actual = self.ahora.strftime("%d/%m/%Y")
        hora_actual = self.ahora.strftime("%H:%M:%S")
        msg['Subject'] = f'Ticket de venta #{numero_venta}-{fecha_actual}'

        body = f'''
        Estimado encargado,

        Adjunto encontrarás el ticket de venta #{numero_venta} generado el dia {fecha_actual} a las {hora_actual}
        Por favor, verifique que se haya realizado la venta correctamente.

        Columbia School
        '''
        msg.attach(MIMEText(body, 'plain'))
        #Adjuntar pdf del ticket
        with open(pdf_filename, 'rb') as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename= {os.path.basename(pdf_filename)}')
        msg.attach(part)

        try:
            #enviar correo
            with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
                server.login(email_sender, sender_password)
                server.send_message(msg)
            print("Emial enviado")
            return True
        except smtplib.SMTPAuthenticationError:
            print("Error de autenticacion. Verifica credenciales")
        except smtplib.SMTPConnectError:
            print("Error de conexion al servidor")
        except Exception as e:
            print("Error al enviar el correo")

    def pagado(self):
        # self.ids.notificacion_exito.text = 'Compra realizada con éxito'
        # self.ids.notificacion_falla.text = ''
        # self.ids.total.text = "$ {:.2f}".format(self.total)
        
        '''Actualización de la base de datos cuando se haga una compra'''
        actualizar = """
        UPDATE 
            uniformes
        SET
            cantidad=?
        WHERE
            codigo=?
        """
        #guardamos la venta realizada en sql
        venta = """
        INSERT INTO ventas (total, fecha, username) VALUES (?,?,?)
        """
        venta_tuple = (self.total, self.ahora, self.usuario['username'])
        venta_id = QueriesSQLite.execute_query(connection, venta, venta_tuple)
        ventas_detalle = """INSERT INTO ventas_detalle(id_venta, precio, producto, talla, cantidad) VALUES (?,?,?,?,?)"""

        #Generar ticket
        pdf_file = self.generar_ticket(venta_id)
        #enviar correo
        self.enviar_email(venta_id, pdf_file)

        actualizar_admin = []
        for producto in self.ids.rvs.data: 
            nueva_cantidad = 0
            if producto['cantidad_inventario'] - producto['cantidad_carrito'] > 0:
                nueva_cantidad = producto['cantidad_inventario'] - producto['cantidad_carrito']
            producto_tuple = (nueva_cantidad, producto['codigo'])
            ventas_detalle_tuple = (venta_id, producto['precio'], producto['codigo'], producto['talla'], producto['cantidad_carrito'])
            actualizar_admin.append({'codigo': producto['codigo'], 'cantidad': nueva_cantidad})

            QueriesSQLite.execute_query(connection, actualizar, producto_tuple)
            QueriesSQLite.execute_query(connection, ventas_detalle, ventas_detalle_tuple)

            #Actualizamos la tabla de total_vendidos
            self.actualizar_total_vendidos(connection, producto,producto['cantidad_carrito'])
        self.actualizar_productos(actualizar_admin)
        self.ids.rvs.data = []
        self.total = 0.0
        self.ids.sub_total.text = '0.00'
        self.ids.total.text = '0.00'
        self.ids.notificacion_exito.text = ''
        self.ids.notificacion_falla.text = ''
        self.ids.buscar_codigo.disabled = False
        self.ids.buscar_nombre.disabled = False
        self.ids.rvs.refresh_from_data()

    def nueva_compra(self, desde_popup=False):
        if desde_popup:
            self.ids.rvs.data = []
            self.total = 0.0
            self.ids.sub_total.text = '0.00'
            self.ids.total.text = '0.00'
            self.ids.notificacion_exito.text = ''
            self.ids.notificacion_falla.text = ''
            self.ids.buscar_codigo.disabled = False
            self.ids.buscar_nombre.disabled = False
            self.ids.pagar.disabled = False #Quitar si se limpia la ventana
            self.ids.rvs.refresh_from_data()
        elif len(self.ids.rvs.data):
            popup = NuevaCompraPopup(self.nueva_compra)
            popup.open()

    def poner_usuario(self, usuario):
        self.ids.bienvenido_label.text = 'Bienvenido ' + usuario['nombre']
        self.usuario = usuario
        if usuario['tipo'] == 'trabajador':
            self.ids.admin_boton.disabled = True
            self.ids.admin_boton.text = ''
            self.ids.admin_boton.opacity = 0
        else:
            self.ids.admin_boton.disabled = False
            self.ids.admin_boton.text = 'Admin'
            self.ids.admin_boton.opacity = 1
            

class ventas(App):
    def build(self):
        return WindowVentas()
    
if __name__ == '__main__':
    ventas().run()