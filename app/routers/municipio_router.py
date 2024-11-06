from app.config.db_archivos import *
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.services.file_processor import procesar_pdf_y_guardar_en_excel_medellin
from app.services.procesar_pdf_manizales_ocr import procesar_pdf_y_guardar_en_excel_manizales
import os
import shutil
import openpyxl
import aiofiles
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from datetime import datetime
import random
import unicodedata
import logging
import pandas as pd 

# Configuración de logging
logging.basicConfig(level=logging.INFO)

router = APIRouter()
import unicodedata
import pandas as pd
from fastapi import HTTPException
import logging
import os

# Configuración de logging
logging.basicConfig(level=logging.INFO)

def normalizar_nombre(nombre):
    """
    Normaliza el texto, elimina acentos y convierte a mayúsculas.
    """
    # Normaliza el texto eliminando los acentos
    nombre_normalizado = unicodedata.normalize('NFD', nombre)
    nombre_normalizado = ''.join([c for c in nombre_normalizado if unicodedata.category(c) != 'Mn'])
    return nombre_normalizado.upper()

def cargar_codigos_dane(municipio):
    """
    Carga el código DANE del municipio desde un archivo Excel.
    """
    ruta_dane =  os.path.join("data", "municipios",  "codigo_dane.xlsx")
    
    try:
        # Verificar si el archivo existe
        if not os.path.exists(ruta_dane):
            raise HTTPException(status_code=404, detail=f"El archivo {ruta_dane} no se encontró.")
        
        # Leer el archivo Excel con pandas
        df = pd.read_excel(ruta_dane, sheet_name="codigo_dane", engine="openpyxl")
        
        # Verificar que las columnas existen
        if 'MUNICIPIO' not in df.columns or 'CODIGO_DANE' not in df.columns:
            raise HTTPException(status_code=400, detail="Las columnas 'MUNICIPIO' o 'CODIGO_DANE' no están presentes.")
        
        df.columns = df.columns.str.strip()  # Eliminar espacios innecesarios en los nombres de las columnas

        # Normalizar el nombre del municipio recibido y los del DataFrame
        municipio_normalizado = normalizar_nombre(municipio)
        df['MUNICIPIO'] = df['MUNICIPIO'].apply(normalizar_nombre)  # Normalizar las filas del DataFrame

        # Buscar el código DANE correspondiente al municipio
        codigo_dane = df[df['MUNICIPIO'] == municipio_normalizado]['CODIGO_DANE']
        
        if codigo_dane.empty:
            raise HTTPException(status_code=404, detail=f"No se encontró el código DANE para el municipio '{municipio}'.")
        
        # Devolver el código DANE encontrado
        return codigo_dane.iloc[0]  

    except Exception as e:
        logging.error(f"Error al cargar el archivo o encontrar el código DANE: {e}")
        raise HTTPException(status_code=500, detail=f"Error al cargar el archivo o encontrar el código DANE: {e}")


def normalize_string(s):
    return ''.join(
        c for c in unicodedata.normalize('NFD', s)
        if unicodedata.category(c) != 'Mn'
    ).lower()

def normalize_string_capitalized(s):
    return normalize_string(s).capitalize()

def obtener_archivo_desde_simulacion_sharepoint(filename, municipio):
    ruta_simulada = os.path.join("data", "municipios", municipio, "sharepoint")
    archivo_path = os.path.join(ruta_simulada, filename)
    if not os.path.exists(archivo_path):
        raise HTTPException(status_code=404, detail=f"Archivo {filename} no encontrado en la carpeta simulada de SharePoint.")
    return archivo_path

def generar_id_unico():
    while True:
        nuevo_id = random.randint(10000, 99999)
        if fs.find_one({"id": nuevo_id}) is None:
            return nuevo_id

def generar_nombre_unico(base_nombre, extension, ruta_directorio, nuevo_id, codigo_dane):
    nuevo_nombre = f"{base_nombre}_{codigo_dane}_{nuevo_id}{extension}"
    if not os.path.exists(os.path.join(ruta_directorio, nuevo_nombre)):
        return nuevo_nombre 
    raise FileExistsError(f"El archivo {nuevo_nombre} ya existe en {ruta_directorio}.")

@lru_cache(maxsize=10)
def cargar_plantilla_excel(ruta_plantilla):
    if not os.path.exists(ruta_plantilla):
        raise HTTPException(status_code=404, detail="No se encontró la plantilla base.")
    return ruta_plantilla

def procesar_municipio_pdf_async(funcion, *args):
    with ThreadPoolExecutor() as executor:
        futuro = executor.submit(funcion, *args)
        return futuro.result()

