import sqlite3
from sqlite3 import Error
import os

db_path = os.path.join(os.path.dirname(__file__), "uniformes.sqlite")

class QueriesSQLite:
    def create_connection(path): #Crea una conexion con la base de datos y requiere de un path
        connection = None
        try:
            connection = sqlite3.connect(path)
            print("Connection to SQLite DB successful")
        except Error as e:
            print(f"The error '{e}' occurred")

        return connection

    def execute_query(connection, query, data_tuple):
        cursor = connection.cursor()
        try:
            cursor.execute(query, data_tuple)
            connection.commit()
            print("Query executed successfully")
            return cursor.lastrowid
        except Error as e:
            print(f"The error '{e}' occurred")

    def execute_read_query(connection, query, data_tuple=()):
        cursor = connection.cursor()
        result = None
        try:
            cursor.execute(query, data_tuple)
            result = cursor.fetchall()
            return result
        except Error as e:
            print(f"The error '{e}' occurred")

    def create_tables():
        connection = QueriesSQLite.create_connection(db_path)

        tabla_uniformes = """
        CREATE TABLE IF NOT EXISTS uniformes(
         codigo TEXT PRIMARY KEY, 
         nombre TEXT NOT NULL,
         talla TEXT NOT NULL, 
         precio REAL NOT NULL, 
         cantidad INTEGER NOT NULL
        );
        """

        tabla_usuarios = """
        CREATE TABLE IF NOT EXISTS usuarios(
         username TEXT PRIMARY KEY, 
         nombre TEXT NOT NULL, 
         password TEXT NOT NULL,
         tipo TEXT NOT NULL
        );
        """

        tabla_ventas = """
        CREATE TABLE IF NOT EXISTS ventas(
         id INTEGER PRIMARY KEY, 
         total REAL NOT NULL, 
         fecha TIMESTAMP,
         username TEXT NOT NULL,
         FOREIGN KEY(username) REFERENCES usuarios(username)
        );
        """

        tabla_ventas_detalle = """
        CREATE TABLE IF NOT EXISTS ventas_detalle(
         id INTEGER PRIMARY KEY,
         id_venta TEXT NOT NULL,
         precio REAL NOT NULL,
         producto TEXT NOT NULL,
         talla TEXT NOT NULL,
         cantidad INTEGER NOT NULL,
         FOREIGN KEY(id_venta) REFERENCES ventas(id),
         FOREIGN KEY(producto) REFERENCES uniformes(codigo)
        );
        """
        tabla_productos_vendidos = """
        CREATE TABLE IF NOT EXISTS total_vendidos(
        id INTEGER PRIMARY KEY,
        producto TEXT NOT NULL,
        talla TEXT NOT NULL,
        total REAL NOT NULL,
        FOREIGN KEY(producto) REFERENCES uniformes(codigo)
        );
        """
        eliminar_tabla_ventas_detalle = """DROP TABLE ventas_detalle"""
        eliminar_tabla_ventas =  """DROP TABLE ventas"""
        elimina_tabla_vendidos = """DROP TABLE total_vendidos"""
        elimina_tabla_usuarios= """DROP TABLE usuarios"""
        elimina_tabla_uniformes= """DROP TABLE uniformes"""

        QueriesSQLite.execute_query(connection, tabla_uniformes, tuple())
        #QueriesSQLite.execute_query(connection, tabla_usuarios, tuple())
        QueriesSQLite.execute_query(connection, tabla_ventas, tuple())
        QueriesSQLite.execute_query(connection, tabla_ventas_detalle, tuple())
        QueriesSQLite.execute_query(connection, tabla_productos_vendidos,tuple())

        #QueriesSQLite.execute_query(connection, eliminar_tabla_ventas_detalle, tuple())
        #QueriesSQLite.execute_query(connection, eliminar_tabla_ventas, tuple())
        #QueriesSQLite.execute_query(connection, elimina_tabla_vendidos, tuple())
        #QueriesSQLite.execute_query(connection, elimina_tabla_usuarios, tuple())
        #QueriesSQLite.execute_query(connection, elimina_tabla_uniformes, tuple())

    #Funcion para revisar las columnas de una tabla
    def get_table_columns(connection, table_name):
        query = f"PRAGMA table_info({table_name});"
        return QueriesSQLite.execute_read_query(connection, query)

