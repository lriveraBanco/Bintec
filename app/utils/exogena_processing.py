import pandas as pd
from pdf2image import convert_from_path
import easyocr
import numpy as np

def procesar_pdf_exogena(ruta_base):
    ruta_pdf_exogena = ruta_base + r"\Resolucion-202350104714-Exogena.pdf"

    # Convertir PDF a imágenes
    imagenes_exogena = convert_from_path(ruta_pdf_exogena)
    
    reader = easyocr.Reader(['es'])
    texto_exogena = ""
    for img in imagenes_exogena:
        img_np = np.array(img)
        resultados_exogena = reader.readtext(img_np)
        for (_, text, _) in resultados_exogena:
            texto_exogena += text + " "

    # Extraer información clave (ajustar según sea necesario)
    informacion_exogena_data = [["Información Exógena"]]
    fechas_data = [["Información periodo grabable"]]
    magneticos_data = [["Medios Magnéticos"]]

    df_informacion_exogena = pd.DataFrame(informacion_exogena_data, columns=["Información Exógena"])
    df_fechas = pd.DataFrame(fechas_data, columns=["Información periodo grabable"])
    df_magneticos = pd.DataFrame(magneticos_data, columns=["Medios Magnéticos"])

    return df_informacion_exogena, df_fechas, df_magneticos

