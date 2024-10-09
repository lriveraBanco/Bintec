from fastapi import APIRouter, HTTPException, status, Form
from app.services.exogena_service import procesar_exogena
from typing import Dict
from fastapi.responses import FileResponse 
import os
router = APIRouter()

@router.post("/procesar-exogena/", tags=["exogena"])
async def procesar_exogena_endpoint(municipio: str = Form(...)):
    """
    Endpoint para procesar el archivo exógena y generar un archivo Excel.
    Recibe el nombre del municipio como un formulario.
    """
    try:
        ruta_excel = procesar_exogena(municipio)
        return FileResponse(ruta_excel, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', filename=os.path.basename(ruta_excel))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al procesar el archivo: {str(e)}")
              