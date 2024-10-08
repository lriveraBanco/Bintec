from app.config.db_archivos import *
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.services.file_processor import procesar_pdf_y_guardar_en_excel_medellin
from app.services.procesar_pdf_manizales_ocr import procesar_pdf_y_guardar_en_excel_manizales
import os
import shutil
import openpyxl
import aiofiles  # Para operaciones de archivo asíncronas
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from datetime import datetime
import random
import unicodedata
import logging

# Configuración del logging
logging.basicConfig(level=logging.INFO)

router = APIRouter()

def normalize_string(s):
    # Elimina acentos o tildes y convierte a minúsculas
    return ''.join(
        c for c in unicodedata.normalize('NFD', s)
        if unicodedata.category(c) != 'Mn'
    ).lower()
def normalize_string_capitalized(s):
    # Elimina acentos o tildes, convierte en minúsculas y capitaliza la primera letra
    return normalize_string(s).capitalize()

# Simulated function to get file from a SharePoint-like structure
def obtener_archivo_desde_simulacion_sharepoint(filename, municipio):
    ruta_simulada = os.path.join("data", "municipios", municipio, "sharepoint")
    archivo_path = os.path.join(ruta_simulada, filename)
    if not os.path.exists(archivo_path):
        raise HTTPException(status_code=404, detail=f"Archivo {filename} no encontrado en la carpeta simulada de SharePoint.")
    return archivo_path

# Generar un nombre único en caso de conflictos
def generar_nombre_unico(base_nombre, extension, ruta_directorio):
    fecha_actual = datetime.now().strftime("%Y%m%d-%H_%M")
    nuevo_nombre = f"{base_nombre}_{fecha_actual}{extension}"  # Crear el nombre con fecha
    # Verificar si el archivo ya existe
    if not os.path.exists(os.path.join(ruta_directorio, nuevo_nombre)):
        return nuevo_nombre 
    # Si el nombre ya existe, retornar un error o manejar la situación
    raise FileExistsError(f"El archivo {nuevo_nombre} ya existe en {ruta_directorio}.")

# Generar un ID único de 5 dígitos
def generar_id_unico():
    while True:
        nuevo_id = random.randint(10000, 99999)  # Genera un número entre 10000 y 99999
        if fs.find_one({"id": nuevo_id}) is None:  # Verifica que no exista en la colección
            return nuevo_id

# Cache para evitar cargar la plantilla repetidamente
@lru_cache(maxsize=10)
def cargar_plantilla_excel(ruta_plantilla):
    if not os.path.exists(ruta_plantilla):
        raise HTTPException(status_code=404, detail="No se encontró la plantilla base.")
    return ruta_plantilla

# Función para ejecutar el procesamiento en paralelo
def procesar_municipio_pdf_async(funcion, *args):
    with ThreadPoolExecutor() as executor:
        futuro = executor.submit(funcion, *args)
        return futuro.result()


