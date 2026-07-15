#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_all.py
Ejecuta todo el pipeline del proyecto:
1. Genera datos de ejemplo
2. Ejecuta el ETL
3. Genera el informe tecnico en Word
"""

import subprocess
import sys
import os

scripts = [
    "etl/generate_sample_data.py",
    "etl/etl_process.py",
    "docs/generate_report.py",
]

for script in scripts:
    print(f"\n{'='*60}")
    print(f"Ejecutando: {script}")
    print('='*60)
    result = subprocess.run([sys.executable, script], cwd=os.path.dirname(os.path.abspath(__file__)))
    if result.returncode != 0:
        print(f"ERROR al ejecutar {script}")
        sys.exit(result.returncode)

print("\n" + "="*60)
print("Proyecto generado exitosamente.")
print("="*60)
print("\nEntregables principales:")
print("  - Base de datos: database/logistica_dw.sqlite")
print("  - Datos procesados: data/processed/datos_procesados.xlsx")
print("  - Dashboard Power BI: dashboard/dashboard_ejecutivo.pbix")
print("  - Informe tecnico: docs/Informe_Tecnico_ETL.docx")
print("  - Informe tecnico Markdown: docs/Informe_Tecnico_ETL.md")
