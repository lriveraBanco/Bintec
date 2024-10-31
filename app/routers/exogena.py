from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import openpyxl
from datetime import datetime
import random
import logging
import unicodedata
from app.utils.exogena_processing import preprocesar_imagen, extraer_texto_desde_pdf, extraer_tabla_informacion_exogena, filtrar_y_reemplazar
from app.config.db_archivos import fs
from PIL import Image
import pytesseract

# Configuración del logging
logging.basicConfig(level=logging.INFO)

router = APIRouter()

# Normalización de strings
def normalize_string(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn').lower()

# Generar un ID único de 5 dígitos
def generar_id_unico():
    while True:
        nuevo_id = random.randint(10000, 99999)
        return nuevo_id

@router.post("/procesar-exogena/", tags=["municipios"])
async def procesar_exogena(
    municipio: str = Form(...),
    archivo_exogena: UploadFile = File(...),
    archivo_calendario: UploadFile = File(...),
    source_type: str = Form(...),
    nombre_base: str = Form(...)
):
    municipio_normalizado = normalize_string(municipio)
    
    # Validar el tipo de fuente
    if source_type not in ["upload"]:
        raise HTTPException(status_code=400, detail="source_type debe ser 'upload'.")

    try:
        # Procesar archivo de exógena
        if archivo_exogena.filename.endswith('.png'):
            imagen = Image.open(archivo_exogena.file)
            imagen_procesada = preprocesar_imagen(imagen)
            texto_exogena = pytesseract.image_to_string(imagen_procesada)
        else:
            texto_exogena = extraer_texto_desde_pdf(archivo_exogena.file)

        # Procesar archivo de calendario
        texto_calendario = extraer_texto_desde_pdf(archivo_calendario.file)

        # Extraer tablas de información del texto procesado
        tabla_exogena = extraer_tabla_informacion_exogena(texto_exogena)
        tabla_calendario = extraer_tabla_informacion_exogena(texto_calendario)

        # Filtrar y limpiar la información obtenida
        datos_exogena = filtrar_y_reemplazar(tabla_exogena)
        datos_calendario = filtrar_y_reemplazar(tabla_calendario)

    except Exception as e:
        logging.error(f"Error al procesar los archivos: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al procesar los archivos.")

    # Guardar la información en un archivo Excel
    try:
        # Crear un nuevo archivo Excel
        wb = openpyxl.Workbook()
        hoja_exogena = wb.active
        hoja_exogena.title = "Exógena"
        
        hoja_calendario = wb.create_sheet("Calendario")

        # Agregar información básica de los archivos procesados
        hoja_exogena.append(["Último dígito de identificación", "Fecha límite de entrega"])
        for fila in datos_exogena:
            hoja_exogena.append(fila)
        
        hoja_calendario.append(["Información de calendario"])
        for fila in datos_calendario:
            hoja_calendario.append(fila)

        # Guardar el archivo Excel en un archivo temporal
        extension_excel = ".xlsx"
        nombre_unico_excel = f"{normalize_string(nombre_base)}_{datetime.now().strftime('%Y%m%d-%H%M')}{extension_excel}"
        wb.save(nombre_unico_excel)
        logging.info(f"Archivo Excel guardado en: {nombre_unico_excel}")

    except Exception as e:
        logging.error(f"Error al crear o guardar el archivo Excel: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al crear o guardar el archivo Excel.")

    # Generar un ID único y guardar el archivo Excel en MongoDB
    try:
        nuevo_id = generar_id_unico()
        with open(nombre_unico_excel, "rb") as archivo_excel:
            contenido_excel = archivo_excel.read()
            documento = {
                "id": nuevo_id,
                "nombre_archivo": nombre_unico_excel,
                "contenido": contenido_excel,
                "municipio": municipio_normalizado,
                "fecha": datetime.now(),
                "tipo_recurso": source_type
            }
            # Guardar en MongoDB
            fs.put(contenido_excel, filename=nombre_unico_excel, metadata=documento)

    except Exception as e:
        logging.error(f"Error al guardar el archivo Excel en MongoDB: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al guardar el archivo Excel en MongoDB.")

    return {
        "mensaje": f"Archivos de Exógena y Calendario procesados para {municipio} y actualizados",
        "resultado": {
            "mensaje": "Datos guardados en Excel correctamente y almacenados en MongoDB",
            "archivo": nombre_unico_excel,
            "id": nuevo_id
        }
    }
