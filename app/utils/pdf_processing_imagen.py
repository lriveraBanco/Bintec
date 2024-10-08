import os
import re
import numpy as np
from PIL import Image, ImageFilter
import pytesseract
from pdf2image import convert_from_path


# Configurar pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\lrivera\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'


def letra_a_indice_columna(letra_columna):
    """Convierte la letra de una columna de Excel en un índice numérico."""
    indice = 0
    for i, letra in enumerate(reversed(letra_columna)):
        indice += (ord(letra.upper()) - ord('A') + 1) * (26 ** i)
    return indice

def preprocesar_imagen(imagen):
    """Aplica técnicas de preprocesamiento para mejorar la calidad del OCR.""" 
    imagen_gris = imagen.convert('L')
    imagen_suavizada = imagen_gris.filter(ImageFilter.MedianFilter(size=3))
    imagen_array = np.array(imagen_suavizada)
    imagen_contraste = 255 - (255 - imagen_array) * 2
    imagen_contraste = Image.fromarray(np.uint8(imagen_contraste))
    imagen_binaria = imagen_contraste.point(lambda x: 0 if x < 140 else 255, '1')
    return imagen_binaria

def procesar_pdf_manizales_ocr(ruta_pdf):

    if not os.path.exists(ruta_pdf):
        print(f"El archivo PDF no existe: {ruta_pdf}")
        return None
    paginas_imagenes = convert_from_path(ruta_pdf, poppler_path='C:\\Users\\lrivera\\Downloads\\INTEGRACION\\Bintec-Versiones\\Bintec-2024 -1.0.0\\files\\Release-24.07.0-0\\poppler-24.07.0\\Library\\bin')
    texto_completo = ""
    for imagen in paginas_imagenes:
        imagen_preprocesada = preprocesar_imagen(imagen)
        custom_config = r'--oem 3 --psm 6'
        texto_pdf = pytesseract.image_to_string(imagen_preprocesada, config=custom_config, lang='spa')
        texto_completo += texto_pdf + "\n"
    return texto_completo

def limpiar_texto(texto):
    """Corrige algunos de los errores más comunes en el OCR."""
    correcciones = {
        'fiementos': 'elementos',
        'impguesto': 'impuesto',
        'tableros': 'tableros',
        'avianes': 'avisos',
        'suieto': 'sujeto',
        'activa': 'activo',
        'sujeins': 'sujetos',
        'imoucsto': 'impuesto',
        'industio': 'industria',
        'Men\'zales': 'Manizales',
        'art[íi]cul[o0]': 'artículo',
        'equivelente': 'equivalente',
        'corenío': 'comercio',
        'UNT':'UVT',
        'estiva ente':'equivalente'
    }
    for error, correccion in correcciones.items():
        texto = re.sub(error, correccion, texto, flags=re.IGNORECASE)
    return texto

def buscar_articulo_44(texto):
    """Busca el valor del UVT en el Artículo 44 del texto corregido."""
    texto = limpiar_texto(texto)
    # Patrón para encontrar el Artículo 44 y el UVT entre paréntesis
    patron_articulo_44 = re.compile(
        r'ART[ÍI]CULO\s+44.*?adicional.*?suma.*?\(\s*(\d+)\s*\)',
        re.DOTALL | re.IGNORECASE
    )
    coincidencia = patron_articulo_44.search(texto)
    if coincidencia:
        return coincidencia.group(1) 
    return None



def buscar_articulo_92(texto):
    """Busca el artículo 92 con porcentaje de tarifa en el texto corregido."""
    texto = limpiar_texto(texto) 
    # Patrón flexible para encontrar el porcentaje en el Artículo 92
    patron_articulo_92 = re.compile(
        r'art[íi]cul[o0]\s*92.*?tarifa.*?(?:\d{1,2}\s*%|\(\d{1,2}\s*%\))',
        re.DOTALL | re.IGNORECASE
    )
    coincidencia = patron_articulo_92.search(texto)
    if coincidencia:
        # Buscar específicamente el número dentro del contexto del artículo
        porcentaje = re.search(r'(\d{1,2}\s*%)', coincidencia.group())
        if porcentaje:
            return porcentaje.group(1)
    
    print("No se encontró una coincidencia en el texto.")
    return None
