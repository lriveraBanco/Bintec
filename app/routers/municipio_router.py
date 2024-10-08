from app.config.db_archivos import *
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.services.file_processor import procesar_pdf_y_guardar_en_excel_medellin
from app.services.procesar_pdf_manizales_ocr import procesar_pdf_y_guardar_en_excel_manizales
import gridfs
import os
import shutil
import openpyxl
import aiofiles  # For asynchronous file operations
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from datetime import datetime
import random


router = APIRouter()

# Simulated function to get file from a SharePoint-like structure
def obtener_archivo_desde_simulacion_sharepoint(filename, municipio):
    ruta_simulada = os.path.join("data", "municipios", municipio, "sharepoint")
    archivo_path = os.path.join(ruta_simulada, filename)
    if not os.path.exists(archivo_path):
        raise HTTPException(status_code=404, detail=f"Archivo {filename} no encontrado en la carpeta simulada de SharePoint.")
    return archivo_path

# Generate a unique filename in case of conflicts
def generar_nombre_unico(base_nombre, extension, ruta_directorio):
    fecha_actual = datetime.now().strftime("%Y%m%d")  # Obtener la fecha actual en formato YYYYMMDD
    nuevo_nombre = f"{base_nombre}_{fecha_actual}{extension}"  # Crear el nombre con fecha
    # Verificar si el archivo ya existe
    if not os.path.exists(os.path.join(ruta_directorio, nuevo_nombre)):
        return nuevo_nombre 
    # Si el nombre ya existe, retornar un error o manejar la situación
    raise FileExistsError(f"El archivo {nuevo_nombre} ya existe en {ruta_directorio}.")

# Generate a unique ID of 5 digits
def generar_id_unico():
    while True:
        nuevo_id = random.randint(10000, 99999)  # Genera un número entre 10000 y 99999
        if fs.find_one({"id": nuevo_id}) is None:  # Verifica que no exista en la colección
            return nuevo_id

# Cache to avoid loading the template repeatedly
@lru_cache(maxsize=10)
def cargar_plantilla_excel(ruta_plantilla):
    if not os.path.exists(ruta_plantilla):
        raise HTTPException(status_code=404, detail="No se encontró la plantilla base.")
    return ruta_plantilla

# Function to run processing in parallel
def procesar_municipio_pdf_async(funcion, *args):
    with ThreadPoolExecutor() as executor:
        futuro = executor.submit(funcion, *args)
        return futuro.result()

# Unified endpoint for processing PDF for multiple municipalities
@router.post("/municipios/procesar-pdf/", tags=["municipios"])
async def procesar_pdf_municipio(
    municipio: str = Form(...),
    archivo: UploadFile = File(None),
    source_type: str = Form(...),
    nombre_base: str = Form(...)
):
    ruta_procesar = None  # Initialize the variable here
    try:
        # Validate source type
        if source_type not in ["upload", "sharepoint"]:
            raise HTTPException(status_code=400, detail="source_type debe ser 'upload' o 'sharepoint'.")

        # Handle uploaded files (upload)
        if source_type == "upload":
            if archivo is None:
                raise HTTPException(status_code=500, detail="Debe subir un archivo si selecciona 'upload'.")

            # Define path to save the PDF
            ruta_directorio_pdf = os.path.join("data", "municipios", municipio, "pdf")
            os.makedirs(ruta_directorio_pdf, exist_ok=True)
            ruta_guardado_pdf = os.path.join(ruta_directorio_pdf, archivo.filename)
            try:
                # Save the PDF file asynchronously
                async with aiofiles.open(ruta_guardado_pdf, "wb") as buffer:
                    contenido = await archivo.read()
                    await buffer.write(contenido)
                ruta_procesar = ruta_guardado_pdf  # Assign after successful save
            except Exception as e:
                raise HTTPException(status_code=500, detail="Error al guardar el archivo PDF.")

        # Handle files from SharePoint
        elif source_type == "sharepoint":
            if archivo and archivo.filename:
                raise HTTPException(status_code=400, detail="No debes subir archivos si vas a consultar desde SharePoint.")
            filename = f"{municipio.capitalize()} Acuerdo.pdf"
            ruta_procesar = obtener_archivo_desde_simulacion_sharepoint(filename, municipio)

        # Validation if ruta_procesar was not assigned
        if ruta_procesar is None:
            raise HTTPException(status_code=500, detail="No se pudo determinar la ruta del archivo a procesar.")

        # Generate a unique Excel filename
        extension_excel = ".xlsx"
        ruta_directorio_base = os.path.join("data", "municipios", municipio, "sharepoint" if source_type == "sharepoint" else "pdf")
        ruta_nuevo_archivo_excel = os.path.join(
            ruta_directorio_base,
            generar_nombre_unico(nombre_base, extension_excel, ruta_directorio_base)
        )

        # Load the Excel template using cache
        ruta_plantilla = cargar_plantilla_excel(os.path.join("data", "municipios", municipio, "plantilla", "Ejemplos industria y comercio3.xlsx"))
        shutil.copyfile(ruta_plantilla, ruta_nuevo_archivo_excel)

        # Process the PDF according to the municipality, in parallel if CPU-bound
        if municipio.lower() == "medellin":
            resultado = procesar_municipio_pdf_async(procesar_pdf_y_guardar_en_excel_medellin, ruta_procesar, municipio)
        elif municipio.lower() == "manizales":
            resultado = procesar_municipio_pdf_async(procesar_pdf_y_guardar_en_excel_manizales, ruta_procesar, municipio)
        else:
            raise HTTPException(status_code=400, detail=f"El municipio '{municipio}' no está soportado.")

        # Update the Excel file with the results
        wb = openpyxl.load_workbook(ruta_nuevo_archivo_excel)
        hoja = wb.active
        hoja["A1"] = f"Datos procesados del archivo: {ruta_procesar}"
        wb.save(ruta_nuevo_archivo_excel)

        # Generate a unique ID
        nuevo_id = generar_id_unico()

        # Save the Excel file to MongoDB using GridFS
        with open(ruta_nuevo_archivo_excel, "rb") as archivo_excel:
            contenido_excel = archivo_excel.read()
            # Crear un documento para MongoDB
            documento = {
                "id": nuevo_id,
                "nombre_archivo": os.path.basename(ruta_nuevo_archivo_excel),
                "contenido": contenido_excel,
                "municipio": municipio,
                "fecha": datetime.now()
            }
            fs.put(contenido_excel, filename=os.path.basename(ruta_nuevo_archivo_excel), id=nuevo_id)  # Save to GridFS

        return {
            "mensaje": f"Archivo PDF procesado para {municipio} y actualizado",
            "resultado": {
                "mensaje": "Datos guardados en Excel correctamente y almacenados en MongoDB",
                "archivo": ruta_nuevo_archivo_excel,
                "id": nuevo_id  # Devolver el ID generado
            }
        }

    except HTTPException as http_ex:
        raise http_ex  # Reraise HTTPExceptions as is
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))