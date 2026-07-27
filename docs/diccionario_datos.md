# Diccionario de datos

## Alcance de la base comparable

- **Países:** Ecuador (`ECU`), Colombia (`COL`), Chile (`CHL`) y Perú (`PER`).
- **Periodo:** 2014 hasta el último año disponible en cada indicador.
- **Frecuencia:** anual.
- **Fuente primaria:** World Development Indicators (WDI) del Banco Mundial.
- **Unidad de observación:** un país y un año.

El archivo procesado principal será `data/processed/indicators_annual.csv`. Cada fila tendrá las columnas de identificación y los cuatro indicadores comparables siguientes.

| Campo | Descripción | Fuente / código | Unidad | Regla de uso |
|---|---|---|---|---|
| `country_code` | Código ISO alfa-3 del país | WDI | texto | `ECU`, `COL`, `CHL` o `PER` |
| `country_name` | Nombre del país | WDI | texto | Nombre informado por la fuente |
| `year` | Año de referencia | WDI | entero | 2014–último disponible |
| `employment_to_population_15plus_pct` | Personas ocupadas como proporción de la población de 15 años o más | `SL.EMP.TOTL.SP.ZS` | porcentaje | Estimación modelada de OIT; comparable entre países |
| `unemployment_rate_pct` | Personas sin empleo, disponibles y buscándolo, como proporción de la fuerza laboral | `SL.UEM.TOTL.ZS` | porcentaje | Estimación modelada de OIT; comparable entre países |
| `internet_users_pct` | Personas que usaron internet en los últimos tres meses | `IT.NET.USER.ZS` | porcentaje de la población | Indicador de uso digital |
| `fixed_broadband_per_100` | Suscripciones de banda ancha fija | `IT.NET.BBND.P2` | suscripciones por 100 personas | Proxy de infraestructura digital |

## Módulo nacional de Ecuador

El archivo `data/processed/ecuador_labor_market.csv` contendrá indicadores de ENEMDU con sus períodos originales y estas columnas mínimas: `period`, `frequency`, `informal_employment_pct`, `adequate_employment_pct`, `unemployment_rate_pct` y `source_url`.

No se combinará mecánicamente la informalidad de ENEMDU con la serie internacional: el indicador internacional disponible se limita al empleo no agrícola y su metodología puede diferir. Los indicadores mensuales y trimestrales de ENEMDU tampoco se mezclarán sin una agregación explícita.

## Trazabilidad y valores faltantes

- Cada descarga se guardará sin modificar en `data/raw/`.
- `data/metadata/` guardará fecha de extracción, URL, indicador y versión/metadatos de la fuente.
- Los valores no disponibles se almacenarán como vacíos (`NA` al cargar en Python), nunca como cero.
- Cada transformación deberá conservar `country_code`, `year` y una referencia de fuente.

## Indicadores derivados

El archivo `data/processed/indicators_derived.csv` conserva todas las columnas del panel base e incorpora:

| Campo | Cálculo | Interpretación |
|---|---|---|
| `*_yoy_change` | Valor del año actual menos el del año anterior, dentro de cada país | Cambio interanual en puntos porcentuales o suscripciones por 100 personas |
| `*_gap_vs_ecu` | Valor del país menos el valor de Ecuador en el mismo año | Brecha frente a Ecuador; Ecuador tiene valor 0 cuando ambos datos están disponibles |
| `digitalization_index_0_100` | Promedio de los puntajes min–max de `internet_users_pct` y `fixed_broadband_per_100` | Proxy descriptivo de digitalización; 0 y 100 corresponden al mínimo y máximo observados del panel disponible, no a umbrales absolutos |

El índice solo se calcula cuando sus dos componentes están disponibles. No se utilizará como medición causal ni para reemplazar los indicadores originales.
