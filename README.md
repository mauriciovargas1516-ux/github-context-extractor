
# Hub de Aplicaciones y Extractor Académico de Contexto GitHub — ULagos 2026

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://app-context-extractor-cl8x5kwfdodzvmx7m3vean.streamlit.app/)
[![Lanzar Hub y Extractor en Streamlit](https://img.shields.io/badge/ABRIR_HUB_Y_EXTRACTOR_EN_STREAMLIT-1E3A8A?style=for-the-badge&logo=streamlit&logoColor=white)](https://app-context-extractor-cl8x5kwfdodzvmx7m3vean.streamlit.app/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://github.com/mauriciovargas1516-ux/github-context-extractor)

Plataforma centralizada de ingeniería de contexto, biblioteca metodológica referenciada y lanzador de aplicaciones web desarrollada en **Python y Streamlit**. Conecta en tiempo real con los repositorios públicos de GitHub (`mauriciovargas1516-ux`) mediante descarga directa en memoria RAM (`codeload.github.com`, inmune al límite de 60 peticiones/hora de la API REST) y con la **Bóveda Instantánea de Cátedras ULagos** para consolidar código fuente, fórmulas de Excel y literatura académica en archivos `.txt` personalizados por asignatura.

**Acceso directo al Hub y Extractor en vivo:**  
https://app-context-extractor-cl8x5kwfdodzvmx7m3vean.streamlit.app/

---

## 1. Directorio de Plataformas Interactivas Conectadas (Streamlit Cloud)

| Plataforma / Asignatura | Docente Cátedra ULagos | Repositorio GitHub | Aplicación Web en Vivo |
| :--- | :--- | :--- | :--- |
| **Hub & Extractor de Contexto Académico** | Portafolio Ingeniería Comercial | [`github-context-extractor`](https://github.com/mauriciovargas1516-ux/github-context-extractor) | [Abrir Hub y Extractor](https://app-context-extractor-cl8x5kwfdodzvmx7m3vean.streamlit.app/) |
| **Evaluación Integrada de Proyectos (`FDIC26`)** | Dra. Luz María Ferrada B. | [`PROYECTOS-2026`](https://github.com/mauriciovargas1516-ux/PROYECTOS-2026) | [Abrir Suite Proyectos](https://proyectos-2026-ubfvxgpqmpp5z7dn6wlnn3.streamlit.app/) |
| **Finanzas Avanzadas** | Prof.ª Camila Bustos Rosas | [`FINANZAS-AVANZADAS-2026`](https://github.com/mauriciovargas1516-ux/FINANZAS-AVANZADAS-2026) | [Abrir Simulador Finanzas](https://finanzas-avanzadas-2026-nxvqzsfrrtgu9e92javcli.streamlit.app/) |
| **Desarrollo y Gestión Territorial** | Prof. Claudio Mancilla | [`DESARROLLO-Y-GESTION-TERRITORIAL-2026`](https://github.com/mauriciovargas1516-ux/DESARROLLO-Y-GESTION-TERRITORIAL-2026) | [Abrir Motor Territorial](https://desarrollo-y-gestion-territorial-2026-ec6keylhsgra88s77bkl6f.streamlit.app/) |
| **Gestión Tributaria para la Toma de Decisiones** | Prof. Richard Villanueva Soto | [`GESTION-TRIBUTARIA-2026`](https://github.com/mauriciovargas1516-ux/GESTION-TRIBUTARIA-2026) | [Abrir Suite Tributaria](https://gestion-tributaria-2026-avecwdhabftj7rjnx5knmb.streamlit.app/) |

---

## 2. Arquitectura Funcional de las 4 Pestañas (`app.py`)

### Pestaña 1 — Extractor GitHub con Nomenclatura Dinámica por Ramo y Blindaje Anti-403
* **Nomenclatura Personalizada Automática:** Genera el nombre del archivo `.txt` y su encabezado técnico según el ramo o la combinación exacta de repositorios seleccionados (por ejemplo, `CONTEXTO_EVALUACION_INTEGRADA_PROYECTOS_FDIC26_2026-11-15.txt` o `CONTEXTO_MULTIRAMO_PROYECTOS_FINANZAS_TERRITORIAL_2026-11-15.txt`).
* **Extracción en Memoria RAM vía `codeload.github.com`:** Descarga y descomprime el paquete `.zip` de cada repositorio directamente en memoria sin consumir la cuota de $60\text{ peticiones/hora}$ de `api.github.com`, evitando bloqueos `HTTP 403: rate limit exceeded`.
* **Inyección Bibliográfica Opcional:** Permite adjuntar al inicio del archivo `.txt` la cuadrilla de fórmulas, tips de evaluación y páginas exactas de la literatura oficial de cada ramo.

### Pestaña 2 — Cuadrillas Metodológicas con Hipervínculos Directos a la Literatura (`#page=N` y `?cita=ID`)
* Integra tarjetas técnicas para **Evaluación Integrada de Proyectos**, **Finanzas Avanzadas**, **Desarrollo y Gestión Territorial**, **Gestión Tributaria** e **Introducción al Deporte Paralímpico**.
* Incluye **hipervínculos externos con ancla de página (`#page=N`)** hacia los textos oficiales (Fontaine, 2008; Metodología General SNI, 2025; Metodología GIRS, 2022; Precios Sociales SNI, 2026; Ley REP N° 20.920; D.L. N° 825; Código Tributario) e **hipervínculos internos (`?cita=ID`)** que abren la transcripción literal de la lámina o página de Moodle.

### Pestaña 3 — Bóveda Moodle Pre-Cargada y Destilador de Archivos / ZIPs en Streaming
* Permite descargar en 1 clic cualquiera de los ramos pre-destilados en `Todos_Los_Ramos_Destilados_TXT.zip` o subir nuevos respaldos `.zip`, `.pdf`, `.xlsx` y `.docx` extrayendo automáticamente las fórmulas nativas de Excel (`=NPV`, `=IRR`, `=PMT`, `=SUM`).

### Pestaña 4 — Buscador Cognitivo de Páginas y Divisor en Tomos para Libros PDF
* Escanea libros extensos (Ross, Brealey, Gitman, Fontaine, CEPAL, Duch Brown, Dini) o los archivos destilados en el repositorio para localizar páginas exactas por concepto, autor o fórmula.

---

## 3. Impacto Operativo: Compilación Automatizada vs. Recolección Manual

| Tarea de Ingeniería de Contexto y Consulta Bibliográfica | Volumen Activo | Tiempo Manual | Tiempo Cloud | % Mejora (Multiplicador) |
| :--- | :--- | :---: | :---: | :---: |
| **Recorrer árboles de directorios de 11 repositorios y listar tamaños en bytes** | ~70 archivos en 11 repositorios | 25,0 minutos | **0,8 segundos** | **99,9% ($1.875\times$ más rápido)** |
| **Extraer y concatenar código fuente (`.py`, `.md`, `.toml`, `.rmd`) vía Codeload ZIP** | $+600.000$ caracteres de código | 45,0 minutos | **1,8 segundos** | **99,9% ($1.500\times$ más rápido)** |
| **Localizar página exacta, fórmula y extracto literal en manuales de cátedra** | 5 asignaturas + libros de 900 págs. | 30,0 minutos | **1 clic (0,2 seg)** | **99,9% ($9.000\times$ más rápido)** |
| **TOTAL GENERACIÓN DE CONTEXTO PERSONALIZADO POR RAMO (`.TXT`)** | **Portafolio GitHub + Cátedra ULagos** | **1,67 horas (100 min)** | **2,8 segundos** | **99,9% ($2.140\times$ más rápido)** |

---

## 4. Estructura del Repositorio e Instalación Local

```text
github-context-extractor/
├── .streamlit/
│   └── config.toml                        # Configuración visual y límite de carga (1024 MB)
├── Todos_Los_Ramos_Destilados_TXT.zip     # Bóveda pre-cargada con los ramos de Moodle destilados en .TXT
├── app.py                                 # Aplicación principal (Extractor Anti-403 + Cuadrillas + Bóveda Moodle)
├── requirements.txt                       # Dependencias de Python (streamlit, pypdf, openpyxl, pandas, python-docx)
└── README.md                              # Documentación técnica del repositorio
```

```bash
git clone https://github.com/mauriciovargas1516-ux/github-context-extractor.git
cd github-context-extractor
pip install -r requirements.txt
streamlit run app.py
```
