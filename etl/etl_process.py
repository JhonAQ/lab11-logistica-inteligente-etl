#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
etl_process.py
Proceso ETL completo para Logística Inteligente del Pacífico S.A.
Extrae datos de 4 fuentes heterogéneas, los limpia, transforma e integra
y los carga en un Data Warehouse SQLite.
"""

import pandas as pd
import numpy as np
import os
import re
import sqlite3
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
DB_DIR = os.path.join(BASE_DIR, "database")
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(DB_DIR, exist_ok=True)

DB_PATH = os.path.join(DB_DIR, "logistica_dw.sqlite")

# ---------------------------------------------------------------------------
# Funciones auxiliares
# ---------------------------------------------------------------------------

def homologar_cliente_id(val):
    """Convierte cualquier variante de ID de cliente a CLI-XXXX."""
    if pd.isna(val):
        return None
    val = str(val).strip().upper()
    m = re.search(r"(\d{4,})", val)
    if m:
        return f"CLI-{int(m.group(1)):04d}"
    return val


def parse_fecha(val):
    """Parsea fechas en múltiples formatos."""
    if pd.isna(val):
        return pd.NaT
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%m/%d/%Y", "%d-%b-%Y", "%Y/%m/%d"):
        try:
            return pd.to_datetime(val, format=fmt)
        except Exception:
            continue
    try:
        return pd.to_datetime(val, dayfirst=True)
    except Exception:
        return pd.NaT


def calcular_horas(salida, llegada):
    """Calcula horas entre dos cadenas de tiempo HH:MM:SS."""
    try:
        fmt = "%H:%M:%S"
        s = datetime.strptime(str(salida), fmt)
        l = datetime.strptime(str(llegada), fmt)
        diff = (l - s).total_seconds() / 3600
        if diff < 0:
            diff += 24
        return round(diff, 2)
    except Exception:
        return np.nan


def nps_categoria(nps):
    """Clasifica puntaje NPS en Promotor / Neutro / Detractor."""
    if pd.isna(nps):
        return "Sin datos"
    nps = int(nps)
    if nps >= 9:
        return "Promotor"
    elif nps >= 7:
        return "Neutro"
    else:
        return "Detractor"


def normalizar_unidades(row):
    """Normaliza peso a kilogramos y crea unidad base."""
    cantidad = row["cantidad"]
    unidad = str(row["unidad_medida"]).lower().strip()
    peso_bruto = row["peso_bruto"]
    peso_unidad = str(row["peso_unidad"]).lower().strip() if pd.notna(row["peso_unidad"]) else "kg"

    factor = 1.0
    if unidad == "ton":
        factor = 1000.0
    elif unidad == "lb":
        factor = 0.453592
    elif unidad == "cajas":
        factor = 12.0
    elif unidad == "pallets":
        factor = 500.0

    cantidad_kg = cantidad * factor

    if pd.isna(peso_bruto):
        peso_bruto_kg = cantidad_kg
    else:
        peso_bruto_kg = peso_bruto * 0.453592 if peso_unidad == "lb" else peso_bruto

    return pd.Series({
        "cantidad_kg": round(cantidad_kg, 2),
        "peso_bruto_kg": round(peso_bruto_kg, 2),
        "unidad_base": "kg",
    })


# ---------------------------------------------------------------------------
# EXTRACCIÓN
# ---------------------------------------------------------------------------
logger.info("Extrayendo datos de fuentes crudas...")

erp = pd.read_csv(os.path.join(RAW_DIR, "erp_financiero.csv"))
gps = pd.read_csv(os.path.join(RAW_DIR, "gps_vehiculos.csv"))
almacen = pd.read_csv(os.path.join(RAW_DIR, "almacenes.csv"))
crm = pd.read_csv(os.path.join(RAW_DIR, "crm_comercial.csv"))

logger.info(f"  ERP: {len(erp)} registros")
logger.info(f"  GPS: {len(gps)} registros")
logger.info(f"  Almacén: {len(almacen)} registros")
logger.info(f"  CRM: {len(crm)} registros")

# ---------------------------------------------------------------------------
# LIMPIEZA Y TRANSFORMACIÓN
# ---------------------------------------------------------------------------
logger.info("Iniciando limpieza y transformación...")

# --- ERP Financiero ---
erp_clean = erp.copy()
erp_clean["cliente_id_original"] = erp_clean["cliente_id"]
erp_clean["cliente_id"] = erp_clean["cliente_id"].apply(homologar_cliente_id)
erp_clean["fecha_emision"] = erp_clean["fecha_emision"].apply(parse_fecha)
erp_clean["mes"] = erp_clean["fecha_emision"].dt.to_period("M").astype(str)
n_dup_erp = erp_clean.duplicated().sum()
erp_clean = erp_clean.drop_duplicates()
logger.info(f"  ERP: {n_dup_erp} duplicados eliminados")
erp_clean["estado_pago"] = erp_clean["estado_pago"].fillna("Pendiente")

# --- GPS Vehículos ---
gps_clean = gps.copy()
gps_clean["fecha"] = gps_clean["fecha"].apply(parse_fecha)
gps_clean["mes"] = gps_clean["fecha"].dt.to_period("M").astype(str)
n_dup_gps = gps_clean.duplicated().sum()
gps_clean = gps_clean.drop_duplicates()
logger.info(f"  GPS: {n_dup_gps} duplicados eliminados")

gps_clean["tiempo_entrega_horas"] = gps_clean.apply(
    lambda r: calcular_horas(r["hora_salida"], r["hora_llegada_real"]), axis=1
)
gps_clean["tiempo_estimado_horas"] = gps_clean.apply(
    lambda r: calcular_horas(r["hora_salida"], r["hora_llegada_estimada"]), axis=1
)
gps_clean["diferencia_tiempo_horas"] = gps_clean["tiempo_entrega_horas"] - gps_clean["tiempo_estimado_horas"]
gps_clean["cumplimiento"] = np.where(gps_clean["diferencia_tiempo_horas"] <= 0, "A tiempo", "Retrasado")
gps_clean["costo_combustible_usd"] = (gps_clean["combustible_litros"] * 0.85).round(2)

# --- Almacenes ---
almacen_clean = almacen.copy()
almacen_clean["cliente_id_original"] = almacen_clean["cliente_id"]
almacen_clean["cliente_id"] = almacen_clean["cliente_id"].apply(homologar_cliente_id)
almacen_clean["fecha_despacho"] = almacen_clean["fecha_despacho"].apply(parse_fecha)
almacen_clean["mes"] = almacen_clean["fecha_despacho"].dt.to_period("M").astype(str)
n_dup_alm = almacen_clean.duplicated().sum()
almacen_clean = almacen_clean.drop_duplicates()
logger.info(f"  Almacén: {n_dup_alm} duplicados eliminados")

units_df = almacen_clean.apply(normalizar_unidades, axis=1)
almacen_clean = pd.concat([almacen_clean, units_df], axis=1)

# --- CRM ---
crm_clean = crm.copy()
crm_clean["id_cliente_crm_original"] = crm_clean["id_cliente_crm"]
crm_clean["id_cliente_crm"] = crm_clean["id_cliente_crm"].apply(homologar_cliente_id)
crm_clean["fecha_ultima_encuesta"] = crm_clean["fecha_ultima_encuesta"].apply(parse_fecha)
n_dup_crm = crm_clean.duplicated(subset=["id_cliente_crm"]).sum()
crm_clean = crm_clean.drop_duplicates(subset=["id_cliente_crm"], keep="first")
logger.info(f"  CRM: {n_dup_crm} duplicados de cliente eliminados")
crm_clean["categoria_nps"] = crm_clean["satisfaccion_nps"].apply(nps_categoria)

# ---------------------------------------------------------------------------
# INTEGRACIÓN: Tabla maestra de clientes
# ---------------------------------------------------------------------------
logger.info("Integrando tablas en modelo dimensional...")

erp_ingresos = (
    erp_clean.groupby("cliente_id")["monto_usd"]
    .sum()
    .reset_index()
    .rename(columns={"cliente_id": "id_cliente_crm", "monto_usd": "ingresos_total"})
)

clientes = pd.merge(
    crm_clean[["id_cliente_crm", "nombre_cliente", "sector", "region_comercial",
               "satisfaccion_nps", "categoria_nps", "ejecutivo_cuenta", "estado_cliente"]],
    erp_ingresos,
    on="id_cliente_crm", how="outer"
)
clientes["ingresos_total"] = clientes["ingresos_total"].fillna(0)
clientes["estado_cliente"] = clientes["estado_cliente"].fillna("Desconocido")
clientes = clientes.rename(columns={"id_cliente_crm": "cliente_id"})

# ---------------------------------------------------------------------------
# TABLAS DE HECHOS
# ---------------------------------------------------------------------------
hechos_financieros = erp_clean[[
    "id_factura", "cliente_id", "region", "fecha_emision", "mes",
    "monto_usd", "costo_logistico_usd", "estado_pago", "vendedor_id"
]].copy()

hechos_logisticos = gps_clean[[
    "id_viaje", "vehiculo_id", "tipo_vehiculo", "fecha", "mes",
    "hora_salida", "hora_llegada_real", "hora_llegada_estimada",
    "distancia_km", "numero_entregas", "combustible_litros",
    "estado_viaje", "tiempo_entrega_horas", "tiempo_estimado_horas",
    "diferencia_tiempo_horas", "cumplimiento", "costo_combustible_usd"
]].copy()

hechos_almacen = almacen_clean[[
    "id_despacho", "cliente_id", "producto", "cantidad", "unidad_medida",
    "fecha_despacho", "mes", "bodega_origen", "cantidad_kg", "peso_bruto_kg", "unidad_base"
]].copy()

# ---------------------------------------------------------------------------
# CÁLCULO DE KPIs AGREGADOS
# ---------------------------------------------------------------------------
logger.info("Calculando KPIs agregados...")

kpis_mensuales = hechos_financieros.groupby("mes").agg(
    ingresos_total=("monto_usd", "sum"),
    costo_logistico_total=("costo_logistico_usd", "sum"),
    facturas_emitidas=("id_factura", "count"),
).reset_index()

log_kpis = hechos_logisticos.groupby("mes").agg(
    entregas_totales=("numero_entregas", "sum"),
    viajes_totales=("id_viaje", "count"),
    distancia_total_km=("distancia_km", "sum"),
    tiempo_promedio_entrega=("tiempo_entrega_horas", "mean"),
    combustible_total_litros=("combustible_litros", "sum"),
    costo_combustible_total=("costo_combustible_usd", "sum"),
    entregas_a_tiempo=("cumplimiento", lambda x: (x == "A tiempo").sum()),
).reset_index()
log_kpis["cumplimiento_pct"] = (log_kpis["entregas_a_tiempo"] / log_kpis["viajes_totales"] * 100).round(2)

kpis_mensuales = pd.merge(kpis_mensuales, log_kpis, on="mes", how="outer")

satisfaccion = crm_clean.groupby("categoria_nps").size().reset_index(name="cantidad")
satisfaccion_total = satisfaccion["cantidad"].sum()
satisfaccion["pct"] = (satisfaccion["cantidad"] / satisfaccion_total * 100).round(2)

# ---------------------------------------------------------------------------
# CARGA EN DATA WAREHOUSE SQLITE
# ---------------------------------------------------------------------------
logger.info(f"Cargando Data Warehouse en {DB_PATH}...")

conn = sqlite3.connect(DB_PATH)

clientes.to_sql("dim_clientes", conn, if_exists="replace", index=False)
hechos_financieros.to_sql("fact_financiero", conn, if_exists="replace", index=False)
hechos_logisticos.to_sql("fact_logistico", conn, if_exists="replace", index=False)
hechos_almacen.to_sql("fact_almacen", conn, if_exists="replace", index=False)
kpis_mensuales.to_sql("kpis_mensuales", conn, if_exists="replace", index=False)
satisfaccion.to_sql("kpis_satisfaccion", conn, if_exists="replace", index=False)

conn.execute("""
CREATE VIEW IF NOT EXISTS v_dashboard AS
SELECT
    f.mes,
    SUM(f.ingresos_total) AS ingresos_total,
    SUM(f.costo_logistico_total) AS costo_logistico_total,
    SUM(f.facturas_emitidas) AS facturas_emitidas,
    SUM(f.entregas_totales) AS entregas_totales,
    SUM(f.viajes_totales) AS viajes_totales,
    AVG(f.tiempo_promedio_entrega) AS tiempo_promedio_entrega,
    SUM(f.costo_combustible_total) AS costo_combustible_total,
    AVG(f.cumplimiento_pct) AS cumplimiento_pct
