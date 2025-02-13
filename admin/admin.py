from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.properties import BooleanProperty
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.uix.dropdown import DropDown
from kivy.clock import Clock
from kivy.uix.popup import Popup
from kivy.core.text import LabelBase
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.label import Label
from kivy.uix.image import Image as KivyImage
from datetime import datetime, timedelta
import csv
from pathlib import Path
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from databases.sqlqueries import QueriesSQLite

#obtener ruta del archivo
current_dir = os.path.dirname(os.path.abspath(__file__))
kv_file_path = os.path.join(current_dir,'..', 'admin', 'admin.kv')
Builder.load_file(kv_file_path)

#ruta a la fuente
fuente_path = os.path.join(current_dir,'..','fonts', 'birthstone-bounce-medium.ttf')
LabelBase.register(name='birthstone', fn_regular=fuente_path)
pdfmetrics.registerFont(TTFont('birthstone-bounce-medium',fuente_path))
#ruta base de datos
db_path = os.path.join(current_dir,'..','databases','uniformes.sqlite')
#Ruta inventario
inventario_path = os.path.join(current_dir,'..','inventario')

connection = QueriesSQLite.create_connection(db_path)
borrar = """DELETE FROM uniformes WHERE codigo = ?"""
actualizar_producto = """
UPDATE 
    uniformes
SET
    nombre=?, talla=?, precio=?, cantidad=?
WHERE 
    codigo=?;
"""
crear_producto = """
INSERT INTO uniformes (codigo, nombre, talla, precio, cantidad)
VALUES (?, ?, ?, ?, ?);
"""
borrar_usuario = """DELETE FROM usuarios WHERE username = ?"""
actualizar_usuarios = """
UPDATE 
    usuarios
SET
    nombre=?, password=?, tipo=?
WHERE 
    username=?;
"""
crear_usuario = """
INSERT INTO usuarios (username, nombre, password, tipo)
VALUES (?, ?, ?, ?);
"""

class SelectableRecycleBoxLayout(FocusBehavior, LayoutSelectionBehavior,RecycleBoxLayout):
    ''' Adds selection and focus behavior to the view. '''
    touch_deselect_last = BooleanProperty(True)

class SelectableProductoLabel(RecycleDataViewBehavior, BoxLayout):
    ''' Add selection support to the Label '''
    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)

    def refresh_view_attrs(self, rv, index, data):
        self.index = index
        self.ids['_hashtag'].text = str(1+index)
        self.ids['_codigo'].text = data['codigo']
        self.ids['_articulo'].text = data['nombre'].capitalize()
        self.ids['_talla'].text = data['talla']
        self.ids['_cantidad'].text = str(data['cantidad'])
        self.ids['_precio'].text = str("$ {:.2f}".format(data['precio']))
        return super(SelectableProductoLabel, self).refresh_view_attrs(
            rv, index, data)

    def on_touch_down(self, touch):
        ''' Add selection on touch down '''
        if super(SelectableProductoLabel, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            rv = self.parent.parent
            rv.deselect_all()
            return self.parent.select_with_touch(self.index, touch)

    def apply_selection(self, rv, index, is_selected):
        ''' Respond to the selection of items in the view. '''
        self.selected = is_selected
        if is_selected:
            rv.data[index]['seleccionado'] = True
        else:
            rv.data[index]['seleccionado'] = False

class SelectableUsuarioLabel(RecycleDataViewBehavior, BoxLayout):
    ''' Add selection support to the Label '''
    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)

    def refresh_view_attrs(self, rv, index, data):
        self.index = index
        self.ids['_hashtag'].text = str(1+index)
        self.ids['_nombre'].text = data['nombre'].title()
        self.ids['_username'].text = data['username']
        self.ids['_tipo'].text = str(data['tipo'])
        return super(SelectableUsuarioLabel, self).refresh_view_attrs(
            rv, index, data)

    def on_touch_down(self, touch):
        ''' Add selection on touch down '''
        if super(SelectableUsuarioLabel, self).on_touch_down(touch):
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

class SelectableEstadisticasLabel(RecycleDataViewBehavior, BoxLayout):
    ''' Add selection support to the Label '''
    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)

    def refresh_view_attrs(self, rv, index, data):
        self.index = index
        self.ids['_hashtag'].text = str(1+index)
        self.ids['_codigo'].text = data['codigo']
        self.ids['_articulo'].text = data['nombre'].capitalize() if data['nombre'] else "Producto descontinuado"
        self.ids['_talla'].text = data['talla']
        self.ids['_total_vendidos'].text = data['total']
        return super(SelectableEstadisticasLabel, self).refresh_view_attrs(
            rv, index, data)

    def on_touch_down(self, touch):
        ''' Add selection on touch down '''
        if super(SelectableEstadisticasLabel, self).on_touch_down(touch):
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

