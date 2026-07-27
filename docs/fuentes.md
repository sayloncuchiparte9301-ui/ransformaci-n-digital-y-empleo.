# Fuentes de datos

## Serie comparable internacional

La fuente de descarga será la API de World Development Indicators del Banco Mundial. Para los cuatro países, el patrón de consulta es:

`https://api.worldbank.org/v2/country/ECU;COL;CHL;PER/indicator/{codigo}?format=json&date=2014:2025&per_page=1000`

| Indicador | Código WDI | Fuente de origen | Uso |
|---|---|---|---|
| Empleo/población, 15+ | `SL.EMP.TOTL.SP.ZS` | OIT, estimaciones modeladas | Comparación laboral anual |
| Desempleo total | `SL.UEM.TOTL.ZS` | OIT, estimaciones modeladas | Comparación laboral anual |
| Uso de internet | `IT.NET.USER.ZS` | UIT | Adopción/uso digital |
| Banda ancha fija | `IT.NET.BBND.P2` | UIT | Infraestructura digital |

## Ecuador: detalle del mercado laboral

- **INEC — ENEMDU:** https://anda.inec.gob.ec/anda/
- Uso previsto: empleo informal, empleo adecuado/pleno y desagregaciones nacionales.
- Se preservará la periodicidad publicada por INEC. El análisis debe documentar toda agregación anual y no mezclar períodos puntuales con acumulados.

## Restricciones de comparabilidad

La informalidad no se incorporará al panel regional hasta comprobar disponibilidad y definición homogénea. El indicador WDI `SL.ISV.IFRM.ZS` se limita al empleo no agrícola y su propia documentación advierte diferencias metodológicas entre países y en el tiempo.