FROM kpis_mensuales f
GROUP BY f.mes;
""")

conn.commit()
conn.close()

# ---------------------------------------------------------------------------
# EXPORTACIÓN ADICIONAL A CSV Y EXCEL
# ---------------------------------------------------------------------------
logger.info("Exportando archivos procesados...")

clientes.to_csv(os.path.join(PROCESSED_DIR, "dim_clientes.csv"), index=False, encoding="utf-8-sig")
hechos_financieros.to_csv(os.path.join(PROCESSED_DIR, "fact_financiero.csv"), index=False, encoding="utf-8-sig")
hechos_logisticos.to_csv(os.path.join(PROCESSED_DIR, "fact_logistico.csv"), index=False, encoding="utf-8-sig")
hechos_almacen.to_csv(os.path.join(PROCESSED_DIR, "fact_almacen.csv"), index=False, encoding="utf-8-sig")
kpis_mensuales.to_csv(os.path.join(PROCESSED_DIR, "kpis_mensuales.csv"), index=False, encoding="utf-8-sig")
satisfaccion.to_csv(os.path.join(PROCESSED_DIR, "kpis_satisfaccion.csv"), index=False, encoding="utf-8-sig")

with pd.ExcelWriter(os.path.join(PROCESSED_DIR, "datos_procesados.xlsx"), engine="openpyxl") as writer:
    clientes.to_excel(writer, sheet_name="Clientes", index=False)
    hechos_financieros.to_excel(writer, sheet_name="Financiero", index=False)
    hechos_logisticos.to_excel(writer, sheet_name="Logistico", index=False)
    hechos_almacen.to_excel(writer, sheet_name="Almacen", index=False)
    kpis_mensuales.to_excel(writer, sheet_name="KPIs_Mensuales", index=False)
    satisfaccion.to_excel(writer, sheet_name="Satisfaccion", index=False)

logger.info("ETL completado exitosamente.")
logger.info(f"Base de datos: {DB_PATH}")
logger.info(f"Resumen KPIs mensuales:\n{kpis_mensuales.to_string(index=False)}")