class ItemVentaLabel(RecycleDataViewBehavior, BoxLayout):
    index = None

    def refresh_view_attrs(self, rv, index, data):
        self.index = index
        self.ids['_hashtag'].text = str(1+index)
        self.ids['_codigo'].text = data['codigo']
        self.ids['_articulo'].text = data['producto'].capitalize()
        self.ids['_talla'].text = str(data['talla'])
        self.ids['_cantidad'].text = str(data['cantidad'])
        self.ids['_precio_por_articulo'].text = str("$ {:.2f}".format(data['precio']))+" /artículo"
        self.ids['_total'].text = str("$ {:.2f}".format(data['total']))
        return super(ItemVentaLabel, self).refresh_view_attrs(
            rv, index, data)
    
class SelectableVentaLabel(RecycleDataViewBehavior, BoxLayout):
    ''' Add selection support to the Label '''
    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)

    def refresh_view_attrs(self, rv, index, data):
        self.index = index
        self.ids['_hashtag'].text = str(1+index)
        self.ids['_username'].text = data['username']
        self.ids['_cantidad'].text = str(data['productos'])
        self.ids['_total'].text = str("$ {:.2f}".format(data['total']))
        self.ids['_time'].text = str(data['fecha'].strftime("%H:%M:%S"))
        self.ids['_date'].text = str(data['fecha'].strftime("%d:%m:%Y"))
        return super(SelectableVentaLabel, self).refresh_view_attrs(
            rv, index, data)

    def on_touch_down(self, touch):
        ''' Add selection on touch down '''
        if super(SelectableVentaLabel, self).on_touch_down(touch):
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

class SelectableInventarioAntiguoLabel(RecycleDataViewBehavior, BoxLayout):
    ''' Add selection support to the Label '''
    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)

    def refresh_view_attrs(self, rv, index, data):
        self.index = index
        self.ids['_prenda'].text = data['prenda']
        self.ids['_2'].text = str(data['2'])
        self.ids['_3'].text = str(data['3'])
        self.ids['_4'].text = str(data['4'])
        self.ids['_6'].text = str(data['6'])
        self.ids['_8'].text = str(data['8'])
        self.ids['_10'].text = str(data['10'])
        self.ids['_12'].text = str(data['12'])
        self.ids['_14'].text = str(data['14'])
        self.ids['_16'].text = str(data['16'])
        self.ids['_18/28'].text = str(data['18_28'])
        self.ids['_20'].text = str(data['20'])
        self.ids['_22'].text = str(data['22'])
        self.ids['_24'].text = str(data['24'])
        self.ids['_30'].text = str(data['30'])
        self.ids['_32'].text = str(data['32'])
        self.ids['_34'].text = str(data['34'])
        self.ids['_36'].text = str(data['36'])
        self.ids['_38'].text = str(data['38'])
        self.ids['_40'].text = str(data['40'])
        self.ids['_CH/42'].text = str(data['CH_42'])
        self.ids['_MD/44'].text = str(data['MD_44'])
        self.ids['_GD/46'].text = str(data['GD_46'])
        self.ids['_XGD'].text = str(data['XGD'])
        self.ids['_Total'].text = str(data['total'])
        return super(SelectableInventarioAntiguoLabel, self).refresh_view_attrs(
            rv, index, data)

    def on_touch_down(self, touch):
        ''' Add selection on touch down '''
        if super(SelectableInventarioAntiguoLabel, self).on_touch_down(touch):
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

class AdminRV(RecycleView):
    def __init__(self, **kwargs):
        super(AdminRV, self).__init__(**kwargs)
        self.data = []

    def agregar_datos(self, datos):
        for dato in datos:
            dato['seleccionado'] = False
            self.data.append(dato)
        self.refresh_from_data()
    
    def dato_seleccionado(self):
        indice = -1
        for i in range(len(self.data)):
            if self.data[i]['seleccionado']:
                indice = i
                break
        return indice
    def deselect_all(self):
        for i in self.data:
            i['seleccionado'] = False
        self.refresh_from_data()

