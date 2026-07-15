import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(
    page_title="Dashboard Ejecutivo - Logística Inteligente del Pacífico",
    page_icon="🚛",
    layout="wide",
)

DB_PATH = Path(__file__).parent.parent / "database" / "logistica_dw.sqlite"

@st.cache_data(ttl=3600)
def load_data():
    conn = sqlite3.connect(DB_PATH)
    kpis = pd.read_sql_query("SELECT * FROM kpis_mensuales", conn)
    satisfaccion = pd.read_sql_query("SELECT * FROM kpis_satisfaccion", conn)
    financiero = pd.read_sql_query("SELECT * FROM fact_financiero", conn)
    logistico = pd.read_sql_query("SELECT * FROM fact_logistico", conn)
    clientes = pd.read_sql_query("SELECT * FROM dim_clientes", conn)
    conn.close()
    return kpis, satisfaccion, financiero, logistico, clientes

kpis, satisfaccion, financiero, logistico, clientes = load_data()

# Título
st.title("🚛 Logística Inteligente del Pacífico S.A.")
st.subheader("Dashboard Ejecutivo de Operaciones y Finanzas")

# Métricas principales
col1, col2, col3, col4, col5 = st.columns(5)

total_ingresos = financiero["monto_usd"].sum()
total_entregas = logistico["numero_entregas"].sum()
cumplimiento = (logistico["cumplimiento"] == "A tiempo").mean() * 100
tiempo_prom = logistico["tiempo_entrega_horas"].mean()
costo_total = financiero["costo_logistico_usd"].sum() + logistico["costo_combustible_usd"].sum()

with col1:
    st.metric("Ingresos Totales", f"${total_ingresos:,.0f}")
with col2:
    st.metric("Entregas Totales", f"{total_entregas:,.0f}")
with col3:
    st.metric("Cumplimiento", f"{cumplimiento:.1f}%")
with col4:
    st.metric("Tiempo Prom. Entrega", f"{tiempo_prom:.1f} h")
with col5:
    st.metric("Costos Logísticos", f"${costo_total:,.0f}")

st.divider()

# Gráficos
left, right = st.columns(2)

with left:
    st.markdown("### Tendencia Mensual de Ingresos")
    fig_ing = px.bar(
        kpis.dropna(subset=["ingresos_total"]),
        x="mes",
        y="ingresos_total",
        color="ingresos_total",
        color_continuous_scale="Blues",
        labels={"ingresos_total": "Ingresos (USD)", "mes": "Mes"},
    )
    st.plotly_chart(fig_ing, use_container_width=True)

with right:
    st.markdown("### Tendencia Mensual de Entregas")
    fig_ent = px.line(
        kpis,
        x="mes",
        y="entregas_totales",
        markers=True,
        labels={"entregas_totales": "Entregas", "mes": "Mes"},
    )
    st.plotly_chart(fig_ent, use_container_width=True)

left2, right2 = st.columns(2)

with left2:
    st.markdown("### Cumplimiento de Entregas por Mes")
    fig_cum = px.bar(
        kpis,
        x="mes",
        y="cumplimiento_pct",
        color="cumplimiento_pct",
        color_continuous_scale="RdYlGn",
        range_color=[0, 100],
        labels={"cumplimiento_pct": "% Cumplimiento", "mes": "Mes"},
    )
    st.plotly_chart(fig_cum, use_container_width=True)

with right2:
    st.markdown("### Distribución de Satisfacción (NPS)")
    fig_sat = px.pie(
        satisfaccion,
        names="categoria_nps",
        values="cantidad",
        color="categoria_nps",
        color_discrete_map={
            "Promotor": "#2ecc71",
            "Neutro": "#f1c40f",
            "Detractor": "#e74c3c",
            "Sin datos": "#95a5a6",
        },
    )
    st.plotly_chart(fig_sat, use_container_width=True)

left3, right3 = st.columns(2)

with left3:
    st.markdown("### Costos Logísticos Mensuales")
    kpis["costos_logisticos_totales"] = kpis["costo_logistico_total"] + kpis["costo_combustible_total"]
    fig_cost = px.area(
        kpis,
        x="mes",
        y="costos_logisticos_totales",
        labels={"costos_logisticos_totales": "Costos Logísticos (USD)", "mes": "Mes"},
    )
    st.plotly_chart(fig_cost, use_container_width=True)

with right3:
    st.markdown("### Tiempo Promedio de Entrega por Mes")
    fig_tiempo = px.bar(
        kpis,
        x="mes",
        y="tiempo_promedio_entrega",
        color="tiempo_promedio_entrega",
        color_continuous_scale="Oranges",
        labels={"tiempo_promedio_entrega": "Horas", "mes": "Mes"},
    )
    st.plotly_chart(fig_tiempo, use_container_width=True)

# Segmentación por regiones
st.markdown("### Ingresos por Región")
ingresos_region = financiero.groupby("region")["monto_usd"].sum().reset_index().sort_values("monto_usd", ascending=False)
fig_region = px.bar(
    ingresos_region,
    x="region",
    y="monto_usd",
    color="region",
    labels={"monto_usd": "Ingresos (USD)", "region": "Región"},
)
st.plotly_chart(fig_region, use_container_width=True)

# Tabla de clientes
st.markdown("### Top 10 Clientes por Ingresos")
top_clientes = clientes.nlargest(10, "ingresos_total")[["cliente_id", "nombre_cliente", "sector", "region_comercial", "ingresos_total", "categoria_nps"]]
st.dataframe(top_clientes, use_container_width=True)

st.divider()
st.caption("Fuente: Data Warehouse SQLite generado por el proceso ETL automatizado.")
