# chilecompra-etl
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