class ProductoPopup(Popup):
    def __init__(self, agregar_callback, **kwargs):
        super(ProductoPopup, self).__init__(**kwargs)
        self.agregar_callback = agregar_callback

    def abrir(self, agregar, producto = None):
        if agregar:
            self.ids.producto_info_1.text = 'Agregar producto nuevo'
            self.ids.producto_codigo.disabled = False
        else:
            self.ids.producto_info_1.text = 'Modificar Producto'
            self.ids.producto_codigo.text = producto['codigo']
            self.ids.producto_codigo.disabled = True
            self.ids.producto_nombre.text = producto['nombre']
            self.ids.producto_talla.text = producto['talla']
            self.ids.producto_cantidad.text = str(producto['cantidad'])
            self.ids.producto_precio.text = str(producto['precio'])
        self.open()
    
    def verificar(self, producto_codigo, producto_nombre, producto_talla, producto_cantidad, producto_precio):
        alert1 = 'Falta: '
        alert2 = ''
        validado = {}
        #Validar que se ingresó un codigo 
        if not producto_codigo:
            alert1 += 'Código. '
            validado['codigo'] = False
        else:
            validado['codigo'] = producto_codigo
        #Validar que se ingresó el nombre
        if not producto_nombre:
            alert1 += 'Nombre. '
            validado['nombre'] = False
        else:
            validado['nombre'] = producto_nombre.lower()
        #Validar que se ingresó la talla
        if not producto_talla:
            alert1 += 'Talla. '
            validado['talla'] = False
        else:
            validado['talla'] = producto_talla.upper()
        #Validar que se ingresó la cantidad
        if not producto_cantidad:
            alert1 += 'Cantidad. '
            validado['cantidad'] = False
        else:
            try:
                numeric = int(producto_cantidad)
                validado['cantidad'] = producto_cantidad
            except:
                alert2 += 'Cantidad no válida. '
                validado['cantidad'] = False
        #Validar que se ingresó el precio
        if not producto_precio:
            alert1 += 'Precio. '
            validado['precio'] = False
        else:
            try:
                numeric = float(producto_precio)
                validado['precio'] = producto_precio
            except:
                alert2 += 'Precio no válido. '
                validado['precio'] = False
        
        valores = list(validado.values())
        if False in valores:
            self.ids.no_valid_notif.text = alert1 + alert2
        else:
            self.ids.no_valid_notif.text = 'Validado'
            validado['cantidad'] = int(validado['cantidad'])
            validado['precio'] = float(validado['precio'])
            self.agregar_callback(True, validado)
            self.dismiss()

