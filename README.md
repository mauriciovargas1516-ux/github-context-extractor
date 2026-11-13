#  Hub de Aplicaciones y Super Extractor de Contexto GitHub para IA

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://app-context-extractor-cl8x5kwfdodzvmx7m3vean.streamlit.app/)
[![Lanzar Super Extractor en Streamlit](https://img.shields.io/badge/_ABRIR_HUB_Y_SUPER_EXTRACTOR_EN_STREAMLIT-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://app-context-extractor-cl8x5kwfdodzvmx7m3vean.streamlit.app/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://github.com/mauriciovargas1516-ux/github-context-extractor)

Plataforma centralizada de ingeniería de contexto y lanzador de aplicaciones web desarrollada en **Python y Streamlit**. Se conecta en tiempo real a la API REST pública de GitHub (`mauriciovargas1516-ux`) para recorrer recursivamente el árbol de directorios de múltiples repositorios y consolidar su código fuente, scripts y documentación técnica en un único archivo maestro `.txt` listo para alimentar ventanas de contexto de modelos de Inteligencia Artificial (LLMs).

 **Acceso directo al Hub y Super Extractor en vivo:**  
 **[https://app-context-extractor-cl8x5kwfdodzvmx7m3vean.streamlit.app/](https://app-context-extractor-cl8x5kwfdodzvmx7m3vean.streamlit.app/)**

---

##  1. Directorio de Plataformas Interactivas Conectadas (Streamlit Cloud)

| Plataforma / Asignatura | Repositorio GitHub | Aplicación Web en Vivo |
| :--- | :--- | :--- |
| **Hub & Super Extractor GitHub** | [`github-context-extractor`](https://github.com/mauriciovargas1516-ux/github-context-extractor) | [ Abrir Super Extractor](https://app-context-extractor-cl8x5kwfdodzvmx7m3vean.streamlit.app/) |
| **Evaluación Integrada de Proyectos** | [`PROYECTOS-2026`](https://github.com/mauriciovargas1516-ux/PROYECTOS-2026) | [ Abrir Suite Proyectos](https://proyectos-2026-ubfvxgpqmpp5z7dn6wlnn3.streamlit.app/) |
| **Finanzas Avanzadas** | [`FINANZAS-AVANZADAS-2026`](https://github.com/mauriciovargas1516-ux/FINANZAS-AVANZADAS-2026) | [ Abrir Simulador Finanzas](https://finanzas-avanzadas-2026-nxvqzsfrrtgu9e92javcli.streamlit.app/) |
| **Desarrollo y Gestión Territorial** | [`DESARROLLO-Y-GESTION-TERRITORIAL-2026`](https://github.com/mauriciovargas1516-ux/DESARROLLO-Y-GESTION-TERRITORIAL-2026) | [ Abrir Motor Territorial](https://desarrollo-y-gestion-territorial-2026-9yq3jazfc52x93tfumxwpz.streamlit.app/) |
| **Gestión Tributaria** | [`GESTION-TRIBUTARIA-2026`](https://github.com/mauriciovargas1516-ux/GESTION-TRIBUTARIA-2026) | [ Abrir Suite Tributaria](https://gestion-tributaria-2026-avecwdhabftj7rjnx5knmb.streamlit.app/) |

---

##  2. Ecosistema de 10 Repositorios Indexados Automáticamente

El motor detecta y empaqueta bajo demanda cualquiera de los siguientes repositorios públicos del portafolio:

1. **`github-context-extractor`:** Hub de aplicaciones en Streamlit y compilador de contexto multi-repositorio para IA.
2. **`GESTION-TRIBUTARIA-2026`:** Suite normativa y simulador impositivo (Ciclo de Vida, Derechos Art. 8 bis CT, Rentas 1ª/2ª Categoría, IVA DL 825 / F29 y Analítica PGCT 2026 SII).
3. **`FINANZAS-AVANZADAS-2026`:** Simulador corporativo para evaluación de activos reales, estructura de capital (CAPM / WACC), Flujo de Caja Libre y del Inversionista, escenarios y Monte Carlo.
4. **`PROYECTOS-2026`:** Suite de formulación y evaluación privada y social de proyectos (normativa SNI / MIDESO 2026) con exportación automatizada de informes Word, PDF y libros Excel.
5. **`DESARROLLO-Y-GESTION-TERRITORIAL-2026`:** Motor econométrico y espacial para análisis regional (ILPES / Shift & Share MADE), convergencia REAT (Sigma/Beta, Gini, Theil, HHI), redes empresariales (UCINET/Dini) y ordenamiento territorial.
6. **`insumaes-woocommerce-automation`:** Pipeline de automatización de inventario e integración de catálogo con Python y Google Cloud Platform (GCP).
7. **`moodle-hybrid-scraper`:** Rastreador web híbrido (`Selenium` + `Requests`) para extracción automatizada de documentos en plataformas Moodle.
8. **`motor-planos-sec-te1-chile`:** Motor paramétrico en Python (`ezdxf` + `Streamlit`) para generación automática de planos eléctricos AutoCAD (`.dxf`), cuadros de cargas y caída de tensión bajo normativa SEC.
9. **`motor-auditor-dte-finops`:** Motor en Python para extracción y auditoría automática de Documentos Tributarios Electrónicos (DTEs) y prevención de pagos duplicados.
10. **`motor-conciliador-chile`:** Sistema de conciliación financiera y cruce automatizado de registros tributarios y contables.

---

##  3. Arquitectura y Funcionamiento Técnico

* **Consulta Dinámica vía API REST de GitHub:** Obtiene en vivo la lista de repositorios del usuario (`https://api.github.com/users/mauriciovargas1516-ux/repos`), metadatos y rama principal sin almacenar credenciales ni requerir clonación local.
* **Recorrido Recursivo de Árboles Git (`git/trees?recursive=1`):** Construye el inventario completo de rutas y pesos en bytes de todos los archivos contenidos en cada repositorio seleccionado.
* **Filtro Inteligente de Extensiones y Tamaño:** Descarga e incrusta íntegramente el código fuente y documentación (`.py`, `.md`, `.txt`, `.rmd`, `.toml`, `.json`) de hasta 300 KB por archivo, registrando los binarios pesados (`.xlsx`, `.pdf`, `.zip`, `.png`, `.docx`) únicamente en el índice para optimizar el consumo de tokens al cargar el archivo `.txt` en cualquier chat de IA.

---

##  4. Estructura del Repositorio y Ejecución Local

| Archivo | Descripción Técnica |
| :--- | :--- |
| `app.py` | Aplicación principal en Streamlit con el lanzador de plataformas web, selector multi-repositorio y compilador `.txt` en memoria. |
| `requirements.txt` | Dependencias del entorno para despliegue en Streamlit Cloud. |

```bash
git clone [https://github.com/mauriciovargas1516-ux/github-context-extractor.git](https://github.com/mauriciovargas1516-ux/github-context-extractor.git)
cd github-context-extractor
pip install -r requirements.txt
streamlit run app.py