if __name__=="__main__":
    connection = QueriesSQLite.create_connection(db_path)
    # QueriesSQLite.create_tables()
    #Obtener columnas de la tabla venta_detalles
    '''
    columnas_venta_Detalles = QueriesSQLite.get_table_columns(connection, "ventas_detalle")
    print("Columnas de la tabla 'ventas_detalle':")
    for column in columnas_venta_Detalles:
        print(f"Nombre: {column[1]}, Tipo: {column[2]}, es clave primaria: {column[5]}")
    
    columnas_venta = QueriesSQLite.get_table_columns(connection, "ventas")
    print("Columnas de la tabla 'ventas':")
    for column in columnas_venta:
        print(f"Nombre: {column[1]}, Tipo: {column[2]}, es clave primaria: {column[5]}")

    columnas_usuarios = QueriesSQLite.get_table_columns(connection, "usuarios")
    print("Columnas de la tabla 'usuarios':")
    for column in columnas_usuarios:
        print(f"Nombre: {column[1]}, Tipo: {column[2]}, es clave primaria: {column[5]}")
    
    columnas_uniformes = QueriesSQLite.get_table_columns(connection, "uniformes")
    print("Columnas de la tabla 'uniformes':")
    for column in columnas_uniformes:
        print(f"Nombre: {column[1]}, Tipo: {column[2]}, es clave primaria: {column[5]}")
    
    columnas_vendidos = QueriesSQLite.get_table_columns(connection, "total_vendidos")
    print("Columnas de la tabla 'vendidos':")
    for column in columnas_vendidos:
        print(f"Nombre: {column[1]}, Tipo: {column[2]}, es clave primaria: {column[5]}")
    '''
    # primer_inventario = """
    #     CREATE TABLE IF NOT EXISTS primer_inventario(
    #      codigo TEXT PRIMARY KEY, 
    #      nombre TEXT NOT NULL,
    #      talla TEXT NOT NULL,  
    #      cantidad INTEGER NOT NULL
    #     );
    #     """
    # QueriesSQLite.execute_query(connection, primer_inventario, tuple())

    # crear_productos = """
    # INSERT INTO 
    #     primer_inventario(codigo, nombre, talla, cantidad)
    # VALUES 
    #     (PYD2,'Playera deportiva T-2',2,10);
    
    # """
    # QueriesSQLite.execute_query(connection, crear_productos, tuple())

    # create_inventario_table = """
    # CREATE TABLE IF NOT EXISTS primer_inventario( 
    #  prenda TEXT NOT NULL,
    #  talla_2 INTEGER NOT NULL,
    #  talla_3 INTEGER NOT NULL,
    #  talla_4 INTEGER NOT NULL,
    #  talla_6 INTEGER NOT NULL,
    #  talla_8 INTEGER NOT NULL,
    #  talla_10 INTEGER NOT NULL,
    #  talla_12 INTEGER NOT NULL,
    #  talla_14 INTEGER NOT NULL,
    #  talla_16 INTEGER NOT NULL,
    #  talla_18_28 INTEGER NOT NULL,
    #  talla_20 INTEGER NOT NULL,
    #  talla_22 INTEGER NOT NULL,
    #  talla_24 INTEGER NOT NULL,
    #  talla_30 INTEGER NOT NULL,
    #  talla_32 INTEGER NOT NULL,
    #  talla_34 INTEGER NOT NULL,
    #  talla_36 INTEGER NOT NULL,
    #  talla_38 INTEGER NOT NULL,
    #  talla_40 INTEGER NOT NULL,
    #  CH_42 INTEGER NOT NULL,
    #  MD_44 INTEGER NOT NULL,
    #  GD_46 INTEGER NOT NULL,
    #  XGD INTEGER NOT NULL, 
    #  total INTEGER NOT NULL
    # );
    # """
    #QueriesSQLite.execute_query(connection, create_inventario_table, tuple()) 

    # tabla_uniformes = """
    #     CREATE TABLE IF NO EXISTS uniformes(
    #      codigo TEXT PRIMARY KEY, 
    #      nombre TEXT NOT NULL,
    #      talla TEXT NOT NULL, 
    #      precio REAL NOT NULL, 
    #      cantidad INTEGER NOT NULL
    #     );
    #     """
    # QueriesSQLite.execute_query(connection, tabla_uniformes, tuple())

    # create_user_table = """
    # CREATE TABLE IF NOT EXISTS usuarios(
    #  username TEXT PRIMARY KEY, 
    #  nombre TEXT NOT NULL, 
    #  password TEXT NOT NULL,
    #  tipo TEXT NOT NULL
    # );
    # """
    # QueriesSQLite.execute_query(connection, create_user_table, tuple()) 

    # crear_producto = """
    # INSERT INTO
    #   primer_inventario (prenda, talla_2,talla_3,talla_4,talla_6,talla_8,talla_10,talla_12,talla_14,talla_16,talla_18_28,talla_20,talla_22,talla_24,talla_30,talla_32,talla_34,talla_36,talla_38,talla_40,CH_42,MD_44,GD_46,XGD,total)
    # VALUES
    #     ('Playera Deportes', 10,35,90,100,125,90,90,120,110,0,0,0,0,0,0,0,0,0,0,80,85,50,12,997),
    #     ('Playera Polo', 5,30,91,108,109,89,99,96,88,0,0,0,0,0,0,0,0,0,0,75,70,33,12,905),
    #     ('Camisa Unisex', 5,30,59,74,74,64,62,66,75,15,0,0,0,0,31,30,45,45,30,15,5,3,0,728),
    #     ('Sweater', 0,16,67,62,78,63,62,76,73,0,0,0,0,0,2,38,32,32,17,10,5,0,0,633),
    #     ('Sudadera Secundaria', 0,0,0,0,0,0,4,61,60,0,0,0,0,0,0,0,0,0,0,55,50,20,12,262),
    #     ('Chamarra Kinder/Primaria IND.', 10,20,97,69,85,55,69,53,60,0,0,0,0,0,0,0,0,0,0,25,0,5,1,554),
    #     ('Pants K/P/S', 8,25,77,110,95,79,89,145,150,0,0,0,0,0,0,0,0,0,0,105,70,30,13,996),
    #     ('Pantalon Kinder-Primaria', 5,25,35,40,65,30,40,30,39,10,5,0,0,0,0,0,0,0,0,0,0,0,0,324),
    #     ('Pantalon Secundaria', 0,0,0,0,0,0,0,5,20,20,15,15,5,10,5,20,20,15,8,2,0,0,0,160),
    #     ('Falda', 0,0,0,0,0,0,0,12,35,32,17,0,0,0,15,20,15,8,2,0,0,0,0,156),
    #     ('Jumper', 5,10,35,40,40,35,40,36,40,7,0,0,0,0,0,0,0,0,0,0,0,0,0,288),
    #     ('Bata Pintor', 0,5,55,51,36,17,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,164),
    #     ('Short', 5,15,45,60,65,50,55,70,70,0,0,0,0,0,0,0,0,0,0,40,45,10,5,535),
    #     ('Chamarra Invierno', 0,10,20,20,20,15,15,9,10,0,0,0,0,0,0,0,0,0,0,5,5,3,2,134) 
    # """
    # QueriesSQLite.execute_query(connection, crear_producto, tuple()) 

    # select_products = "SELECT * from uniformes"
    # productos = QueriesSQLite.execute_read_query(connection, select_products)
    # for producto in productos:
    #     print(producto)


    # usuario_tuple=('persona1', 'Persona 1', 'abc', 'admin')
    # crear_usuario = """
    # INSERT INTO
    #   usuarios (username, nombre, password, tipo)
    # VALUES
    #     (?,?,?,?);
    # """
    # QueriesSQLite.execute_query(connection, crear_usuario, usuario_tuple) 


    # select_users = "SELECT * from usuarios"
    # usuarios = QueriesSQLite.execute_read_query(connection, select_users)
    # for usuario in usuarios:
    #     print("type:", type(usuario), "usuario:",usuario)

    # neuva_data=('Persona 55', '123', 'admin', 'persona1')
    # actualizar = """
    # UPDATE
    #   usuarios
    # SET
    #   nombre=?, password=?, tipo = ?
    # WHERE
    #   username = ?
    # """
    # QueriesSQLite.execute_query(connection, actualizar, neuva_data)

    # select_users = "SELECT * from usuarios"
    # usuarios = QueriesSQLite.execute_read_query(connection, select_users)
    # for usuario in usuarios:
    #     print("type:", type(usuario), "usuario:",usuario)



    # select_products = "SELECT * from uniformes"
    # productos = QueriesSQLite.execute_read_query(connection, select_products)
    # for producto in productos:
    #     print(producto)

    # select_users = "SELECT * from usuarios"
    # usuarios = QueriesSQLite.execute_read_query(connection, select_users)
    # for usuario in usuarios:
    #     print("type:", type(usuario), "usuario:",usuario)

    # producto_a_borrar=('666',)
    # borrar = """DELETE from uniformes where codigo = ?"""
    # QueriesSQLite.execute_query(connection, borrar, producto_a_borrar)

    # select_products = "SELECT * from uniformes"
    # productos = QueriesSQLite.execute_read_query(connection, select_products)
    # for producto in productos:
    #     print(producto)
