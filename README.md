# MIAX 15 Financial Powertool

**Python toolkit for financial data analysis, portfolio management and Monte Carlo simulation.**

[Versión en español](#español) | [English version](#english)

---

<a id="español"></a>
# Español

## 1. Descripción

**MIAX 15 Financial Powertool** es una herramienta desarrollada en Python para la descarga, procesamiento y análisis de datos financieros, la construcción y evaluación de carteras de inversión y la simulación de escenarios mediante el método de Monte Carlo.

El proyecto combina una biblioteca modular y reutilizable con una interfaz de terminal interactiva que guía al usuario a través del análisis de activos y carteras.

Su objetivo es facilitar un flujo de trabajo reproducible, desde la obtención de datos históricos hasta la generación de indicadores, visualizaciones e informes.

## 2. Funcionalidades principales

- **Obtención de datos financieros:** conexión con Yahoo Finance y Twelve Data mediante proveedores estandarizados.
- **Datos macroeconómicos:** integración independiente con FRED para consultar PIB real (GDPC1), IPC (CPIAUCSL), desempleo (UNRATE), tipos de interés (FEDFUNDS) y rendimiento del bono del Tesoro a 10 años (GS10).
- **Rentabilidad real:** cálculo de la evolución de la cartera ajustada por inflación mediante el IPC.
- **Rentabilidad ajustada al riesgo:** cálculo de los ratios de Sharpe y Sortino de la cartera, con el tipo libre de riesgo de FRED (FEDFUNDS) o introducido por el usuario, y lectura automática de cada ratio.
- **Descarga de múltiples activos:** consulta de varios tickers y normalización de los datos recibidos.
- **Procesamiento y validación:** limpieza, preparación y validación de series temporales financieras.
- **Análisis de activos:** construcción de objetos `PriceSeries` y cálculo de estadísticas financieras.
- **Gestión de carteras:** creación de objetos `Portfolio`, asignación de ponderaciones y análisis conjunto de activos.
- **Análisis de riesgo y rendimiento:** métricas descriptivas, rendimientos y relaciones entre activos.
- **Simulación de Monte Carlo:** generación de trayectorias para activos individuales y carteras.
- **Visualización:** gráficos de análisis y simulación.
- **Informes:** generación de informes en Markdown y gráficos mediante `Portfolio.report()` y `Portfolio.plots_report()`.
- **Comparación de proveedores:** contraste de datos obtenidos desde Yahoo Finance y Twelve Data.
- **Series macroeconómicas:** representación de indicadores mediante objetos `MacroSeries` y estadísticas descriptivas.
- **Exportación:** almacenamiento de datos, resultados y documentos para su análisis posterior.
- **Interfaz interactiva:** ejecución guiada mediante Rich en la terminal.

## 3. Arquitectura

El proyecto utiliza una estructura `src/` y separa las responsabilidades en módulos:

```text
Financial-toolkit-MIAX15RF/
├── docs/
│   └── architecture.md
├── examples/
│   └── example_portfolio.py
├── src/
│   └── Financial_toolkit/
│       ├── analytics/
│       │   ├── plots.py
│       │   └── reports.py
│       ├── cli/
│       │   ├── banners.py
│       │   ├── formatting.py
│       │   └── interface.py
│       ├── data/
│       │   ├── downloader.py
│       │   ├── macro_pipeline.py
│       │   ├── macro_providers.py
│       │   ├── company_universe.py
│       │   ├── pipeline.py
│       │   ├── preprocessing.py
│       │   └── providers.py
│       ├── models/
│       │   ├── macro_series.py
│       │   ├── portfolio.py
│       │   ├── price_series.py
│       │   └── real_performance.py
│       ├── simulation/
│       │   └── monte_carlo.py
│       └── utils/
│           └── validators.py
├── tests/
├── outputs/
├── pyproject.toml
└── README.md
```

### Componentes

| Módulo | Responsabilidad |
|---|---|
| `data` | Proveedores, descarga, pipeline y preprocesamiento |
| `models` | Modelos `PriceSeries`, `MacroSeries` y `Portfolio` |
| `analytics` | Informes y visualizaciones y ratio de Sharpe y Sortino |
| `simulation` | Simulación de Monte Carlo |
| `utils` | Validaciones y utilidades |
| `cli` | Interfaz de terminal, presentación y formato de resultados |
| `examples` | Ejemplo de ejecución integral |

La documentación de arquitectura y el diagrama correspondiente se encuentran en [`docs/architecture.md`](docs/architecture.md).

## 4. Requisitos

- Python 3.10 o superior.
- Conexión a Internet para descargar datos financieros.
- Una clave API de Twelve Data cuando se utilice ese proveedor.
- Una clave API de FRED cuando se utilice el proveedor macroeconómico.
- Dependencias instaladas mediante `pip`.

Las dependencias principales incluyen:

- pandas
- NumPy
- yfinance
- Matplotlib
- Seaborn
- SciPy
- Requests

La interfaz interactiva utiliza Rich. Las pruebas se ejecutan con pytest.

## 5. Instalación

Clona el repositorio:

```bash
git clone https://github.com/soyfragoso/Financial-toolkit-MIAX15RF
cd Financial-toolkit-MIAX15RF
```

Crea y activa un entorno virtual:

**Windows:**

```bash
python -m venv .venv
.venv\Scripts\activate
```

**Linux / macOS:**

```bash
python -m venv .venv
source .venv/bin/activate
```

Instala el proyecto con las dependencias de desarrollo y de interfaz:

```bash
pip install -e ".[cli,dev]"
```

Esta instalación incluye las dependencias principales, Rich y pytest.

## 6. Configuración de Twelve Data

Yahoo Finance puede utilizarse sin una clave API.

Para Twelve Data se necesita una clave API. Puede obtenerse en:

https://twelvedata.com/

Configura la variable de entorno `TWELVE_DATA_API_KEY`.

**Linux / macOS:**

```bash
export TWELVE_DATA_API_KEY="YOUR_API_KEY"
```

**Windows PowerShell:**

```powershell
$env:TWELVE_DATA_API_KEY="YOUR_API_KEY"
```

También es posible proporcionar la clave mediante el argumento `api_key` del proveedor.

No incluyas claves API en el código fuente, en el README ni en el repositorio.

## 7. Configuración de FRED

La integración macroeconómica de FRED es opcional e independiente de los proveedores de precios de mercado. Para utilizarla, se necesita una clave API gratuita de FRED.

Configura la variable de entorno antes de iniciar el programa.

En Linux, macOS o Codespaces:

```bash
export FRED_API_KEY="TU_CLAVE_API"
```

En PowerShell:

```powershell
$env:FRED_API_KEY="TU_CLAVE_API"
```

El miniagente puede consultar las siguientes series:

| Indicador | Código FRED |
|---|---|
| PIB real | `GDPC1` |
| Índice de precios al consumidor (IPC) | `CPIAUCSL` |
| Tasa de desempleo | `UNRATE` |
| Tasa de fondos federales | `FEDFUNDS` |
| Rendimiento del Tesoro a 10 años | `GS10` |

Si la clave no está configurada o los datos macroeconómicos no están disponibles, el análisis financiero principal puede continuar sin la integración FRED.

**Consideración metodológica sobre la inflación:** el cálculo de rentabilidad real utiliza las observaciones del IPC disponibles y no posteriores a la fecha de referencia de la cartera. Sin embargo, las fechas de observación no equivalen necesariamente a las fechas de publicación. La implementación no reconstruye los retrasos de publicación ni las revisiones históricas de FRED; por tanto, el resultado no debe interpretarse como una serie histórica completamente libre de sesgo de anticipación (*look-ahead bias*) para backtesting.

## 8. Ejecución

Desde la raíz del proyecto:

```bash
python examples/example_portfolio.py
```

El programa inicia **MIAX 15 Financial Powertool (miniagente interactivo)**, una interfaz de terminal que guía al usuario por las distintas etapas del análisis.

El flujo contempla:

1. Presentación y configuración inicial.
2. Selección del proveedor de datos.
3. Selección de activos.
4. Asignación de ponderaciones de la cartera.
5. Definición del periodo histórico.
6. Análisis individual y conjunto de los activos.
7. Generación de informes y visualizaciones.
8. Simulación de Monte Carlo.
9. Exportación de resultados.
10. Comparación entre proveedores.
11. Consulta opcional de indicadores macroeconómicos de FRED.
12. Cálculo de rentabilidad real ajustada por IPC, cuando hay datos disponibles.
13. Cálculo opcional de los ratios de Sharpe y Sortino, con lectura automática de cada ratio.
14. Elaboración del resumen ejecutivo y presentación del estado de calidad e integridad de las pruebas.

Las opciones disponibles dependen de los datos obtenidos, del proveedor seleccionado y de la configuración de cada ejecución.

## 9. Archivos generados

Cada ejecución crea un directorio independiente dentro de `outputs/`, identificado mediante una marca temporal.

Entre los archivos que puede generar se encuentran:

| Archivo | Contenido |
|---|---|
| `portfolio_report.md` | Informe de análisis de la cartera |
| `historical_data.csv` | Datos históricos descargados |
| `portfolio_returns.csv` | Rendimientos de la cartera |
| `monte_carlo_trajectories.csv` | Trayectorias simuladas |
| `monte_carlo_final_values.csv` | Valores finales de las simulaciones |
| `monte_carlo_analysis.png` | Visualización de Monte Carlo |
| `provider_comparison.csv` | Comparación de proveedores, cuando se solicita |
| `fred_indicators.csv` | Indicadores macroeconómicos de FRED, cuando están disponibles |
| `real_performance.csv` | Evolución de la cartera ajustada por inflación |
| `real_performance.png` | Visualización de la rentabilidad real |
| `executive_summary.md` | Resumen ejecutivo |

También se generan gráficos individuales a partir de `Portfolio.plots_report()`.

Los archivos concretos dependen de las funcionalidades ejecutadas y de los resultados disponibles.

## 10. Límites y consideraciones de Twelve Data

La integración con Twelve Data utiliza el endpoint `/time_series` para obtener datos históricos.

Es importante distinguir entre los límites publicados por el proveedor y las características de la implementación de este proyecto.

### Límites del proveedor

Según la documentación y los planes publicados por Twelve Data:

- El endpoint `/time_series` tiene un coste de referencia de **1 crédito por símbolo**.
- El plan Basic gratuito publica un límite de **8 créditos por minuto** y **800 créditos por día**.
- Los créditos por minuto se restablecen cada minuto; la cuota diaria se restablece a medianoche UTC.
- Al superar los límites aplicables, la API puede responder con HTTP 429 (Too Many Requests).
- Las solicitudes de series temporales admiten hasta **5.000 puntos de datos por petición**.
- La profundidad histórica y la disponibilidad de instrumentos dependen del mercado, del símbolo y del plan contratado.

Estos límites pueden cambiar. Deben verificarse en la documentación y en el plan vigente antes de realizar consultas de gran volumen.

### Limitaciones de esta implementación

- Se realiza **una petición HTTP independiente por ticker**. No se implementa descarga por lotes en una sola petición.
- Por tanto, una ejecución con varios tickers consume créditos de acuerdo con el número de símbolos consultados y el coste aplicable a cada petición.
- El intervalo está fijado en datos diarios (`1day`).
- Se establece un timeout de 30 segundos por petición.
- No se implementan reintentos automáticos, espera exponencial (*backoff*) ni gestión automática de cuotas.
- Los errores HTTP se propagan mediante el mecanismo de comprobación de respuestas de Requests.
- La respuesta se normaliza al esquema común de datos del proyecto. Si el proveedor no proporciona una columna, esta puede completarse con valores ausentes (`NaN`).
- En particular, `adj_close` puede no estar disponible en los datos de Twelve Data y permanecer como `NaN`.
- La implementación adapta la fecha final de consulta para mantener una convención de intervalo compatible con la utilizada por Yahoo Finance.
- Los periodos extensos pueden superar el máximo de puntos permitido por petición y requerir una estrategia de consulta distinta.

**Recomendación:** para análisis con numerosos activos o periodos extensos, comprueba previamente la cuota disponible, la cobertura histórica y las condiciones de tu plan de Twelve Data.

Documentación oficial:

- Créditos y límites: https://support.twelvedata.com/en/articles/5615854-credits
- Planes y precios: https://twelvedata.com/pricing
- Endpoint Time Series: https://twelvedata.com/docs#time-series
- Preguntas frecuentes sobre datos históricos: https://support.twelvedata.com/

## 11. Pruebas

### Estandarización de datos

MIAX 15 Financial Powertool utiliza un esquema común para integrar datos de distintos proveedores, incluidos Yahoo Finance y Twelve Data.

El esquema normalizado contempla los siguientes campos:

- `ticker`: símbolo del activo.
- `date`: fecha de negociación.
- `open`, `high`, `low`, `close`: precios OHLC.
- `adj_close`: precio de cierre ajustado.
- `volume`: volumen negociado.

Los proveedores de mercado entregan los datos al pipeline, que aplica el procesamiento y la normalización necesarios antes de utilizarlos en los modelos.

Los datos macroeconómicos de FRED utilizan un flujo independiente. `FredDataProvider` obtiene las observaciones y `MacroDataPipeline` las organiza mediante objetos `MacroSeries`. Su esquema utiliza los campos `series_id`, `date` y `value`, por lo que no se mezcla con el esquema OHLCV de los precios de mercado. La clave API puede configurarse mediante la variable de entorno `FRED_API_KEY`.

### Controles de calidad de datos

El sistema incorpora controles automatizados para verificar, entre otros aspectos:

- Presencia de las columnas obligatorias.
- Normalización de símbolos y fechas.
- Conversión y validación de valores numéricos.
- Detección y eliminación de registros duplicados o incompletos.
- Coherencia de los valores OHLC.
- Rechazo de precios de cierre no positivos.
- Detección de valores numéricos infinitos.
- Conservación de los datos originales durante el preprocesamiento.

Estos controles verifican la consistencia estructural y numérica de los datos recibidos. No constituyen una auditoría externa ni garantizan la exactitud de las fuentes originales.

### Pruebas de integridad del sistema

Las pruebas automatizadas cubren los principales componentes:

- Proveedores de datos de mercado y macroeconómicos, descarga y pipelines.
- Validación y procesamiento de series macroeconómicas.
- Series de precios y validación de activos.
- Construcción de carteras y validación de ponderaciones.
- Rendimientos, volatilidad y métricas de riesgo.
- Simulaciones Monte Carlo y de carteras.
- Validación de parámetros, matrices de covarianza y reproducibilidad.
- Generación de informes y gráficos.
- Universo estático de compañías incorporado en la versión 1.1.
- Cálculo y validación de rentabilidad real ajustada por inflación.

### Suite automatizada

En la versión 1.2, la última ejecución validada de la suite automatizada completó **212 pruebas aprobadas**, sin fallos ni advertencias. El número de pruebas puede cambiar conforme evolucione el proyecto.



Para ejecutar la suite de pruebas:

```bash
pytest -q
```

La interfaz de calidad presenta el resultado de las pruebas mediante las siguientes categorías:

- **Correcto:** todas las pruebas ejecutadas finalizaron satisfactoriamente.
- **Advertencia:** existen incidencias, advertencias o errores que requieren atención.
- **Revisión necesaria:** al menos una prueba ha fallado.
- **No verificado:** no ha sido posible ejecutar la suite de pruebas.

El resumen contempla pruebas aprobadas, errores o advertencias, pruebas fallidas, omitidas, total de pruebas y porcentaje de aprobación.

## 12. Dependencias opcionales

El proyecto define los siguientes grupos opcionales:

```bash
pip install -e ".[cli]"
```

Instala Rich para la interfaz de terminal.

```bash
pip install -e ".[dev]"
```

Instala pytest para desarrollo y pruebas.

Para instalar ambos grupos:

```bash
pip install -e ".[cli,dev]"
```

## 13. Licencia

Este proyecto declara la licencia MIT en su configuración de empaquetado (`pyproject.toml`). Consulta el archivo [LICENSE](LICENSE) para conocer sus términos completos.

---

<a id="english"></a>
# English

## 1. Overview

**MIAX 15 Financial Powertool** is a Python toolkit for financial data retrieval and processing, investment portfolio construction and analysis, and scenario generation through Monte Carlo simulation.

The project combines a modular, reusable library with an interactive terminal interface that guides users through asset and portfolio analysis.

Its purpose is to provide a reproducible workflow, from historical data retrieval to financial metrics, visualizations, and reports.

## 2. Main features

- **Financial data retrieval:** standardized connections to Yahoo Finance and Twelve Data.
- **Macroeconomic data:** independent FRED integration for real GDP (GDPC1), CPI (CPIAUCSL), unemployment (UNRATE), federal funds rate (FEDFUNDS), and 10-year Treasury yield (GS10).
- **Real performance:** calculation of portfolio performance adjusted for inflation using CPI.
- **Risk-adjusted return:** Sharpe and Sortino ratios for the portfolio, using the FRED risk-free rate (FEDFUNDS) or one entered by the user, with an automatic reading of each ratio.
- **Multiple asset downloads:** retrieval of several tickers and normalization of provider data.
- **Data processing and validation:** cleaning, preparation, and validation of financial time series.
- **Asset analysis:** `PriceSeries` objects and automatic financial statistics.
- **Portfolio management:** `Portfolio` objects, asset weights, and combined portfolio analysis.
- **Risk and return analysis:** descriptive metrics, returns, and relationships between assets.
- **Monte Carlo simulation:** simulation paths for individual assets and portfolios.
- **Visualization:** analytical and simulation charts.
- **Reporting:** Markdown reports and charts through `Portfolio.report()` and `Portfolio.plots_report()`.
- **Provider comparison:** comparison of Yahoo Finance and Twelve Data data.
- **Macroeconomic series:** representation of indicators through `MacroSeries` objects and descriptive statistics.
- **Export:** storage of data, results, and reports for further analysis.
- **Interactive interface:** guided terminal execution using Rich.

## 3. Architecture

The project follows a `src/` layout and separates responsibilities into modules:

| Module | Responsibility |
|---|---|
| `data` | Data providers, downloads, pipeline, and preprocessing |
| `models` | `PriceSeries`, `MacroSeries`, and `Portfolio` models |
| `analytics` | Reports, visualizations and Sharpe and Sortino ratios |
| `simulation` | Monte Carlo simulation |
| `utils` | Validation and utilities |
| `cli` | Terminal interface, presentation, and result formatting |
| `examples` | End-to-end usage example |

Architecture documentation and the corresponding diagram are available in [`docs/architecture.md`](docs/architecture.md).

## 4. Requirements

- Python 3.10 or later.
- Internet access for financial data retrieval.
- A Twelve Data API key when using that provider.
- A FRED API key when using the macroeconomic data provider.
- Dependencies installed through `pip`.

Main dependencies include pandas, NumPy, yfinance, Matplotlib, Seaborn, SciPy, and Requests.

The interactive interface uses Rich. Tests are run with pytest.

## 5. Installation

Clone the repository:

```bash
git clone https://github.com/soyfragoso/Financial-toolkit-MIAX15RF
cd Financial-toolkit-MIAX15RF
```

Create and activate a virtual environment:

**Windows:**

```bash
python -m venv .venv
.venv\Scripts\activate
```

**Linux / macOS:**

```bash
python -m venv .venv
source .venv/bin/activate
```

Install the project with its development and interface dependencies:

```bash
pip install -e ".[cli,dev]"
```

This installs the core dependencies, Rich, and pytest.

## 6. Twelve Data configuration

Yahoo Finance can be used without an API key.

Twelve Data requires an API key, available at:

https://twelvedata.com/

Set the `TWELVE_DATA_API_KEY` environment variable.

**Linux / macOS:**

```bash
export TWELVE_DATA_API_KEY="YOUR_API_KEY"
```

**Windows PowerShell:**

```powershell
$env:TWELVE_DATA_API_KEY="YOUR_API_KEY"
```

The key can also be passed through the provider's `api_key` argument.

Do not include API keys in source code, the README, or the repository.

## 7. FRED configuration

FRED macroeconomic integration is optional and independent of market price data providers. A free FRED API key is required to use it.

Set the environment variable before launching the program.

On Linux, macOS, or Codespaces:

```bash
export FRED_API_KEY="YOUR_API_KEY"
```

On PowerShell:

```powershell
$env:FRED_API_KEY="YOUR_API_KEY"
```

The miniagent can retrieve the following series:

| Indicator | FRED series |
|---|---|
| Real GDP | `GDPC1` |
| Consumer Price Index (CPI) | `CPIAUCSL` |
| Unemployment rate | `UNRATE` |
| Federal funds rate | `FEDFUNDS` |
| 10-year Treasury yield | `GS10` |

If the API key is not configured or macroeconomic data is unavailable, the main financial analysis can continue without FRED integration.

**Inflation methodology note:** real performance calculations use available CPI observations no later than the portfolio reference date. However, observation dates do not necessarily match publication dates. The implementation does not reconstruct historical publication delays or FRED revisions; therefore, the result should not be interpreted as a fully point-in-time, look-ahead-bias-free historical series for backtesting.

## 8. Running the example

From the project root:

```bash
python examples/example_portfolio.py
```

The program launches **MIAX 15 Financial Powertool (interactive miniagent)**, a terminal interface that guides users through the analysis workflow.

The workflow covers:

1. Welcome and initial configuration.
2. Data provider selection.
3. Asset selection.
4. Portfolio weight allocation.
5. Historical period selection.
6. Individual asset and portfolio analysis.
7. Report and visualization generation.
8. Monte Carlo simulation.
9. Results export.
10. Provider comparison.
11. Optional retrieval of FRED macroeconomic indicators.
12. CPI-adjusted real performance calculation, when data is available.
13. Optional Sharpe and Sortino ratio calculation, with an automatic reading of each ratio.
14. Executive summary generation and test quality and integrity status.

Available options depend on retrieved data, the selected provider, and the configuration of each run.

## 9. Generated files

Each execution creates a separate timestamped directory under `outputs/`.

Potential outputs include:

| File | Contents |
|---|---|
| `portfolio_report.md` | Portfolio analysis report |
| `historical_data.csv` | Retrieved historical data |
| `portfolio_returns.csv` | Portfolio returns |
| `monte_carlo_trajectories.csv` | Simulated paths |
| `monte_carlo_final_values.csv` | Final simulation values |
| `monte_carlo_analysis.png` | Monte Carlo visualization |
| `provider_comparison.csv` | Provider comparison, when requested |
| `fred_indicators.csv` | FRED macroeconomic indicators, when available |
| `real_performance.csv` | Inflation-adjusted portfolio performance |
| `real_performance.png` | Real performance visualization |
| `executive_summary.md` | Executive summary |

Individual charts can also be generated through `Portfolio.plots_report()`.

Actual outputs depend on the features executed and the available results.

## 10. Twelve Data API limits and considerations

The Twelve Data integration uses the `/time_series` endpoint to retrieve historical data.

Provider limits should be distinguished from the behavior and limitations of this project's implementation.

### Provider limits

According to Twelve Data's published documentation and plans:

- The `/time_series` endpoint has a reference cost of **1 credit per symbol**.
- The published free Basic plan provides **8 credits per minute** and **800 credits per day**.
- Per-minute credits reset every minute; the daily quota resets at midnight UTC.
- Exceeding applicable limits may result in HTTP 429 (Too Many Requests).
- Time Series requests support up to **5,000 data points per request**.
- Historical depth and instrument availability depend on the market, symbol, and subscription plan.

These limits may change. Check the current documentation and subscription plan before making high-volume requests.

### Implementation limitations

- The provider makes **one independent HTTP request per ticker**. Batch requests are not implemented.
- Therefore, a run involving multiple tickers consumes credits according to the number of symbols requested and the applicable request cost.
- The data interval is fixed to daily (`1day`).
- Each request uses a 30-second timeout.
- Automatic retries, exponential backoff, and automated quota management are not implemented.
- HTTP errors are propagated through Requests' response validation.
- Provider responses are normalized to the toolkit's common data schema. Missing columns may be populated with `NaN`.
- In particular, `adj_close` may not be available from Twelve Data and may remain `NaN`.
- The implementation adjusts the requested end date to maintain an interval convention compatible with Yahoo Finance.
- Long date ranges may exceed the maximum number of data points per request and require a different retrieval strategy.

**Recommendation:** before running analyses with many assets or long historical periods, check your available quota, historical coverage, and Twelve Data subscription conditions.

Official documentation:

- Credits and limits: https://support.twelvedata.com/en/articles/5615854-credits
- Plans and pricing: https://twelvedata.com/pricing
- Time Series endpoint: https://twelvedata.com/docs#time-series
- Historical data FAQ: https://support.twelvedata.com/

## 11. Testing

### Data standardization

MIAX 15 Financial Powertool uses a common schema to integrate data from different providers, including Yahoo Finance and Twelve Data.

The normalized schema includes:

- `ticker`: asset symbol.
- `date`: trading date.
- `open`, `high`, `low`, `close`: OHLC prices.
- `adj_close`: adjusted closing price.
- `volume`: trading volume.

Market data providers supply data to the pipeline, which applies the required processing and normalization before the data is used by the models.

FRED macroeconomic data follows an independent workflow. `FredDataProvider` retrieves observations and `MacroDataPipeline` organizes them through `MacroSeries` objects. Its schema uses the fields `series_id`, `date`, and `value`, keeping it separate from the OHLCV market price schema. The API key can be configured through the `FRED_API_KEY` environment variable.

### Data quality controls

Automated controls verify, among other aspects:

- Required columns are present.
- Tickers and dates are normalized.
- Numeric values are converted and validated.
- Duplicate and incomplete records are detected and removed.
- OHLC values are consistent.
- Non-positive closing prices are rejected.
- Infinite numeric values are detected.
- Original data is preserved during preprocessing.

These controls verify the structural and numerical consistency of received data. They do not constitute an external audit or guarantee the accuracy of the original data sources.

### System integrity tests

The automated tests cover the main system components:

- Market and macroeconomic data providers, downloading and pipelines.
- Macroeconomic series validation and processing.
- Price series and asset validation.
- Portfolio construction and weight validation.
- Returns, volatility and risk metrics.
- Monte Carlo and portfolio simulations.
- Parameter validation, covariance matrices and reproducibility.
- Report and chart generation.
- Static company universe introduced in version 1.1.
- Calculation and validation of inflation-adjusted real performance.

### Automated test suite

In version 1.2, the latest validated automated test run completed **212 passing tests**, with no failures or warnings. The test count may change as the project evolves.



Run the test suite with:

```bash
pytest -q
```

The quality interface reports test results using the following categories:

- **Correct:** all executed tests passed.
- **Warning:** issues, warnings, or errors require attention.
- **Review required:** at least one test failed.
- **Not verified:** the test suite could not be executed.

The summary includes passed tests, errors or warnings, failed tests, skipped tests, total tests, and pass percentage.

## 12. Optional dependencies

Install Rich for the terminal interface:

```bash
pip install -e ".[cli]"
```

Install pytest for development and testing:

```bash
pip install -e ".[dev]"
```

Install both optional groups:

```bash
pip install -e ".[cli,dev]"
```

## 13. License

The project declares the MIT license in its packaging configuration (`pyproject.toml`). Refer to the [LICENSE](LICENSE) file for the complete terms.

---

**MIAX 15 Financial Powertool**
*Financial data analysis, portfolio management, and Monte Carlo simulation.*