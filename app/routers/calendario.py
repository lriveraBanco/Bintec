from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.config.db_calendario import fs
import io
import logging
router = APIRouter()

@router.get("/archivos_calendario", tags=["archivos"])
async def descargar_archivo(archivo_id: int):
    """
    Endpoint para descargar un archivo almacenado en MongoDB.
    
    Parámetros:
    - archivo_id: ID único del archivo almacenado en la base de datos.
    """
    try:
        # Buscar el archivo en MongoDB usando su ID
        archivo = fs.get(archivo_id)

        if not archivo:
            raise HTTPException(status_code=404, detail="Archivo no encontrado.")

        # Crear un stream del contenido del archivo
        contenido_archivo = io.BytesIO(archivo.read())

        # Retornar el archivo como una respuesta de streaming
        return StreamingResponse(contenido_archivo, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": f"attachment; filename={archivo.filename}"})

    except Exception as e:
        # Log del error
        logging.error(f"Error al descargar el archivo: {str(e)}")
        raise HTTPException(status_code=500, detail="Error al intentar descargar el archivo.")
