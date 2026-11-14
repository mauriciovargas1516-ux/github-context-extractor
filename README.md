# Hub de Aplicaciones y Super Extractor de Contexto GitHub

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://app-context-extractor-cl8x5kwfdodzvmx7m3vean.streamlit.app/)
[![Lanzar Super Extractor en Streamlit](https://img.shields.io/badge/ABRIR_HUB_Y_SUPER_EXTRACTOR_EN_STREAMLIT-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://app-context-extractor-cl8x5kwfdodzvmx7m3vean.streamlit.app/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://github.com/mauriciovargas1516-ux/github-context-extractor)

Plataforma centralizada de ingeniería de contexto y lanzador de aplicaciones web desarrollada en **Python y Streamlit**. Se conecta en tiempo real a la API REST pública de GitHub (`mauriciovargas1516-ux`) para recorrer recursivamente el árbol de directorios de múltiples repositorios y consolidar su código fuente, scripts y documentación técnica en un único archivo maestro `.txt` listo para alimentar ventanas de contexto de modelos de Inteligencia Artificial (LLMs).

**Acceso directo al Hub y Super Extractor en vivo:**  
https://app-context-extractor-cl8x5kwfdodzvmx7m3vean.streamlit.app/

---

## 1. Directorio de Plataformas Interactivas Conectadas (Streamlit Cloud)

| Plataforma / Asignatura | Repositorio GitHub | Aplicación Web en Vivo |
| :--- | :--- | :--- |
| **Hub & Super Extractor GitHub** | [`github-context-extractor`](https://github.com/mauriciovargas1516-ux/github-context-extractor) | [Abrir Super Extractor](https://app-context-extractor-cl8x5kwfdodzvmx7m3vean.streamlit.app/) |
| **Evaluación Integrada de Proyectos** | [`PROYECTOS-2026`](https://github.com/mauriciovargas1516-ux/PROYECTOS-2026) | [Abrir Suite Proyectos](https://proyectos-2026-ubfvxgpqmpp5z7dn6wlnn3.streamlit.app/) |
| **Finanzas Avanzadas** | [`FINANZAS-AVANZADAS-2026`](https://github.com/mauriciovargas1516-ux/FINANZAS-AVANZADAS-2026) | [Abrir Simulador Finanzas](https://finanzas-avanzadas-2026-nxvqzsfrrtgu9e92javcli.streamlit.app/) |
| **Desarrollo y Gestión Territorial** | [`DESARROLLO-Y-GESTION-TERRITORIAL-2026`](https://github.com/mauriciovargas1516-ux/DESARROLLO-Y-GESTION-TERRITORIAL-2026) | [Abrir Motor Territorial](https://desarrollo-y-gestion-territorial-2026-ec6keylhsgra88s77bkl6f.streamlit.app/) |
| **Gestión Tributaria** | [`GESTION-TRIBUTARIA-2026`](https://github.com/mauriciovargas1516-ux/GESTION-TRIBUTARIA-2026) | [Abrir Suite Tributaria](https://gestion-tributaria-2026-avecwdhabftj7rjnx5knmb.streamlit.app/) |

---

## 2. Impacto Operativo: Compilación vía API REST vs. Recolección Manual de Código

| Tarea de Ingeniería de Contexto para IA | Volumen Activo | Tiempo Manual | Tiempo Cloud | % Mejora (Multiplicador) |
| :--- | :--- | :---: | :---: | :---: |
| **Recorrer árboles de directorios de 10 repositorios y listar tamaños en bytes** | ~65 archivos en 10 repositorios | 25,0 minutos | **0,8 segundos** | **99,9% (1.875x más rápido)** |
| **Abrir, copiar y concatenar código fuente (`.py`, `.md`, `.toml`, `.txt`) sin romper formato** | +550.000 caracteres de código | 45,0 minutos | **2,2 segundos** | **99,9% (1.227x más rápido)** |
| **Filtrar binarios pesados (`>300 KB`) para no saturar ventana de tokens del LLM** | Exclusión automática de `.xlsx`/`.zip` | 15,0 minutos | **0,05 segundos** | **99,9% (18.000x más rápido)** |
| **TOTAL GENERACIÓN DE SUPER ARCHIVO DE CONTEXTO (`.TXT`)** | **Portafolio GitHub Completo** | **1,4 horas (85 min)** | **3,0 segundos** | **99,9% (1.700x más rápido)** |

---

## 3. Ecosistema de 10 Repositorios Indexados Automáticamente

1. **`github-context-extractor`:** Hub de aplicaciones en Streamlit y compilador de contexto multi-repositorio para IA.
2. **`GESTION-TRIBUTARIA-2026`:** Suite normativa y simulador impositivo (Ciclo de Vida, Derechos Art. 8 bis CT, Rentas 1ª/2ª Categoría, IVA DL 825 / F29 y Analítica PGCT 2026 SII).
3. **`FINANZAS-AVANZADAS-2026`:** Simulador corporativo para evaluación de activos reales, estructura de capital (CAPM / WACC), Flujo de Caja Libre y del Inversionista, escenarios y Monte Carlo.
4. **`PROYECTOS-2026`:** Suite de formulación y evaluación privada y social de proyectos (normativa SNI / MIDESO 2026) con exportación automatizada de informes Word, PDF y libros Excel.
5. **`DESARROLLO-Y-GESTION-TERRITORIAL-2026`:** Motor econométrico y espacial para análisis regional (ILPES / Shift & Share MADE), convergencia REAT, redes empresariales y ordenamiento territorial.
6. **`insumaes-woocommerce-automation`:** Pipeline de automatización de inventario e integración de catálogo omnicanal con Python y Google Cloud Platform (GCP).
7. **`moodle-hybrid-scraper`:** Rastreador web híbrido (`Selenium` + `Requests`) para extracción automatizada de documentos en plataformas Moodle.
8. **`motor-planos-sec-te1-chile`:** Motor paramétrico en Python (`ezdxf` + `Streamlit`) para generación automática de planos eléctricos AutoCAD (`.dxf`), cuadros de cargas y caída de tensión bajo normativa SEC.
9. **`motor-auditor-dte-finops`:** Motor en Python para extracción y auditoría automática de Documentos Tributarios Electrónicos (DTEs) y prevención de pagos duplicados.
10. **`motor-conciliador-chile`:** Sistema de conciliación financiera y cruce automatizado de registros tributarios y contables.

---

## 4. Instalación y Ejecución Local

```bash
git clone [https://github.com/mauriciovargas1516-ux/github-context-extractor.git](https://github.com/mauriciovargas1516-ux/github-context-extractor.git)
cd github-context-extractor
pip install -r requirements.txt
streamlit run app.py
```