class VistaProductos(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(self.cargar_productos, 1)

    def cargar_productos(self, *args):
        _productos = []
        inventario_sql = QueriesSQLite.execute_read_query(connection, "SELECT * from uniformes")
        if inventario_sql:
            for producto in inventario_sql:
                _productos.append({'codigo':producto[0], 'nombre':producto[1], 'talla':producto[2], 'cantidad':producto[4], 'precio': producto[3]})
        self.ids.rv_productos.agregar_datos(_productos)

    def agregar_producto(self, agregar = False, validado=None):
        if agregar:
            producto_tuple = (
                validado['codigo'],
                validado['nombre'],
                validado['talla'],
                float(validado['precio']),
                int(validado['cantidad'])
            )
            QueriesSQLite.execute_query(connection, crear_producto, producto_tuple)
            self.ids.rv_productos.data.append(validado)
            self.ids.rv_productos.refresh_from_data()
        else:
            popup = ProductoPopup(self.agregar_producto)
            popup.abrir(True)

    def modificar_producto(self, modificar=False, validado=None):
        indice = self.ids.rv_productos.dato_seleccionado()
        if modificar:
            producto_tuple = (
                validado['nombre'],
                validado['talla'],
                float(validado['precio']),
                int(validado['cantidad']),
                validado['codigo']
            )
            QueriesSQLite.execute_query(connection, actualizar_producto, producto_tuple)
            self.ids.rv_productos.data[indice]['nombre'] = validado['nombre']
            self.ids.rv_productos.data[indice]['talla'] = validado['talla']
            self.ids.rv_productos.data[indice]['precio'] = validado['precio']
            self.ids.rv_productos.data[indice]['cantidad'] = validado['cantidad']
            self.ids.rv_productos.refresh_from_data()
        else:
            if indice >= 0:
                producto = self.ids.rv_productos.data[indice].copy()
                popup = ProductoPopup(self.modificar_producto)
                popup.abrir(False, producto)
                self.ids.rv_productos.deselect_all()

    def eliminar_producto(self):
        indice = self.ids.rv_productos.dato_seleccionado()
        if indice >= 0:
            producto_tuple = (
                self.ids.rv_productos.data[indice]['codigo'],
                )
            QueriesSQLite.execute_query(connection, borrar, producto_tuple)
            self.ids.rv_productos.data.pop(indice)
            self.ids.rv_productos.refresh_from_data()

    def actualizar_productos(self, productos_actualizados):
        for producto_nuevo in productos_actualizados:
            for producto_viejo in self.ids.rv_productos.data:
                if producto_nuevo['codigo'] == producto_viejo['codigo']:
                    producto_viejo['cantidad'] = producto_nuevo['cantidad']
                    break
        self.ids.rv_productos.refresh_from_data()

    def generar_file_inventario(self):
        #Asegurar que la carpeta inventario existe
        os.makedirs(inventario_path, exist_ok=True)
        #Configurar nombre del archivo
        fecha_actual = datetime.now().strftime("%d-%m-%Y")
        filename = os.path.join(inventario_path,f"Inventario_{fecha_actual}.pdf")

        #Crear documento pdf
        doc = SimpleDocTemplate(filename, pagesize=letter, topMargin=30,bottomMargin=30)
        elements = []

        logo_path = os.path.join(current_dir,'..','assets','logo_columbia_inventario.png')
        if os.path.exists(logo_path):
            logo = Image(logo_path)
            logo.drawHeight = 100
            logo.drawWidth = 100
            elements.append(logo)
        elements.append(Spacer(1,10))

        #Configurar estilo
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('CustomTitle',parent=styles['Heading1'],fontSize=20,textColor=colors.darkblue,spaceAfter=10,alignment=TA_CENTER)

        lema_style = ParagraphStyle('lema', fontSize=20, textColor=colors.black, alignment=TA_CENTER, fontName='birthstone-bounce-medium', spaceAfter=30)
        #Lema
        lema = Paragraph("Discovering Knowledge", lema_style)
        elements.append(lema)
        #Titulo
        title = Paragraph("Reporte de Inventario", title_style)
        elements.append(title)
        elements.append(Spacer(1,20))
        #Configurar tabla
        headers = ['Código', 'Nombre', 'Talla', 'Cantidad', 'Precio']
        data = [headers]

        for producto in self.ids.rv_productos.data:
            row = [
                producto['codigo'],
                producto['nombre'],
                producto['talla'],
                str(producto['cantidad']),
                f"${producto['precio']:.2f}"
            ]
            data.append(row)
        #Crear tabla
        tabla_inventario = Table(data)
        tabla_inventario.setStyle(TableStyle([
            #Estilo encabezado
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0),(-1,0),'CENTER'),
            ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
            ('FONTSIZE',(0,0),(-1,0),12),
            #Estilo contenido
            ('BACKGROUND', (0,1),(-1,-1), colors.beige),
            ('TEXTCOLOR',(0,1),(-1,-1),colors.black),
            ('FONTNAME',(0,0),(-1,-1), 'Helvetica'),
            ('FONTSIZE',(0,0),(-1,-1), 10),
            ('GRID',(0,0),(-1,-1),1,colors.black),
            ('ALIGN',(0,0),(-1,-1),'CENTER'),
            ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ]))

        elements.append(tabla_inventario)
        doc.build(elements)
        return filename

    def generar_file_estadisticas(self):
        #Asegurar que la carpeta inventario existe
        os.makedirs(inventario_path, exist_ok=True)
        #Configurar nombre del archivo
        fecha_actual = datetime.now().strftime("%d-%m-%Y")
        estadisticas_filename = os.path.join(inventario_path,f"Estadisticas_venta_{fecha_actual}.pdf")

        #Crear documento pdf
        doc = SimpleDocTemplate(estadisticas_filename, pagesize=letter, topMargin=30,bottomMargin=30)
        elements = []
        logo_path = os.path.join(current_dir,'..','assets','logo_columbia_inventario.png')
        if os.path.exists(logo_path):
            logo = Image(logo_path)
            logo.drawHeight = 100
            logo.drawWidth = 100
            elements.append(logo)
        elements.append(Spacer(1,10))

        #Configurar estilo
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('CustomTitle',parent=styles['Heading1'],fontSize=20,textColor=colors.darkblue,spaceAfter=10,alignment=TA_CENTER)

        lema_style = ParagraphStyle('lema', fontSize=20, textColor=colors.black, alignment=TA_CENTER, fontName='birthstone-bounce-medium', spaceAfter=30)
        #Lema
        lema = Paragraph("Discovering Knowledge", lema_style)
        elements.append(lema)
        #Titulo
        title = Paragraph("Estadísticas de venta", title_style)
        elements.append(title)
        elements.append(Spacer(1,20))
        #Configurar tabla
        headers = ['Código', 'Nombre', 'Talla', 'Total vendido']
        data = [headers]

        connection = QueriesSQLite.create_connection(db_path)

        query_total_vendidos = """
        SELECT
            tv.id,
            tv.producto as codigo,
            u.nombre,
            tv.talla,
            tv.total
        FROM
            total_vendidos tv
        LEFT JOIN
            uniformes u ON tv.producto = u.codigo
        ORDER BY
            tv.total DESC
        """

        estadisticas_sql = QueriesSQLite.execute_read_query(connection,query_total_vendidos)
        if estadisticas_sql:
            for estadistica in estadisticas_sql:
                nombre = estadistica[2] if estadistica[2] else "Producto descontinuado"
                row = [
                    estadistica[1],#codigo
                    nombre,#nombre
                    estadistica[3],#talla
                    str(estadistica[4])#total vendido
                ]
                data.append(row)

        #Crear tabla
        tabla_estadisticas = Table(data)
        tabla_estadisticas.setStyle(TableStyle([
            #Estilo encabezado
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0),(-1,0),'CENTER'),
            ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
            ('FONTSIZE',(0,0),(-1,0),12),
            #Estilo contenido
            ('BACKGROUND', (0,1),(-1,-1), colors.beige),
            ('TEXTCOLOR',(0,1),(-1,-1),colors.black),
            ('FONTNAME',(0,0),(-1,-1), 'Helvetica'),
            ('FONTSIZE',(0,0),(-1,-1), 10),
            ('GRID',(0,0),(-1,-1),1,colors.black),
            ('ALIGN',(0,0),(-1,-1),'CENTER'),
            ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ]))

        elements.append(tabla_estadisticas)
        doc.build(elements)
        return estadisticas_filename

    def enviar_inventario(self):
        email_sender = 'uniformescolumbia@gmail.com'
        sender_password = 'vjao qrmv dlai ybdo'
        email_destino = 'brenda2ventauniformes@gmail.com'
        smtp_server = 'smtp.gmail.com'
        smtp_port = 465

        pdf_filename = self.generar_file_inventario()
        estadisticas_filename = self.generar_file_estadisticas()
        #Enviar el archivo pdf por email
        msg = MIMEMultipart()
        msg['From'] = email_sender
        msg['To'] = email_destino
        fecha_actual = datetime.now().strftime("%d-%m-%Y")
        msg['Subject'] = f'Inventario y Estadísticas al día {fecha_actual}'

        body = f'''
        Estimado encargado,

        Adjunto encontrará:
            1. El inventario existente actualizado
            2. Las estadísticas de ventas
        
        Ambos documentos estan actualizados al día {fecha_actual}
        
        Por favor, verifique que la información este correcta.

        Columbia School
        '''
        msg.attach(MIMEText(body, 'plain'))
        #Adjuntar pdf del ticket
        for filename in [pdf_filename, estadisticas_filename]:
            with open(filename, 'rb') as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename= {os.path.basename(filename)}')
            msg.attach(part)

        try:
            #enviar correo
            with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
                server.login(email_sender, sender_password)
                server.send_message(msg)
            
            #MEnsaje de exito
            popup = Popup(title='Éxito',content=Label(text='El reporte ha sido enviado exitosamente.'),size_hint=(None,None),size=(400,200))
            popup.open()
            return True
        except smtplib.SMTPAuthenticationError:
            
            popup = Popup(title='Error autenticación',content=Label(text='Error de autenticacion. Verifica credenciales'),size_hint=(None,None),size=(400,200))
            popup.open()
        except smtplib.SMTPConnectError:
            popup = Popup(title='Error de conexión',content=Label(text='Error de conexion al servidor'),size_hint=(None,None),size=(400,200))
            popup.open()
        except Exception as e:
            popup = Popup(title='Error',content=Label(text='Error al enviar el correo'),size_hint=(None,None),size=(400,200))
            popup.open()