@router.post("/municipios/procesar-pdf/", tags=["municipios"])
async def procesar_pdf_municipio(
    municipio: str = Form(...),
    archivo: UploadFile = File(None),
    source_type: str = Form(...),
    nombre_base: str = Form(...)
):
    # Normalizar el nombre del municipio
    municipio_normalizado = normalize_string(municipio)
    municipio_capitalizado = normalize_string_capitalized(municipio)
    ruta_procesar = None
    
    try:
        # Validar el tipo de fuente
        if source_type not in ["upload", "sharepoint"]:
            raise HTTPException(status_code=400, detail="source_type debe ser 'upload' o 'sharepoint'.")

        # Manejar archivos subidos (upload)
        if source_type == "upload":
            if archivo is None:
                raise HTTPException(status_code=400, detail="Debe subir un archivo si selecciona 'upload'.")

            # Definir la ruta para guardar el PDF
            ruta_directorio_pdf = os.path.join("data", "municipios", municipio_normalizado, "pdf")
            os.makedirs(ruta_directorio_pdf, exist_ok=True)
            ruta_guardado_pdf = os.path.join(ruta_directorio_pdf, archivo.filename)
            try:
                # Guardar el archivo PDF de forma asíncrona
                async with aiofiles.open(ruta_guardado_pdf, "wb") as buffer:
                    contenido = await archivo.read()
                    await buffer.write(contenido)
                ruta_procesar = ruta_guardado_pdf
            except Exception as e:
                raise HTTPException(status_code=500, detail="Error al guardar el archivo PDF.")

        # Manejar archivos desde SharePoint
        elif source_type == "sharepoint":
            if archivo and archivo.filename:
                raise HTTPException(status_code=400, detail="No debes subir archivos si vas a consultar desde SharePoint.")
            filename = f"{municipio_capitalizado} Acuerdo.pdf"
            ruta_procesar = obtener_archivo_desde_simulacion_sharepoint(filename, municipio_normalizado)

        # Validación si ruta_procesar no fue asignada
        if ruta_procesar is None:
            raise HTTPException(status_code=500, detail="No se pudo determinar la ruta del archivo a procesar.")

        # Generar un nombre de archivo Excel único
        extension_excel = ".xlsx"
        ruta_directorio_base = os.path.join("data", "municipios", municipio_normalizado, "sharepoint" if source_type == "sharepoint" else "pdf")
        ruta_nuevo_archivo_excel = os.path.join(
            ruta_directorio_base,
            generar_nombre_unico(nombre_base, extension_excel, ruta_directorio_base)
        )

        # Cargar la plantilla de Excel usando caché
        ruta_plantilla = cargar_plantilla_excel(os.path.join("data", "municipios", municipio_normalizado, "plantilla", "Ejemplos industria y comercio3.xlsx"))
        shutil.copyfile(ruta_plantilla, ruta_nuevo_archivo_excel)

        # Procesar el PDF según el municipio
        if municipio_normalizado == "medellin":
            resultado = procesar_municipio_pdf_async(procesar_pdf_y_guardar_en_excel_medellin, ruta_procesar, municipio_normalizado)
        elif municipio_normalizado == "manizales":
            resultado = procesar_municipio_pdf_async(procesar_pdf_y_guardar_en_excel_manizales, ruta_procesar, municipio_normalizado)
        else:
            raise HTTPException(status_code=400, detail=f"El municipio '{municipio}' no está soportado.")

        # Actualizar el archivo Excel con los resultados
        wb = openpyxl.load_workbook(ruta_nuevo_archivo_excel)
        hoja = wb.active
        hoja["A1"] = f"Datos procesados del archivo: {ruta_procesar}"
        wb.save(ruta_nuevo_archivo_excel)

        # Generar un ID único
        nuevo_id = generar_id_unico()

        # Guardar el archivo Excel en MongoDB usando GridFS
        with open(ruta_nuevo_archivo_excel, "rb") as archivo_excel:
            contenido_excel = archivo_excel.read()
            # Crear un documento para MongoDB
            documento = {
                "id": nuevo_id,
                "nombre_archivo": os.path.basename(ruta_nuevo_archivo_excel),
                "contenido": contenido_excel,
                "municipio": municipio_normalizado,
                "fecha": datetime.now(),
                "Tipo_recurso": source_type  # Asegúrate de que aquí esté correctamente asignado
            }
            fs.put(contenido_excel, filename=os.path.basename(ruta_nuevo_archivo_excel), id=nuevo_id, metadata=documento)

        return {
            "mensaje": f"Archivo PDF procesado para {municipio} y actualizado",
            "resultado": {
                "mensaje": "Datos guardados en Excel correctamente y almacenados en MongoDB",
                "archivo": ruta_nuevo_archivo_excel,
                "id": nuevo_id  # Devolver el ID generado
            }
        }

    except Exception as e:
        logging.error(f"Error procesando municipio {municipio}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
