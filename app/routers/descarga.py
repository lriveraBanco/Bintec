from fastapi import APIRouter, HTTPException, Response, status
from fastapi.responses import FileResponse
from bson.objectid import ObjectId
import gridfs
from app.config.db_archivos import *
import os


router = APIRouter()
@router.get("/descargar-excel/{file_id}", tags=["exogena"])
async def descargar_excel_por_id(file_id: int):
    try:
        # Buscar el archivo en la base de datos usando el campo 'id'
        file_data = fs.find_one({"id": file_id})
        if file_data is None:
            raise HTTPException(status_code=404, detail=f"Archivo con id {file_id} no encontrado")
        # Leer el archivo desde GridFS usando el ObjectId directamente de file_data
        contenido = file_data.read()
        # Devolver el archivo como respuesta
        return Response(
            content=contenido,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={file_data.filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar la descarga del archivo: {str(e)}")