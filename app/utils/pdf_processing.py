import fitz  # PyMuPDF
from PIL import Image
import pytesseract
import re
import os

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
    umbral = 128
    imagen_binaria = imagen_gris.point(lambda x: 0 if x < umbral else 255, '1')
    return imagen_binaria

def extraer_texto_pdf(ruta_pdf):
    documento = fitz.open(ruta_pdf)
    texto_completo = ""
    for pagina in documento:
        texto = pagina.get_text()
        if texto.strip():  
            texto_completo += texto
        else:
            pix = pagina.get_pixmap()
            imagen = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            imagen_procesada = preprocesar_imagen(imagen)
            texto_ocr = pytesseract.image_to_string(imagen_procesada)
            texto_completo += texto_ocr
    return texto_completo

def buscar_articulo_71(texto):
    patron_articulo_71 = re.compile(r'ART[IÍ]CULO\s+71\.?\s+C[ÓO]DIGOS\s+DE\s+ACTIVIDAD\s+Y\s+TARIFAS\s+DE\s+¡NDUSTRIA\s+Y\s+COMERCIO\.', re.IGNORECASE)
    coincidencia = patron_articulo_71.search(texto)
    if coincidencia:
        return texto[coincidencia.start():]
    return None

def corregir_codigo_ciiu(codigo):
    """Corrige posibles errores comunes en códigos CIIU extraídos por OCR."""
    codigo = re.sub(r'(\d{4})4$', r'\1A', codigo)  # '45114' a '4511A'
    codigo = re.sub(r'(\d{4})1$', r'\1B', codigo)  # '63111' a '6311B'
    codigo = re.sub(r'O', '0', codigo)
    return codigo

def buscar_tarifa_2024(texto, codigo_ciiu):
    if not codigo_ciiu:
        return None
    codigo_ciiu = corregir_codigo_ciiu(str(codigo_ciiu))  # Aplicar corrección antes de la búsqueda
    patron_simple = re.compile(rf'{codigo_ciiu}\s+[^\d]*\s+(\d+)', re.IGNORECASE | re.MULTILINE)
    patron_multiple = re.compile(rf'{codigo_ciiu}\s+[A-Za-z\s,]+\s+\d+\s+(\d+)\s+\d+\s+\d+', re.IGNORECASE | re.MULTILINE)
    coincidencia_multiple = patron_multiple.search(texto)
    if coincidencia_multiple:
        return coincidencia_multiple.group(1)
    coincidencia_simple = patron_simple.search(texto)
    if coincidencia_simple:
        return coincidencia_simple.group(1)
    return None

def buscar_articulo_97(texto):
    patron_articulo_97 = re.compile(r'97\.?\s+TARIFA\s*:\s*Será\s+el\s+(\d+)%', re.IGNORECASE)
    coincidencia = patron_articulo_97.search(texto)
    if coincidencia:
        return f"{coincidencia.group(1)}%"
    return None

def buscar_articulo_105(texto):
    patron_articulo_105 = re.compile(
        r'105\.?\s+TARIFA\s*:\s*será\s+equivalente\s+al\s+([\w\s]+)\s+por\s+ciento',
        re.IGNORECASE
    )
    coincidencia = patron_articulo_105.search(texto)
    if coincidencia:
        porcentaje_palabra = coincidencia.group(1).strip().lower()
        porcentaje_mapeo = {
            "uno": "1", "dos": "2", "tres": "3", "cuatro": "4", "cinco": "5",
            "seis": "6", "siete": "7", "ocho": "8", "nueve": "9", "diez": "10"
        }
        return porcentaje_mapeo.get(porcentaje_palabra, "1") + "%"
    return None

def buscar_valor_articulo_56(texto):
    # Patrón para buscar el Artículo 56
    patron_articulo_56 = re.compile(
        r'ART¡CULO\s+56.*?(suma\s+equivalente\s+a\s+(\d+\s*,\s*\d+|\d+)\s*UYT)',
        re.IGNORECASE | re.DOTALL
    )
    coincidencia = patron_articulo_56.search(texto)
    if coincidencia:
        valor_uyt_uvt = coincidencia.group(2).replace(" ", "")  # Obtener el valor y quitar espacios
        return valor_uyt_uvt
    return None