class UsuarioPopup(Popup):
    def __init__(self, _agregar_callback, **kwargs):
        super(UsuarioPopup, self).__init__(**kwargs)
        self.agregar_usuario = _agregar_callback

    def abrir(self, agregar, usuario=None):
        if agregar:
            self.ids.usuario_info_1.text = 'Agregar usuario nuevo'
            self.ids.usuario_username.disabled = False
        else:
            self.ids.usuario_info_1.text = 'Modificar Usuario'
            self.ids.usuario_username.text = usuario['username']
            self.ids.usuario_username.disabled = True
            self.ids.usuario_nombre.text = usuario['nombre']
            self.ids.usuario_password.text = usuario['password']
            if usuario['tipo'] == 'admin':
                self.ids.admin_tipo.state = 'down'
            else:
                self.ids.trabajador_tipo.state = 'down'
        self.open()
    
    def verificar(self, usuario_username, usuario_nombre, usuario_password, admin_tipo, trabajador_tipo):
        alert1 = 'Falta: '
        alert2 = ''
        validado = {}
        #Validar que se ingresó un username
        if not usuario_username:
            alert1 += 'Username. '
            validado['username'] = False
        else:
            validado['username'] = usuario_username
        #Validar que se ingresó el nombre
        if not usuario_nombre:
            alert1 += 'Nombre. '
            validado['nombre'] = False
        else:
            validado['nombre'] = usuario_nombre.lower()
        #Validar que se ingresó el password
        if not usuario_password:
            alert1 += 'Password. '
            validado['password'] = False
        else:
            validado['password'] = usuario_password
        #Validar que se ingresó el tipo
        if admin_tipo == 'normal' and trabajador_tipo == 'normal':
            alert1 += 'Tipo. '
            validado['tipo'] = False
        else:
            if admin_tipo == 'down':
                validado['tipo'] = 'admin'
            else:
                validado['tipo'] = 'trabajador'        
        
        valores = list(validado.values())

        if False in valores:
            self.ids.no_valid_notif.text = alert1 + alert2
        else:
            self.ids.no_valid_notif.text = 'Validado'
            self.agregar_usuario(True, validado)
            self.dismiss()
    
