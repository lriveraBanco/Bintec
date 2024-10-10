from fastapi import APIRouter, HTTPException
from bson import ObjectId
from app.config.db_archivos import fs

router = APIRouter()

@router.get("/archivos", tags=["archivos"])
async def obtener_todos_los_archivos():
    try:
        # Buscar todos los archivos en MongoDB usando GridFS
        archivos = fs.find()

        # Verificar si existen archivos
        lista_archivos = []
        for archivo in archivos:
            # Asegurarse de obtener el tipo de recurso desde los metadatos
            tipo_recurso = archivo.metadata.get("Tipo_recurso") if archivo.metadata else "Desconocido"

            datos_archivo = {
                "nombre_archivo": archivo.filename.replace(".xlsx", ""),  # Eliminar extensión .xlsx
                "codigo": archivo.id,
                "fecha": archivo.uploadDate.strftime("%Y-%m-%d"),
                "municipio": archivo.metadata.get("municipio", "Desconocido") if archivo.metadata else "Desconocido",
                "Tipo_recurso": tipo_recurso
            }
            lista_archivos.append(datos_archivo)

        # Si no se encontraron archivos
        if not lista_archivos:
            raise HTTPException(status_code=404, detail="No se encontraron archivos.")

        return lista_archivos

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

