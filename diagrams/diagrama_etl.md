# Diagrama del Proceso ETL

## Arquitectura General

```mermaid
flowchart TB
    subgraph Fuentes["Fuentes de Datos"]
        A1[ERP Financiero]
        A2[Sistema GPS]
        A3[Sistema de Almacenes]
        A4[CRM Comercial]
    end

    subgraph Staging["Capa Staging / Extracción"]
        B1[CSV ERP]
        B2[CSV GPS]
        B3[CSV Almacén]
        B4[CSV CRM]
    end

    subgraph Transform["Capa de Transformación"]
        C1[Limpieza de duplicados]
        C2[Homologación de IDs de cliente]
        C3[Normalización de fechas]
        C4[Normalización de unidades a kg]
        C5[Columnas calculadas:<br/>tiempo de entrega, cumplimiento,<br/>costo combustible, categoría NPS]
    end

    subgraph DW["Data Warehouse"]
        D1[dim_clientes]
        D2[fact_financiero]
        D3[fact_logistico]
        D4[fact_almacen]
        D5[kpis_mensuales]
        D6[kpis_satisfaccion]
    end

    subgraph BI["Visualización"]
        E1[Dashboard Ejecutivo Power BI]
    end

    A1 --> B1
    A2 --> B2
    A3 --> B3
    A4 --> B4

    B1 --> C1
    B2 --> C1
    B3 --> C1
    B4 --> C1

    C1 --> C2 --> C3 --> C4 --> C5

    C5 --> D1
    C5 --> D2
    C5 --> D3
    C5 --> D4
    C5 --> D5
    C5 --> D6

    D1 --> E1
    D2 --> E1
    D3 --> E1
    D4 --> E1
    D5 --> E1
    D6 --> E1
```

## Flujo Detallado por Fuente

### 1. ERP Financiero
- **Extrae:** `id_factura`, `cliente_id`, `region`, `fecha_emision`, `monto_usd`, `costo_logistico_usd`, `estado_pago`, `vendedor_id`
- **Problemas detectados:** IDs de cliente inconsistentes (`CLI-`, `cliente_`, `C-`), duplicados exactos, fechas en formato `dd/mm/yyyy`, estados de pago faltantes.
- **Transformaciones:**
  - Homologar `cliente_id` a formato `CLI-XXXX`
  - Parsear fechas a formato ISO
  - Eliminar duplicados exactos
  - Imputar estados de pago faltantes como "Pendiente"
  - Crear columna `mes`
- **Carga:** Tabla `fact_financiero`

### 2. Sistema GPS
- **Extrae:** `id_viaje`, `vehiculo_id`, `tipo_vehiculo`, `fecha`, `hora_salida`, `hora_llegada_real`, `hora_llegada_estimada`, `distancia_km`, `numero_entregas`, `combustible_litros`, `estado_viaje`
- **Problemas detectados:** Duplicados, fechas en formatos mixtos (`yyyy-mm-dd`, `mm/dd/yyyy`).
- **Transformaciones:**
  - Parsear fechas
  - Calcular `tiempo_entrega_horas`
  - Calcular `tiempo_estimado_horas`
  - Calcular `diferencia_tiempo_horas`
  - Crear `cumplimiento` (A tiempo / Retrasado)
  - Calcular `costo_combustible_usd`
  - Eliminar duplicados
- **Carga:** Tabla `fact_logistico`

### 3. Sistema de Almacenes
- **Extrae:** `id_despacho`, `cliente_id`, `producto`, `cantidad`, `unidad_medida`, `fecha_despacho`, `bodega_origen`, `peso_bruto`, `peso_unidad`
- **Problemas detectados:** Unidades de medida variadas (`kg`, `ton`, `lb`, `cajas`, `pallets`), IDs de cliente inconsistentes, pesos faltantes, fechas en formato `dd-mmm-yyyy`.
- **Transformaciones:**
  - Homologar `cliente_id`
  - Normalizar unidades a kilogramos (`cantidad_kg`, `peso_bruto_kg`)
  - Imputar pesos faltantes a partir de la cantidad
  - Parsear fechas
- **Carga:** Tabla `fact_almacen`

### 4. CRM Comercial
- **Extrae:** `id_cliente_crm`, `nombre_cliente`, `sector`, `region_comercial`, `satisfaccion_nps`, `fecha_ultima_encuesta`, `ejecutivo_cuenta`, `estado_cliente`
- **Problemas detectados:** IDs inconsistentes, duplicados parciales por cliente, encuestas sin respuesta.
- **Transformaciones:**
  - Homologar `id_cliente_crm`
  - Eliminar duplicados por cliente
  - Clasificar NPS en Promotor / Neutro / Detractor
- **Carga:** Tabla `dim_clientes`

## Modelo Dimensional Resultante

| Tabla | Tipo | Descripción |
|-------|------|-------------|
| `dim_clientes` | Dimensión | Catálogo maestro de clientes con sector, región, satisfacción e ingresos |
| `fact_financiero` | Hechos | Transacciones financieras por factura |
| `fact_logistico` | Hechos | Viajes y entregas con tiempos y cumplimiento |
| `fact_almacen` | Hechos | Despachos de bodega con cantidades normalizadas |
| `kpis_mensuales` | Agregado | Indicadores consolidados por mes |
| `kpis_satisfaccion` | Agregado | Distribución de NPS |
