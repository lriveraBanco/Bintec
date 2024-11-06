import pytesseract
import pdfplumber
import pandas as pd
from PIL import Image, ImageFilter
import re
import fitz
import openpyxl
from app.config.db_calendario import fs

# Configuración de Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\lrivera\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'

# Función para preprocesar imágenes
def preprocesar_imagen(imagen):
    """Aplica técnicas de preprocesamiento para mejorar la calidad del OCR."""
    imagen_gris = imagen.convert('L')  # Convertir a escala de grises
    imagen_gris = imagen_gris.filter(ImageFilter.SHARPEN)  # Aumentar el enfoque
    umbral = 128
    imagen_binaria = imagen_gris.point(lambda x: 0 if x < umbral else 255, '1')
    return imagen_binaria

# Función para extraer texto desde PDF
def extraer_texto_desde_pdf(pdf_path):
    documento = fitz.open(pdf_path)
    texto_completo = ""
    for pagina in documento:
        texto = pagina.get_text()
        if texto.strip():  
            texto_completo += texto
        else:
            pix = pagina.get_pixmap()
            imagen = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            imagen = imagen.resize((int(imagen.width * 2), int(imagen.height * 2)))  # Sin ANTIALIAS
            imagen_procesada = preprocesar_imagen(imagen)
            texto_ocr = pytesseract.image_to_string(imagen_procesada, lang='spa', config='--psm 6')  # Probar con psm 6
            texto_completo += texto_ocr
    return texto_completo

# Función para buscar la tabla en el artículo de "información exógena"
def extraer_tabla_informacion_exogena(texto):
    # Ajustamos el patrón para capturar el último dígito (0-9) y la fecha en el formato "dd de mes de yyyy"
    patron_fila = r"(\d)\s+(\d{1,2}\sde\s[a-zA-Z]+\sde\s\d{4})"
    datos = re.findall(patron_fila, texto)
    return datos

# Función para filtrar y reemplazar el 8 por "Bancolombia" y el 5 por "Banca de Inversiones Bancolombia"
def filtrar_y_reemplazar(datos):
    datos_filtrados = []
    for dato in datos:
        ultimo_digito = dato[0]
        fecha_limite = dato[1]
        
        # Filtrar solo el 8 y el 5
        if ultimo_digito == '8':
            datos_filtrados.append(["Bancolombia", fecha_limite])
        elif ultimo_digito == '5':
            datos_filtrados.append(["Banca de Inversiones Bancolombia", fecha_limite])
        else:
            datos_filtrados.append([ultimo_digito, fecha_limite])  # Agregar otros dígitos si es necesario
    
    return datos_filtrados

# Función para procesar los archivos de exógena y calendario, y crear un Excel
def procesar_exogena_y_calendario(archivo_exogena, archivo_calendario, nombre_base):
    # Procesar el archivo de exógena
    texto_exogena = extraer_texto_desde_pdf(archivo_exogena)
    texto_exogena = re.sub(r'\s+', ' ', texto_exogena)  # Limpiar el texto
    tabla_datos_exogena = extraer_tabla_informacion_exogena(texto_exogena)
    datos_filtrados_exogena = filtrar_y_reemplazar(tabla_datos_exogena)

    # Procesar el archivo de calendario
    texto_calendario = extraer_texto_desde_pdf(archivo_calendario)
    texto_calendario = re.sub(r'\s+', ' ', texto_calendario)  # Limpiar el texto
    tabla_datos_calendario = extraer_tabla_informacion_exogena(texto_calendario)
    datos_filtrados_calendario = filtrar_y_reemplazar(tabla_datos_calendario)

    # Crear un archivo Excel con ambos conjuntos de datos
    wb = openpyxl.Workbook()
    
    # Agregar datos de exógena
    hoja_exogena = wb.active
    hoja_exogena.title = "Exógena"
    hoja_exogena.append(["Último dígito de identificación", "Fecha límite de entrega"])
    for fila in datos_filtrados_exogena:
        hoja_exogena.append(fila)
    
    # Agregar datos de calendario en una nueva hoja
    hoja_calendario = wb.create_sheet("Calendario")
    hoja_calendario.append(["Último dígito de identificación", "Fecha límite de entrega"])
    for fila in datos_filtrados_calendario:
        hoja_calendario.append(fila)
    
    # Guardar el archivo Excel
    ruta_excel = f"{nombre_base}.xlsx"
    wb.save(ruta_excel)

    # Guardar el archivo Excel en MongoDB
    with open(ruta_excel, "rb") as excel_file:
        file_data = excel_file.read()
        fs.put(file_data, filename=nombre_base)
    
    return ruta_excel
