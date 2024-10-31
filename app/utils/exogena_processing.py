import pytesseract
import pdfplumber
from PIL import Image, ImageFilter
import re

pytesseract.pytesseract.tesseract_cmd = r'C:\Users\lrivera\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'

# Función para preprocesar imágenes
def preprocesar_imagen(imagen):
    imagen_gris = imagen.convert('L')  # Convertir a escala de grises
    imagen_gris = imagen_gris.filter(ImageFilter.SHARPEN)  # Aumentar el enfoque
    umbral = 128
    imagen_binaria = imagen_gris.point(lambda x: 0 if x < umbral else 255, '1')
    return imagen_binaria

# Función para extraer texto desde un archivo PDF
def extraer_texto_desde_pdf(pdf_file):
    texto_extraido = ""
    with pdfplumber.open(pdf_file) as pdf:
        for pagina in pdf.pages:
            texto_extraido += pagina.extract_text() + "\n"
    return texto_extraido

# Función para extraer información de la tabla de datos exógenos
def extraer_tabla_informacion_exogena(texto):
    filas = texto.splitlines()
    datos = []
    for fila in filas:
        columnas = re.split(r'\s{2,}', fila.strip())  # Separar por múltiples espacios
        if len(columnas) >= 2:  # Validar que haya al menos dos columnas
            datos.append(columnas)
    return datos

# Función para filtrar y reemplazar datos
def filtrar_y_reemplazar(datos):
    # Implementar lógica de filtrado y reemplazo según sea necesario
    return datos
