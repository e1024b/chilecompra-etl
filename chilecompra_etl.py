"""
ETL Automatizado - ChileCompra (Mercado Público)
--------------------------------------------------
Extrae licitaciones públicas del sector salud desde la API abierta de
Mercado Público, las limpia, transforma y analiza para detectar
posibles anomalías de precio por proveedor/categoría.

Este script extiende el análisis manual ya publicado en el portafolio
("Manual Funcional de Licitaciones de Salud" y el dashboard de
Power BI de ChileCompra), automatizando la etapa de extracción y
sumando una capa de detección de anomalías que hoy no existe en la
versión Power BI/Excel.

Requisitos:
    pip install requests pandas numpy

API:
    Mercado Público entrega un ticket gratuito de acceso en:
    https://www.mercadopublico.cl/APIS
    Reemplaza TICKET_API por el tuyo antes de ejecutar.

Nota: los nombres exactos de los campos devueltos por la API pueden
variar según la versión del endpoint; revisa la respuesta cruda
(por ejemplo imprimiendo `crudo.columns`) y ajusta la lista
`columnas_utiles` si es necesario.

Autor: Antonio Contreras Riquelme
"""

import sqlite3
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import requests

TICKET_API = "TU_TICKET_AQUI"  # Ticket gratuito de developers.mercadopublico.cl
BASE_URL = "https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json"

# Palabras clave que identifican licitaciones del sector salud
KEYWORDS_SALUD = [
    "salud", "médic", "medic", "farmac", "hospital", "clinic", "clínic",
    "dialisis", "diálisis", "insumo", "sanitari",
]


def obtener_licitaciones(fecha: str) -> list:
    """
    Consulta licitaciones publicadas en una fecha específica
    (formato ddmmyyyy). Devuelve la lista cruda entregada por la API.
    """
    params = {"ticket": TICKET_API, "fecha": fecha}
    respuesta = requests.get(BASE_URL, params=params, timeout=30)
    respuesta.raise_for_status()
    datos = respuesta.json()
    return datos.get("Listado", [])


def extraer_rango_fechas(dias_atras: int = 7) -> pd.DataFrame:
    """
    Recorre los últimos N días y concatena todas las licitaciones
    obtenidas en un único DataFrame.
    """
    registros = []
    hoy = datetime.today()

    for i in range(dias_atras):
        fecha = (hoy - timedelta(days=i)).strftime("%d%m%Y")
        try:
            licitaciones = obtener_licitaciones(fecha)
            registros.extend(licitaciones)
        except requests.RequestException as error:
            print(f"[AVISO] No se pudo obtener datos para {fecha}: {error}")

    return pd.DataFrame(registros)


def filtrar_sector_salud(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filtra únicamente las licitaciones relacionadas al sector salud
    según coincidencia de palabras clave en el nombre de la licitación.
    """
    if df.empty or "Nombre" not in df.columns:
        return df

    patron = "|".join(KEYWORDS_SALUD)
    mascara = df["Nombre"].str.contains(patron, case=False, na=False)
    return df[mascara].copy()


def limpiar_transformar(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza tipos de datos, elimina duplicados y estandariza
    columnas clave para el análisis posterior.
    """
    columnas_utiles = [
        "CodigoExterno", "Nombre", "CodigoEstado", "Organismo",
        "Region", "FechaCierre", "MontoEstimado",
    ]
    df = df[[c for c in columnas_utiles if c in df.columns]].copy()

    if "CodigoExterno" in df.columns:
        df = df.drop_duplicates(subset="CodigoExterno")

    df["MontoEstimado"] = pd.to_numeric(df.get("MontoEstimado"), errors="coerce")
    df["FechaCierre"] = pd.to_datetime(df.get("FechaCierre"), errors="coerce")
    df = df.dropna(subset=["MontoEstimado"])

    return df


def detectar_anomalias_precio(df: pd.DataFrame) -> pd.DataFrame:
    """
    Detecta licitaciones con montos estimados atípicos dentro de su
    región usando el método de rango intercuartílico (IQR).
    Un monto atípico puede indicar sobreprecio, error de digitación
    o una oportunidad de negocio inusual - útil para auditoría.
    """
    if "Region" not in df.columns or df.empty:
        df["Anomalia_Precio"] = False
        return df

    def marcar_outliers(grupo):
        q1 = grupo["MontoEstimado"].quantile(0.25)
        q3 = grupo["MontoEstimado"].quantile(0.75)
        iqr = q3 - q1
        limite_superior = q3 + 1.5 * iqr
        grupo["Anomalia_Precio"] = grupo["MontoEstimado"] > limite_superior
        return grupo

    return df.groupby("Region", group_keys=False).apply(marcar_outliers)


def guardar_resultados(df: pd.DataFrame, ruta_db: str = "chilecompra_salud.db"):
    """
    Persiste los resultados en una base SQLite local y exporta un
    resumen en CSV con las licitaciones marcadas como anómalas.
    """
    conexion = sqlite3.connect(ruta_db)
    df.to_sql("licitaciones_salud", conexion, if_exists="replace", index=False)
    conexion.close()

    anomalias = df[df["Anomalia_Precio"]]
    anomalias.to_csv("licitaciones_anomalas.csv", index=False)

    print(f"Total licitaciones procesadas: {len(df)}")
    print(f"Licitaciones con precio atípico: {len(anomalias)}")
    print(f"Resultados guardados en {ruta_db} y licitaciones_anomalas.csv")


def ejecutar_pipeline(dias_atras: int = 7):
    crudo = extraer_rango_fechas(dias_atras)
    salud = filtrar_sector_salud(crudo)
    limpio = limpiar_transformar(salud)

    if limpio.empty:
        print("No se encontraron licitaciones de salud en el rango solicitado.")
        return

    con_anomalias = detectar_anomalias_precio(limpio)
    guardar_resultados(con_anomalias)


if __name__ == "__main__":
    ejecutar_pipeline(dias_atras=7)

