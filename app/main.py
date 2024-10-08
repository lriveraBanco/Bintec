from fastapi import FastAPI
from app.routers.municipio_router import router
from app.routers.user import user

from app.routers.exogena import router as exogena_router
from app.routers.descarga import router as descarga_router 


app = FastAPI(
    title="API Bintec 2024",
    description="La API automatiza la extracción de información clave de diversos formatos de documentos (PDF, imagen, Word, Excel) relacionados con la normativa fiscal (ICA). Revisa y extrae secciones específicas como artículos y normas, transfiriéndolas a una matriz de Excel para cálculos posteriores sobre tipos y porcentajes necesarios para el cumplimiento del ICA. ",
    version="1.0.0"
)

# Incluir router de municipios
app.include_router(router)
app.include_router(user)

app.include_router(exogena_router)
app.include_router(descarga_router)


@app.get("/",tags=["municipios"])
async def home():
    """
    Welcome message.
    Returns a simple welcome message for the API.
    """
    return {"message": "Bienvenido a la API de Bintec-2024"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)