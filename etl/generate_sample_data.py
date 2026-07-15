#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_sample_data.py
Genera datos crudos de ejemplo para el caso empresarial de Logística Inteligente del Pacífico S.A.
Incluye problemas de calidad reales: duplicados, IDs inconsistentes, fechas heterogéneas,
unidades de medida variadas y valores faltantes.
"""

import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import os

random.seed(42)
np.random.seed(42)

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "raw")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Parámetros de la simulación
# ---------------------------------------------------------------------------
CLIENTES = [f"CLI-{1000 + i}" for i in range(50)]
REGIONES = ["Costa", "Sierra", "Oriente", "Insular"]
VENDEDORES = [f"VEND-{10 + i}" for i in range(8)]
VEHICULOS = [f"VH-{100 + i}" for i in range(25)]
TIPOS_VEHICULO = ["Camión ligero", "Camión pesado", "Furgoneta", "Tráiler"]
PRODUCTOS = ["Electrodomésticos", "Textiles", "Alimentos", "Químicos", "Materiales de construcción"]
UNIDADES = ["kg", "ton", "lb", "cajas", "pallets"]
MESES = pd.date_range("2025-01-01", "2025-06-25", freq="D")

# ---------------------------------------------------------------------------
# 1. ERP Financiero
# ---------------------------------------------------------------------------
print("Generando ERP financiero...")
n_erp = 1200
facturas = []
for i in range(n_erp):
    cliente = random.choice(CLIENTES)
    region = random.choice(REGIONES)
    fecha = random.choice(MESES)
    # Monto en USD, algunos negativos por notas de crédito
    monto = round(random.uniform(500, 15000), 2)
    if random.random() < 0.05:
        monto = -round(random.uniform(200, 2000), 2)
    costo_logistico = round(abs(monto) * random.uniform(0.08, 0.25), 2)
    facturas.append({
        "id_factura": f"FAC-{20250000 + i}",
        "cliente_id": cliente,
        "region": region,
        "fecha_emision": fecha.strftime("%d/%m/%Y"),
        "monto_usd": monto,
        "costo_logistico_usd": costo_logistico,
        "estado_pago": random.choice(["Pagado", "Pendiente", "Vencido", None]),
        "vendedor_id": random.choice(VENDEDORES),
    })

erp = pd.DataFrame(facturas)
# Introducir duplicados aleatorios
dup_rows = erp.sample(n=25, random_state=7)
erp = pd.concat([erp, dup_rows], ignore_index=True)
# IDs de cliente inconsistentes en algunos registros
def alterar_id(x):
    if random.random() < 0.04:
        return x.replace("CLI-", "cliente_")
    if random.random() < 0.03:
        return x.replace("CLI-", "C-")
    return x

erp["cliente_id"] = erp["cliente_id"].apply(alterar_id)
erp.to_csv(os.path.join(OUTPUT_DIR, "erp_financiero.csv"), index=False, encoding="utf-8-sig")

# ---------------------------------------------------------------------------
# 2. Sistema GPS de vehículos
# ---------------------------------------------------------------------------
print("Generando GPS vehículos...")
n_gps = 1500
gps_records = []
for i in range(n_gps):
    vehiculo = random.choice(VEHICULOS)
    tipo = random.choice(TIPOS_VEHICULO)
    fecha = random.choice(MESES)
    hora_salida = fecha + timedelta(hours=random.randint(6, 14), minutes=random.randint(0, 59))
    duracion_horas = random.uniform(2, 48)
    hora_llegada = hora_salida + timedelta(hours=duracion_horas)
    distancia_km = round(duracion_horas * random.uniform(30, 70), 2)
    # Entregas asociadas
    entregas = random.randint(1, 6)
    gps_records.append({
        "id_viaje": f"VIAJE-{5000 + i}",
        "vehiculo_id": vehiculo,
        "tipo_vehiculo": tipo,
        "fecha": fecha.strftime("%Y-%m-%d"),
        "hora_salida": hora_salida.strftime("%H:%M:%S"),
        "hora_llegada_real": hora_llegada.strftime("%H:%M:%S"),
        "hora_llegada_estimada": (hora_salida + timedelta(hours=duracion_horas * random.uniform(0.85, 1.15))).strftime("%H:%M:%S"),
        "distancia_km": distancia_km,
        "numero_entregas": entregas,
        "combustible_litros": round(distancia_km * random.uniform(0.25, 0.45), 2),
        "estado_viaje": random.choice(["Completado", "Completado", "Completado", "Retrasado", "Cancelado"]),
    })

gps = pd.DataFrame(gps_records)
# Duplicados
gps = pd.concat([gps, gps.sample(n=20, random_state=9)], ignore_index=True)
gps.to_csv(os.path.join(OUTPUT_DIR, "gps_vehiculos.csv"), index=False, encoding="utf-8-sig")

# ---------------------------------------------------------------------------
# 3. Sistema de almacenes
# ---------------------------------------------------------------------------
print("Generando almacenes...")
n_alm = 1000
almacen_records = []
for i in range(n_alm):
    cliente = random.choice(CLIENTES)
    producto = random.choice(PRODUCTOS)
    cantidad = random.randint(10, 500)
    unidad = random.choice(UNIDADES)
    fecha_despacho = random.choice(MESES) + timedelta(days=random.randint(0, 5))
    almacen_records.append({
        "id_despacho": f"DES-{8000 + i}",
        "cliente_id": cliente,
        "producto": producto,
        "cantidad": cantidad,
        "unidad_medida": unidad,
        "fecha_despacho": fecha_despacho.strftime("%d-%b-%Y"),
        "bodega_origen": random.choice(["BOD-01", "BOD-02", "BOD-03", "BOD-04"]),
        "peso_bruto": round(cantidad * random.uniform(0.5, 25), 2),
        "peso_unidad": random.choice(["kg", "lb"]),  # unidad inconsistente respecto a cantidad
    })

almacen = pd.DataFrame(almacen_records)
# IDs inconsistentes
almacen["cliente_id"] = almacen["cliente_id"].apply(alterar_id)
# Faltantes
almacen.loc[almacen.sample(frac=0.05, random_state=11).index, "peso_bruto"] = np.nan
almacen.to_csv(os.path.join(OUTPUT_DIR, "almacenes.csv"), index=False, encoding="utf-8-sig")

# ---------------------------------------------------------------------------
# 4. CRM Comercial
# ---------------------------------------------------------------------------
print("Generando CRM comercial...")
crm_records = []
for cliente in CLIENTES:
    crm_records.append({
        "id_cliente_crm": cliente,
        "nombre_cliente": f"Empresa Industrial {cliente.replace('CLI-', '')}",
        "sector": random.choice(["Manufactura", "Retail", "Construcción", "Agroindustria", "Químico"]),
        "region_comercial": random.choice(REGIONES),
        "satisfaccion_nps": random.choice([None] + list(range(0, 11))),
        "fecha_ultima_encuesta": random.choice(MESES).strftime("%Y/%m/%d"),
        "ejecutivo_cuenta": random.choice(VENDEDORES),
        "estado_cliente": random.choice(["Activo", "Activo", "Activo", "Inactivo", "Prospecto"]),
    })

crm = pd.DataFrame(crm_records)
# Variantes de ID para CRM
crm["id_cliente_crm"] = crm["id_cliente_crm"].apply(alterar_id)
# Duplicados parciales
crm_dup = crm.sample(n=5, random_state=13).copy()
crm = pd.concat([crm, crm_dup], ignore_index=True)
crm.to_csv(os.path.join(OUTPUT_DIR, "crm_comercial.csv"), index=False, encoding="utf-8-sig")

print(f"Datos crudos generados en: {OUTPUT_DIR}")
print("Archivos creados:")
for f in os.listdir(OUTPUT_DIR):
    print(f" - {f}")