class VistaUsuarios(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(self.cargar_usuarios, 1)

    def cargar_usuarios(self, *args):
        _usuarios = []
        usuarios_sql = QueriesSQLite.execute_read_query(connection, "SELECT * from usuarios")
        if usuarios_sql:
            for usuario in usuarios_sql:
                _usuarios.append({'nombre':usuario[1], 'username':usuario[0], 'password': usuario[2],'tipo':usuario[3]})
        self.ids.rv_usuarios.agregar_datos(_usuarios)

    def agregar_usuario(self, agregar=False, validado=None):
        if agregar:
            usuario_tuple = tuple(validado.values())
            QueriesSQLite.execute_query(connection, crear_usuario, usuario_tuple)
            self.ids.rv_usuarios.data.append(validado)
            self.ids.rv_usuarios.refresh_from_data()
        else:
            popup = UsuarioPopup(self.agregar_usuario)
            popup.abrir(True)

    def modificar_usuario(self, modificar=False, validado=None):
        indice = self.ids.rv_usuarios.dato_seleccionado()
        if modificar:
            usuario_tuple = (
                validado['nombre'],
                validado['password'],
                validado['tipo'],
                validado['username']
                )
            QueriesSQLite.execute_query(connection, actualizar_usuarios, usuario_tuple)
            self.ids.rv_usuarios.data[indice]['nombre'] = validado['nombre']
            self.ids.rv_usuarios.data[indice]['tipo'] = validado['tipo']
            self.ids.rv_usuarios.data[indice]['password'] = validado['password']
            self.ids.rv_usuarios.refresh_from_data()
        else:
            if indice >= 0:
                usuario = self.ids.rv_usuarios.data[indice]
                popup = UsuarioPopup(self.modificar_usuario)
                popup.abrir(False, usuario)

    def eliminar_usuario(self):
        indice = self.ids.rv_usuarios.dato_seleccionado()
        if indice >= 0:
            usuario_tuple = (
                self.ids.rv_usuarios.data[indice]['username'],
                )
            QueriesSQLite.execute_query(connection, borrar_usuario, usuario_tuple)
            self.ids.rv_usuarios.data.pop(indice)
            self.ids.rv_usuarios.refresh_from_data()

class InfoVentaPopup(Popup):
    connection = QueriesSQLite.create_connection(db_path)
    select_item_query = """SELECT nombre FROM uniformes WHERE codigo=?"""
    def __init__(self, venta, **kwargs):
        super(InfoVentaPopup, self).__init__(**kwargs)
        self.venta = [{"codigo":producto[3] ,"producto": QueriesSQLite.execute_read_query(self.connection, self.select_item_query, (producto[3],))[0][0], "talla":producto[4] ,"cantidad":producto[5] ,"precio": producto[2],"total":producto[5]*producto[2] } for producto in venta]

    def mostrar(self):
        self.open()
        total_items = 0
        total_dinero = 0.0
        for articulo in self.venta:
            total_items += articulo['cantidad']
            total_dinero += articulo['total']
        self.ids.total_items.text = str(total_items)
        self.ids.total_dinero.text = "$ "+ str("{:.2f}".format(total_dinero))
        self.ids.info_rv.agregar_datos(self.venta)

class GuardarArchivoPopup(Popup):
    def __init__(self,guardar_archivo_callback, **kwargs):
        super(GuardarArchivoPopup, self).__init__(**kwargs)
        self.guardar_archivo_callback = guardar_archivo_callback
        Clock.schedule_once(self.set_initial_path, 0)

    def set_initial_path(self, dt):
        documentos_path = os.path.expanduser('~/Documents')
        if hasattr(self.ids, 'filechooser'):
            self.ids.filechooser.path = documentos_path
        
    def mostrar(self):
        self.open()

    def guardar_archivo(self, selection):
        if selection:
            ruta = selection[0] if isinstance(selection, list) else selection

            self.guardar_archivo_callback(ruta)
            self.dismiss()

class VistaVentas(Screen):
    productos_actuales = []
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
    def crear_csv(self):
        connection = QueriesSQLite.create_connection(db_path)
        select_item_query = """SELECT nombre FROM uniformes WHERE codigo=?"""
        if self.ids.ventas_rv.data:
            def guardar_archivo(ruta_seleccionada):
                #Construir la ruta completa del archivo
                nombre_archivo = f"Ventas_{self.ids.date_id.text}.csv"
                ruta_completa = os.path.join(ruta_seleccionada, nombre_archivo)

                if os.path.exists(ruta_completa):
                    self.ids.notificacion.text = 'El archivo ya existe'
                    return
        
                productos_csv = []
                total = 0
                for venta in self.productos_actuales:
                    for item in venta:
                        item_found = next((producto for producto in productos_csv if producto['codigo'] == item[3]), None)
                        total += item[2]*item[5]
                        if item_found:
                            item_found['cantidad'] += item[5]
                            item_found['precio_total'] = item_found['precio']*item_found['cantidad']
                        else:
                            nombre = QueriesSQLite.execute_read_query(connection, select_item_query, (item[3],))[0][0]
                            productos_csv.append({'nombre': nombre,'codigo': item[3], 'talla': item[4], 'cantidad': item[5], 'precio': item[2], 'precio_total': item[2]*item[5]})
                try: 
                    with open(ruta_completa, 'w', encoding='UTF8', newline='') as f:
                        write = csv.writer(f, delimiter='\t')
                        #Escribir encabezado con fecha
                        write.writerow(['REPORTE DE VENTAS'])
                        write.writerow([f'Fecha: {self.ids.date_id.text}'])
                        write.writerow([])
                        #Escribir encabezado
                        headers = ['Nombre','', 'Codigo','', 'Talla','', 'Cantidad','', 'Precio Unitario','', 'Total']
                        write.writerow(headers)
                        #Escribir datos de productos
                        for producto in productos_csv:
                            write.writerow([
                                producto['nombre'],'',
                                producto['codigo'],'',
                                producto['talla'],'',
                                producto['cantidad'],'',
                                f"${producto['precio']:.2f}",'',
                                f"${producto['precio_total']:.2f}"
                            ])
                        #Escribir linea en blanco y total
                        write.writerow([])
                        write.writerow(['', '', '', '', 'TOTAL:', f"${total:.2f}"])

                    self.ids.notificacion.text = 'Archivo creado y guardado'
                except Exception as e:
                    self.ids.notificacion.text = f'Error al crear el archivo: {str(e)}'
            p = GuardarArchivoPopup(guardar_archivo_callback=guardar_archivo)
            p.mostrar()
        else:
            self.ids.notificacion.text = 'No hay datos que guardar'
        self.ids.ventas_rv.data = ''

    def mas_info(self):
        indice = self.ids.ventas_rv.dato_seleccionado()
        if indice >= 0:
            venta = self.productos_actuales[indice]
            p = InfoVentaPopup(venta)
            p.mostrar()

    def cargar_venta(self, choice='Default'):

        valid_input = True
        final_sum = 0
        f_inicio = datetime.strptime('01/01/00', '%d/%m/%y')
        f_fin = datetime.strptime('31/12/2099', '%d/%m/%Y')

        _ventas = []
        _total_productos = []

        select_ventas_query = """
        SELECT * FROM ventas WHERE fecha BETWEEN ? AND ?
        """
        select_productos_query = """
        SELECT * FROM ventas_detalle WHERE id_venta=?
        """
        self.ids.ventas_rv.data = []
        #codigo al ver las ventas
        if choice == 'Default':#Cuando se presiona ver la venta de hoy
            f_inicio = datetime.today().date()
            f_fin = f_inicio + timedelta(days=1)
            self.ids.date_id.text = str(f_inicio.strftime("%d-%m-%y"))
        elif choice == 'Date':#Cuando se da una fecha especifica
            date = self.ids.single_date.text
            try:
                f_elegida = datetime.strptime(date, '%d/%m/%y')
            except:
                valid_input = False
            if valid_input:
                f_inicio = f_elegida
                f_fin = f_elegida + timedelta(days=1)
                self.ids.date_id.text = f_elegida.strftime('%d-%m-%y')
        else:# Cuando se da un rango de fechas
            if self.ids.initial_date.text:
                initial_date = self.ids.initial_date.text
                try:
                    f_inicio = datetime.strptime(initial_date, '%d/%m/%y')
                except:
                    valid_input = False
            if self.ids.last_date.text:
                last_date = self.ids.last_date.text
                try:
                    f_fin = datetime.strptime(last_date, '%d/%m/%y')
                except:
                    valid_input = False
            if valid_input:
                self.ids.date_id.text = f_inicio.strftime("%d-%m-%y")+" - "+ f_fin.strftime("%d-%m-%y")

        if valid_input:
            inicio_fin = (f_inicio, f_fin)
            ventas_sql = QueriesSQLite.execute_read_query(connection, select_ventas_query, inicio_fin)
            if ventas_sql:
                for venta in ventas_sql:
                    final_sum += venta[1]
                    ventas_detalle_sql = QueriesSQLite.execute_read_query(connection, select_productos_query, (venta[0],))
                    _total_productos.append(ventas_detalle_sql)
                    count = 0
                    for producto in ventas_detalle_sql:
                        count += producto[5]
                    _ventas.append({"username": venta[3], "productos": count, "total": venta[1], "fecha": datetime.strptime(venta[2], '%Y-%m-%d %H:%M:%S.%f')})
                self.ids.ventas_rv.agregar_datos(_ventas)
                self.productos_actuales = _total_productos
        self.ids.final_sum.text = '$ ' + str("{:.2f}".format(final_sum))
        self.ids.initial_date.text = ''
        self.ids.last_date.text = ''
        self.ids.single_date.text = ''
        self.ids.notificacion.text = 'Datos de ventas'
        
class VistaEstadisticas(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(self.cargar_productos_vendidos, 1)
    def on_enter(self):
        self.cargar_productos_vendidos()
        
    def cargar_productos_vendidos(self, *args):
        _estadisticas = []

        query_total_vendidos = """
        SELECT
            tv.id,
            tv.producto as codigo,
            u.nombre,
            tv.talla,
            tv.total
        FROM
            total_vendidos tv
        LEFT JOIN
            uniformes u ON tv.producto = u.codigo
        ORDER BY
            tv.total DESC
        """
        estadisticas_sql = QueriesSQLite.execute_read_query(connection,query_total_vendidos)

        self.ids.estadisticas_rv.data = []

        if estadisticas_sql:
            for venta in estadisticas_sql:
                #Si el producto fue eliminado, usar Producto descontinuado
                nombre = venta[2] if venta[2] else "Producto descontinuado"
                _estadisticas.append({
                    'id': venta[0],
                    'codigo': venta[1],
                    'nombre': nombre,
                    'talla': venta[3],
                    'total': str(venta[4]),
                    'seleccionnado': False
                })
        self.ids.estadisticas_rv.agregar_datos(_estadisticas)
        self.ids.estadisticas_rv.refresh_from_data()

class VistaInventarioAntiguo(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(self.cargar_inventario, 1)

    def cargar_inventario(self, *args):
        _inventario = []
        final_sum =0
        inventario_antiguo_sql = QueriesSQLite.execute_read_query(connection, "SELECT * from primer_inventario")
        if inventario_antiguo_sql:
            for prenda in inventario_antiguo_sql:
                final_sum += prenda[24]
                _inventario.append({'prenda':prenda[0], '2':prenda[1],'3':prenda[2],'4':prenda[3],'6':prenda[4],'8':prenda[5],'10':prenda[6],'12':prenda[7],'14':prenda[8],'16':prenda[9],'18_28':prenda[10],'20':prenda[11],'22':prenda[12],'24':prenda[13],'30':prenda[14],'32':prenda[15],'34':prenda[16],'36':prenda[17],'38':prenda[18],'40':prenda[19],'CH_42':prenda[20],'MD_44':prenda[21],'GD_46':prenda[22],'XGD':prenda[23],'total':prenda[24]})
        self.ids.inventario_antiguo_rv.agregar_datos(_inventario)
        self.ids.total_inventario.text = str(final_sum)
        
class CustomDropDown(DropDown):
    def __init__(self, cambiar_callback, **kwargs):
        self._succ_cb = cambiar_callback
        super(CustomDropDown, self).__init__(**kwargs)
    
    def vista(self, vista):
        if callable(self._succ_cb):
            self._succ_cb(True, vista)
        
class AdminWindow(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.vista_actual = 'Productos'
        self.vista_manager = self.ids.vista_manager
        self.dropdown = CustomDropDown(self.cambiar_vista)
        self.ids.cambiar_vista.bind(on_release=self.dropdown.open)

        #imagen del logo en la interfaz
        logo_path = os.path.join(current_dir,'..','assets', 'logo_columbia.png')

        logo_image = KivyImage()
        logo_image.source = logo_path
        logo_image.allow_stretch = True
        logo_image.size_hint_y = 1
        
        self.ids.image_logo.add_widget(logo_image)

    def cambiar_vista(self, cambio=False, vista=None):
        if cambio:
            self.vista_actual = vista
            self.vista_manager.current = self.vista_actual
            self.dropdown.dismiss()
        
    def signout(self):
        self.parent.parent.current = 'screen_signin'
    
    def venta(self):
        self.parent.parent.current = 'screen_ventas'

    def actualizar_productos(self, productos):
        self.ids.vista_productos.actualizar_productos(productos)
    

class admin(App):
    def build(self):
        return AdminWindow()
    
if __name__ == "__main__":
    admin().run()
    