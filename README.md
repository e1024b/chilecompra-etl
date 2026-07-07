# ChileCompra ETL — Licitaciones del Sector Salud

Script en Python que extrae licitaciones públicas del sector salud desde
la API de Mercado Público, las limpia y transforma, y detecta montos
estimados atípicos por región mediante análisis estadístico (IQR).

## Problema que resuelve
Automatiza la extracción manual de licitaciones que hoy se procesa en
Power BI/Excel, agregando una capa de auditoría de precios.

## Tecnologías
Python · pandas · numpy · requests · SQLite

## Configuración
1. `pip install -r requirements.txt`
2. Obtener un ticket gratuito de acceso en mercadopublico.cl/APIS
3. Reemplazar TICKET_API en el script con el ticket obtenido

## Ejecución
python chilecompra_etl.py

## Resultado
Genera una base de datos SQLite (`chilecompra_salud.db`) con todas las
licitaciones procesadas, y un archivo CSV (`licitaciones_anomalas.csv`)
con las licitaciones marcadas como anómalas.
