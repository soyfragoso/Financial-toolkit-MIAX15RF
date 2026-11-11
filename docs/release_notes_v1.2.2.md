# MIAX 15 Financial Powertool v1.2.2
## Sharpe & Sortino + Data Quality & Integrity Edition

### Evolución del proyecto

La versión 1.2.2 formaliza y amplía el enfoque de calidad e integridad
de datos del MIAX 15 Financial Powertool.

La calidad de los datos es un requisito transversal de cualquier proceso
de análisis financiero. Esta evolución organiza los controles existentes
y añade un proceso sistemático, medible y trazable para evaluar los datos
antes de utilizarlos en cálculos de cartera y simulaciones.

No representa un cambio de filosofía del proyecto, sino una extensión
del alcance técnico y una presentación más estructurada de sus controles.

### Alcance funcional

#### 1. Integridad
- Detección de valores ausentes y NaN.
- Detección de valores infinitos y datos no numéricos.
- Identificación de precios de cierre no positivos.
- Detección de volúmenes negativos.
- Validación de coherencia entre precios OHLC.
- Identificación de fechas inválidas y registros duplicados.

#### 2. Completitud
- Recuento de celdas y observaciones ausentes.
- Porcentaje de datos faltantes.
- Porcentaje de completitud global y por columna.
- Identificación de faltantes por activo.

#### 3. Consistencia temporal
- Cobertura temporal individual por activo.
- Identificación de fechas comunes entre series.
- Comparación entre fechas compartidas y fechas observadas.
- Medición de la cobertura temporal común.

#### 4. Tratamiento controlado de datos

El pipeline contempla cuatro políticas:

- `strict`: rechaza datos con problemas de integridad.
- `drop`: elimina registros incompletos o inválidos según las reglas
  de limpieza establecidas.
- `preserve`: conserva los datos para inspección, sin autorizar
  cálculos financieros.
- `forward_fill`: permite completar exclusivamente el precio `close`,
  con un máximo de una observación consecutiva por activo.

No se utiliza interpolación lineal ni se fabrican fechas u observaciones.
El relleno no se extiende a las columnas OHLC ni al volumen.
`adj_close` es una columna opcional.

#### 5. Protección de los cálculos

Los problemas críticos que persistan después del tratamiento impiden
autorizar los cálculos financieros. Los datos conservados únicamente
para inspección tampoco habilitan cálculos.

La validación posterior al tratamiento permite comprobar que la política
aplicada no ha dejado incidencias críticas sin resolver.

#### 6. Trazabilidad y diagnóstico

El informe `data_quality_report.md` documenta:
- Diagnóstico inicial.
- Problemas detectados y su clasificación.
- Recomendación y política seleccionada.
- Registros recibidos, eliminados y completados.
- Diagnóstico posterior al tratamiento.
- Cobertura y alineación temporal.
- Resultado de los criterios de autorización de cálculos.

También se incorporan diagnósticos de descarga para distinguir
símbolos no encontrados, posibles bajas, problemas de conexión,
respuestas vacías y errores del proveedor.

### Criterios de compatibilidad

Esta evolución mantiene la arquitectura y los proveedores existentes.
No modifica el comportamiento del cálculo de rentabilidad de cartera,
la comparación de proveedores ni el tratamiento de datos de inflación
procedentes de FRED.

### Validación

La suite completa de pruebas alcanzó **321 pruebas superadas** durante
la validación de esta evolución.

### Identificación

**Producto:** MIAX 15 Financial Powertool  
**Versión:** 1.2.2  
**Edición:** Sharpe & Sortino + Data Quality & Integrity Edition

