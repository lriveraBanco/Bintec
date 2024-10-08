import pandas as pd
from app.utils.ocr import procesar_imagenes_calendario
from app.utils.exogena_processing import procesar_pdf_exogena
import os
import numpy as np
import datetime
def procesar_exogena(municipio: str) -> str:
    """
    Función principal que procesa las imágenes del calendario tributario y el PDF de exógena,
    generando un archivo Excel con los resultados.
    Acepta el nombre del municipio como parámetro.
    """
    
    # Configura la ruta base según el municipio
    ruta_base = os.path.join(os.getcwd(), f'data/municipios/{municipio}/calendario')
    
    # Procesar el calendario tributario
    df_retencion, df_impuesto, df_informacion_exogena_calendario = procesar_imagenes_calendario(ruta_base)

    # Procesar el PDF de exógena
    df_informacion_exogena, df_fechas, df_magneticos = procesar_pdf_exogena(ruta_base)
    
    fecha_actual = datetime.datetime.now().strftime("%Y-%m-%d")
    nombre_archivo = f"Calendario_Tributario_Exogena_{municipio}_{fecha_actual}.xlsx"
    ruta_guardar_excel = os.path.join(ruta_base, nombre_archivo)
    # Guardar los resultados en un archivo Excel
    ruta_guardar_excel = os.path.join(ruta_base, 'Calendario_Tributario_Exogena.xlsx')
    with pd.ExcelWriter(ruta_guardar_excel, engine="xlsxwriter") as writer:
        # Hoja del Calendario Tributario
        df_retencion.to_excel(writer, sheet_name="Calendario Tributario", index=False)
        df_impuesto.to_excel(writer, sheet_name="Calendario Tributario", startrow=len(df_retencion)+2, index=False)
        df_informacion_exogena_calendario.to_excel(writer, sheet_name="Calendario Tributario", startrow=len(df_retencion)+len(df_impuesto)+4, index=False)
        
        # Hoja de Información Exógena
        df_informacion_exogena.to_excel(writer, sheet_name="Información Exógena", index=False)
        df_fechas.to_excel(writer, sheet_name="Información Exógena", startrow=len(df_informacion_exogena)+2, index=False)
        df_magneticos.to_excel(writer, sheet_name="Información Exógena", startrow=len(df_informacion_exogena)+len(df_fechas)+4, index=False)

    return ruta_guardar_excel