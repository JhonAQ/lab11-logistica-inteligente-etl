# Logística Inteligente del Pacífico S.A. - Proyecto ETL

Este proyecto implementa un proceso ETL completo y automatizado para consolidar información de cuatro sistemas independientes (ERP financiero, GPS, almacenes y CRM) en un Data Warehouse, con el objetivo de alimentar un dashboard ejecutivo.

## Estructura del proyecto

```
lab11/
├── data/
│   ├── raw/                    # Datos crudos de las 4 fuentes
│   └── processed/              # Datos limpios y transformados
├── database/
│   └── logistica_dw.sqlite     # Data Warehouse final
├── dashboard/
│   ├── dashboard_ejecutivo.pbix # Dashboard oficial en Power BI
│   └── app.py                  # Dashboard alternativo en Streamlit
├── diagrams/
│   └── diagrama_etl.md         # Diagrama y documentación del flujo ETL
├── docs/
│   ├── Informe_Tecnico_ETL.docx # Informe técnico de 7 páginas
│   └── generate_report.py
├── etl/
│   ├── generate_sample_data.py # Generador de datos de ejemplo
│   └── etl_process.py          # Proceso ETL completo
└── README.md                   # Este archivo
```

## Requisitos

- Python 3.10 o superior
- Librerías: pandas, numpy, openpyxl, python-docx, plotly

Instalación rápida:

```bash
pip install pandas numpy openpyxl python-docx plotly
```

## Cómo ejecutar

1. Generar datos de ejemplo:

```bash
python etl/generate_sample_data.py
```

2. Ejecutar el proceso ETL:

```bash
python etl/etl_process.py
```

3. Generar el informe técnico:

```bash
python docs/generate_report.py
```

O ejecuta todo de una vez:

```bash
python run_all.py
```

## Entregables

| Producto | Archivo | Descripción |
|----------|---------|-------------|
| Proyecto ETL completo | `etl/etl_process.py` | Script de extracción, transformación y carga |
| Base de datos final | `database/logistica_dw.sqlite` | Data Warehouse en SQLite |
| Dashboard Power BI | `dashboard/dashboard_ejecutivo.pbix` | Dashboard oficial en Power BI Desktop |
| Dashboard alternativo | `dashboard/app.py` | Dashboard ejecutivo en Streamlit |
| Informe técnico | `docs/Informe_Tecnico_ETL.docx` | Informe de 7 páginas |
| Diagrama ETL | `diagrams/diagrama_etl.md` | Arquitectura y flujo detallado |

## Autor

Proyecto académico - Ejercicio Propuesto 2.
