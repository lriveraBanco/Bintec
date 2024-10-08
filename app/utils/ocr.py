import cv2
import easyocr
import pandas as pd
from pdf2image import convert_from_path
import numpy as np
import os


def procesar_imagenes_calendario(ruta_base):
    # Cargar la imagen del calendario
    ruta_calendario = ruta_base + r"\CALENDARIO-TRIBUTARIO-2024.png"
    imagen_calendario = cv2.imread(ruta_calendario)

    # Recortar y procesar las tablas
    tabla1 = imagen_calendario[55:650, 100:600]
    tabla2 = imagen_calendario[250:550, 600:1500]

    # Guardar las imágenes recortadas
    cv2.imwrite(ruta_base + r"\tabla1.png", tabla1)
    cv2.imwrite(ruta_base + r"\tabla2.png", tabla2)

    # OCR para cada tabla
    reader = easyocr.Reader(['es'])
    resultado_tabla1 = reader.readtext(ruta_base + r"\tabla1.png")
    resultado_tabla2 = reader.readtext(ruta_base + r"\tabla2.png")

    # Extraer texto
    texto_tabla1 = [text for _, text, _ in resultado_tabla1]
    texto_tabla2 = [text for _, text, _ in resultado_tabla2]

    # Procesar tablas y devolver DataFrames
    retencion_data = [["ENERO", "FEBRERO", "14 DE MARZO"]]  # Ejemplo de datos
    impuesto_data = [["ENERO - FEBRERO", "29 DE FEBRERO", "10%"]]  # Ejemplo de datos
    informacion_exogena_data_calendario = [["HASTA EL 30 DE ABRIL DE 2024"]]  # Ejemplo

    df_retencion = pd.DataFrame(retencion_data, columns=["Mes 1", "Mes 2", "Fecha de Pago"])
    df_impuesto = pd.DataFrame(impuesto_data, columns=["Periodo", "Fecha Límite", "Descuento"])
    df_informacion_exogena_calendario = pd.DataFrame(informacion_exogena_data_calendario, columns=["Información Exógena Calendario"])

    return df_retencion, df_impuesto, df_informacion_exogena_calendario

def procesar_pdf_exogena(ruta_base: str):
    """
    Procesa el PDF de exógena convirtiéndolo en imágenes y extrayendo el texto con OCR.
    Devuelve tres DataFrames con información extraída.
    """
    ruta_pdf_exogena = os.path.join(ruta_base, "Resolucion-202350104714-Exogena.pdf")

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

