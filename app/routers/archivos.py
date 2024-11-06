from fastapi import APIRouter, HTTPException
from app.config.db_archivos import fs
from app.routers.municipio_router import cargar_codigos_dane  

router = APIRouter()

@router.get("/archivos", tags=["archivos"])
async def obtener_todos_los_archivos():
    try:
        # Buscar todos los archivos en MongoDB usando GridFS
        archivos = fs.find()

        # Verificar si existen archivos
        lista_archivos = []
        for archivo in archivos:
            # Verificar si 'metadata' es None antes de intentar acceder a sus valores
            metadata = archivo.metadata if archivo.metadata else {}
            
            # Asegurarse de obtener el tipo de recurso desde los metadatos
            tipo_recurso = metadata.get("Tipo_recurso", "Desconocido")
            municipio = metadata.get("municipio", "Desconocido")
            codigo_dane = metadata.get("codigo_dane", None)

            # Si el código DANE no está presente, intentar cargarlo usando la función cargar_codigos_dane
            if not codigo_dane and municipio != "Desconocido":
                try:
                    # Aquí usamos la función `cargar_codigos_dane` para obtener el código DANE del municipio
                    codigo_dane = cargar_codigos_dane(municipio)
                except HTTPException as e:
                    # En caso de error con la carga del código DANE, mantener como "Desconocido"
                    codigo_dane = "Desconocido"
                    print(f"No se pudo cargar el código DANE para el municipio '{municipio}': {e.detail}")

            # Verificar si 'codigo_dane' es un valor válido para convertir a int, si es None se asigna "Desconocido"
            if codigo_dane is not None and codigo_dane != "Desconocido":
                try:
                    codigo_dane = int(codigo_dane)
                except ValueError:
                    codigo_dane = "Desconocido"  # Si no se puede convertir a int, asignar "Desconocido"

            datos_archivo = {
                "nombre_archivo": archivo.filename.replace(".xlsx", ""),  # Eliminar extensión .xlsx
                "codigo": str(archivo._id),  # Usar _id en lugar de id
                "fecha": archivo.uploadDate.strftime("%Y-%m-%d"),
                "municipio": municipio,
                "Tipo_recurso": tipo_recurso,
                "codigo_dane": codigo_dane
            }
            lista_archivos.append(datos_archivo)

        # Si no se encontraron archivos
        if not lista_archivos:
            raise HTTPException(status_code=404, detail="No se encontraron archivos.")

        return lista_archivos

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