@router.post("/municipios/procesar-pdf/", tags=["municipios"])
async def procesar_pdf_municipio(
    municipio: str = Form(...),
    archivo: UploadFile = File(None),
    source_type: str = Form(...),
    nombre_base: str = Form(...),
):
    municipio_normalizado = normalize_string(municipio)
    municipio_capitalizado = normalize_string_capitalized(municipio)
    ruta_procesar = None

    try:
        # Cargar los códigos DANE
        codigo_dane = cargar_codigos_dane(municipio)
        if not codigo_dane:
            raise HTTPException(status_code=500, detail="Error al cargar los códigos DANE.")
        
        nuevo_id = generar_id_unico()

        if source_type not in ["upload", "sharepoint"]:
            raise HTTPException(status_code=400, detail="source_type debe ser 'upload' o 'sharepoint'.")

        # Procesar el archivo según el tipo de fuente
        if source_type == "upload":
            if archivo is None:
                raise HTTPException(status_code=400, detail="Debe subir un archivo si selecciona 'upload'.")

            ruta_directorio_pdf = os.path.join("data", "municipios", municipio_normalizado, "pdf")
            os.makedirs(ruta_directorio_pdf, exist_ok=True)
            ruta_guardado_pdf = os.path.join(ruta_directorio_pdf, archivo.filename)
            async with aiofiles.open(ruta_guardado_pdf, "wb") as buffer:
                contenido = await archivo.read()
                await buffer.write(contenido)
            ruta_procesar = ruta_guardado_pdf

        elif source_type == "sharepoint":
            if archivo and archivo.filename:
                raise HTTPException(status_code=400, detail="No debes subir archivos si vas a consultar desde SharePoint.")
            filename = f"{municipio_capitalizado} Acuerdo.pdf"
            ruta_procesar = obtener_archivo_desde_simulacion_sharepoint(filename, municipio_normalizado)

        if ruta_procesar is None:
            raise HTTPException(status_code=500, detail="No se pudo determinar la ruta del archivo a procesar.")

        extension_excel = ".xlsx"
        ruta_directorio_base = os.path.join("data", "municipios", municipio_normalizado, "sharepoint" if source_type == "sharepoint" else "pdf")
        ruta_nuevo_archivo_excel = os.path.join(
            ruta_directorio_base,
            generar_nombre_unico(nombre_base, extension_excel, ruta_directorio_base, nuevo_id, codigo_dane)
        )

        # Cargar plantilla y procesar datos
        ruta_plantilla = cargar_plantilla_excel(os.path.join("data", "municipios", municipio_normalizado, "plantilla", "Ejemplos industria y comercio3.xlsx"))
        shutil.copyfile(ruta_plantilla, ruta_nuevo_archivo_excel)

        # Procesadores específicos para cada municipio
        procesadores_municipios = {
            "medellin": procesar_pdf_y_guardar_en_excel_medellin,
            "manizales": procesar_pdf_y_guardar_en_excel_manizales,
        }

        if municipio_normalizado in procesadores_municipios:
            funcion_procesamiento = procesadores_municipios[municipio_normalizado]
            resultado = procesar_municipio_pdf_async(funcion_procesamiento, ruta_procesar, municipio_normalizado)
        else:
            raise HTTPException(status_code=400, detail=f"El municipio '{municipio}' no está soportado.")

        wb = openpyxl.load_workbook(ruta_nuevo_archivo_excel)
        hoja = wb.active
        hoja["A1"] = f"Datos procesados del archivo: {ruta_procesar}"
        wb.save(ruta_nuevo_archivo_excel)

        # Guardar archivo en MongoDB
        with open(ruta_nuevo_archivo_excel, "rb") as archivo_excel:
            contenido_excel = archivo_excel.read()
            documento = {
                "id": nuevo_id,
                "nombre_archivo": os.path.basename(ruta_nuevo_archivo_excel),
                "contenido": contenido_excel,
                "municipio": municipio_normalizado,
                "fecha": datetime.now(),
                "Tipo_recurso": source_type,
                "codigo_dane": int(codigo_dane)
            }
            fs.put(contenido_excel, filename=os.path.basename(ruta_nuevo_archivo_excel), id=nuevo_id, metadata=documento)

        return {
            "mensaje": f"Archivo PDF procesado para {municipio} y actualizado",
            "resultado": {
                "mensaje": "Datos guardados en Excel correctamente y almacenados en MongoDB",
                "archivo": ruta_nuevo_archivo_excel.replace("/", "\\"),  # Para estilo de ruta en Windows
                "id": nuevo_id,
                "codigo_dane": int(codigo_dane)
            }
        }

    except Exception as e:
        logging.error(f"Error procesando municipio {municipio}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
