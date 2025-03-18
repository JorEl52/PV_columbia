from barcode import Code128
from barcode.writer import ImageWriter
import os

#Obtener ruta del archivo actual
current_dir = os.path.dirname(__file__)
#Crear la ruta del archivo de salida
output_path = os.path.join(current_dir, "bata_preescolar_t3")

codigo = "BP3"
barcode = Code128(codigo, writer=ImageWriter())

#Configurar las medidas del codigo de barras
options = {
    'module_width': 1,
    'module_height': 30,
    'font_size': 20,
    'text_distance': 10.0,
    'quiet_zone': 6.5,
    'write_text': True,
    'backgroud': "white",
    'foreground': "black"
}

barcode.save(output_path, options=options)