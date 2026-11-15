
# Super Hub Académico y Central de Mando Multi-Repositorio — ULagos 2026

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://app-context-extractor-cl8x5kwfdodzvmx7m3vean.streamlit.app/)
[![Lanzar Super Hub en Streamlit](https://img.shields.io/badge/ABRIR_SUPER_HUB_Y_CENTRAL_DE_MANDO-1E3A8A?style=for-the-badge&logo=streamlit&logoColor=white)](https://app-context-extractor-cl8x5kwfdodzvmx7m3vean.streamlit.app/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://github.com/mauriciovargas1516-ux/github-context-extractor)

Plataforma centralizada de **ingeniería de contexto**, **gestión remota multi-repositorio (GitHub CMS)** y **consulta bibliográfica conectada a Google Drive API** desarrollada en **Python y Streamlit** por **Mauricio Alejandro Vargas Ortega** (Ingeniería Comercial, Universidad de Los Lagos — Osorno, Chile).

Permite compilar el código completo de todo tu portafolio en segundos, visualizar páginas exactas de PDFs alojados dentro de respaldos `.zip` en Google Drive mediante extracción quirúrgica **HTTP Byte-Range**, y administrar en lote `About`, `Topics`, `requirements.txt`, `README.md`, `.streamlit/config.toml` y archivos de todos tus repositorios sin abrirlos uno por uno en GitHub.

**Acceso directo a la aplicación en vivo:**  
https://app-context-extractor-cl8x5kwfdodzvmx7m3vean.streamlit.app/

---

## 1. Tutorial Rápido de Uso (Paso a Paso)

### Paso 0 — Modo Público vs. Modo Admin
La aplicación funciona en dos niveles de acceso:

* **Modo Público (sin clave):** Cualquier visitante puede usar las **Pestañas 1 a 4** (extraer repositorios públicos, consultar cuadrillas metodológicas, abrir PDFs en Drive y descargar la bóveda destilada). La Pestaña 5 queda bloqueada en solo lectura.
* **Modo Admin (con clave en la barra lateral):**
  1. Abre la barra lateral izquierda (**Acceso Central de Mando**).
  2. Ingresa tu **Clave Admin** (`ADMIN_PASSWORD`).
  3. El servidor valida tu clave con comparación segura (`hmac.compare_digest`) y activa internamente `GITHUB_TOKEN` **sin enviar jamás el token al navegador**.
  4. Al desbloquearse, verás la confirmación verde **Modo Admin activo**, se incluirán tus repositorios privados en la Pestaña 1 y se habilitará la escritura remota en la Pestaña 5.

---

### Pestaña 1 — Super Extractor GitHub (`extractor_github_avanzado.py`)
Compila uno, varios o todos tus repositorios en memoria RAM vía `codeload.github.com` (inmune al límite de 60 peticiones/hora de la API pública).

**Cómo elegir el nivel de captura según lo que necesites:**

| Nivel de Captura | Qué incluye | Cuándo usarlo |
| :--- | :--- | :--- |
| **1. SUPER EXTRACTOR TOTAL** | Todo el código fuente, configs (`.gitignore`, `packages.txt`, `.ipynb` limpio sin base64) y metadatos en un solo archivo. | Para respaldo integral o para cargar todo tu portafolio en herramientas de ventana amplia (como NotebookLM). |
| **2. Código Limpio** | Todo el código completo, pero recorta automáticamente archivos de datos pesados (`.csv`, `.json`, `.txt` > 15 KB) a las primeras 40 líneas. | Para depurar o programar en profundidad entre **1 y 3 repositorios** sin llenar el contexto con datos crudos. |
| **3. Mapa Arquitectónico (AST)** | `About`, `Topics`, `README.md`, `requirements.txt`, `config.toml`, árbol de archivos y únicamente imports, clases y funciones (`def` / `class`) de cada `.py`. | Para auditar **los 11+ repositorios juntos en un solo chat de IA** sin que el archivo se corte por tamaño. |
| **4. Solo Auditoría CMS** | Únicamente `About`, `Topics`, `README.md`, `requirements.txt` y `config.toml`. | Para revisar documentación y dependencias antes de editarlas en lote desde la Pestaña 5. |

**Opciones extra y descargas:**
* **Modo Mega-Contexto:** Activa la casilla opcional para anexar al final del `.txt` la Bóveda Moodle destilada del servidor.
* **Tabla de peso y tokens:** Tras compilar, revisa el tamaño en KB, los tokens estimados y el archivo de entrada (`app.py` / `consola_web.py`) detectado en cada repo.
* **3 botones de descarga simultáneos:**
  1. **Todo en 1 `.TXT`:** Archivo maestro unificado.
  2. **`.ZIP` (1 `.TXT` por Repo):** Un archivo independiente por cada repositorio + índice maestro.
  3. **`.ZIP` en Tomos (~350 KB):** Divide automáticamente la extracción en tomos equilibrados para subir por partes si una IA limita el peso por archivo.

---

### Pestaña 2 y 3 — Cuadrillas Metodológicas y Explorador Quirúrgico de Google Drive
* **Pestaña 2 (Cuadrillas y Visor PDF):** Reúne fórmulas en LaTeX, tips de evaluación y referencias exactas por asignatura. Al pulsar el botón verde de cualquier tarjeta (`Abrir PDF desde Google Drive en Pág. N`), el motor extrae vía **HTTP Byte-Range** únicamente los bytes de ese PDF desde dentro del `.zip` en Google Drive (sin descargar el respaldo completo), recorta las páginas solicitadas y las dibuja en pantalla con **Mozilla PDF.js** (con zoom y apertura en pestaña nueva).
* **Pestaña 3 (Explorador `.ZIP` en Drive):** Lista el contenido completo de tus archivos `.zip` en Google Drive leyendo solo los últimos KB de cabecera, permite filtrar por carpeta/ramo, previsualizar PDFs u hojas de Excel (`.xlsx`) y descargar cualquier documento individual.

---

### Pestaña 4 — Bóveda Destilada en 1 Clic
Lee automáticamente el archivo maestro `.txt` o el paquete `Todos_Los_Ramos_Destilados_TXT.zip` alojado en el repositorio, genera un botón de descarga por asignatura y ofrece un buscador rápido por autor, fórmula o página.

---

### Pestaña 5 — Super Central de Mando (`central_mando_github.py`)
Consola de administración remota conectada a la API REST de GitHub para aplicar cambios en uno o múltiples repositorios a la vez (requiere **Modo Admin**).

**Recetas prácticas de uso diario:**

1. **Corregir un `ModuleNotFoundError` en Streamlit Cloud (10 segundos):**
   * Ve a **5.2 `requirements.txt` y Config**.
   * Elige el repositorio afectado (o varios a la vez).
   * Marca la librería faltante (por ejemplo `beautifulsoup4`, `pypdf` u `openpyxl`) o escríbela en el campo de librerías adicionales.
   * Pulsa **APLICAR CAMBIOS EN `requirements.txt` (LOTE)**. El sistema agrega solo lo que falta sin duplicar líneas y Streamlit Cloud reinicia la app automáticamente.

2. **Completar descripciones (`About`), links y `Topics` en lote:**
   * Ve a **5.1 About, URL y Topics**.
   * La tabla superior muestra en vivo qué repositorios tienen campos vacíos.
   * Usa **SINCRONIZAR ABOUT EN LOTE** para rellenar varios de una sola vez desde el catálogo, o edita un repositorio específico en el panel derecho y pulsa **GUARDAR ABOUT**.

3. **Unificar botones `Open in Streamlit` o editar un `README.md`:**
   * Ve a **5.3 README.md y Badges**.
   * En la columna izquierda, selecciona tus apps desplegadas y pulsa **INYECTAR BADGE STREAMLIT EN LOTE** (inserta o actualiza el botón usando la URL del `Homepage` sin borrar el resto del `README.md`).
   * En la columna derecha, carga el `README.md` actual de cualquier repo, edítalo o genera una plantilla base y guárdalo directo en GitHub.

4. **Editar código en vivo o distribuir un archivo a todos los repos (Broadcast):**
   * Ve a **5.4 Editor y Envío Masivo de Archivos**.
   * **Modo Individual:** Selecciona repo + archivo (detecta automáticamente `app.py` o `consola_web.py`), edita y guarda con tu mensaje de commit.
   * **Modo Masivo:** Ideal para desplegar un `.gitignore` común (protegiendo `.env` y `.streamlit/secrets.toml`), un `packages.txt` o un módulo compartido en múltiples repositorios con un solo clic.

5. **Estandarizar tema visual claro (`.streamlit/config.toml`):**
   * Ve a **5.2 `requirements.txt` y Config** (columna derecha), selecciona las apps destino y pulsa **INYECTAR `.streamlit/config.toml` EN LOTE**.
   * *Nota:* Excluye `github-context-extractor` si deseas mantener intacta su configuración `maxUploadSize = 1024`.

6. **Conectar o desacoplar el Puente en Vivo hacia Google Drive (`5.5`):**
   * Selecciona las apps destino y pulsa **INYECTAR / ACTUALIZAR PUENTE EN LOTE**. El inyector detecta automáticamente si la app usa `app.py` o `consola_web.py`, agrega el bloque al final entre marcadores sin tocar tu código original y asegura las dependencias requeridas.
   * Para revertirlo limpiamente en cualquier momento, pulsa **Desacoplar Puente y Restaurar Archivo Original**.
   * *Requisito:* Cada app hija donde actives el visor de Drive debe tener configurado `gcp_service_account_json` en sus **Secrets** de Streamlit Cloud.

---

## 2. Ecosistema de Repositorios Conectados

### Plataformas de Cátedra ULagos 2026

| Asignatura / Plataforma | Docente | Repositorio | Entrypoint | App en Vivo |
| :--- | :--- | :--- | :--- | :--- |
| **Super Hub & Central de Mando** | Portafolio Ing. Comercial | [`github-context-extractor`](https://github.com/mauriciovargas1516-ux/github-context-extractor) | `app.py` | [Abrir App](https://app-context-extractor-cl8x5kwfdodzvmx7m3vean.streamlit.app/) |
| **Evaluación Integrada de Proyectos (FDIC26)** | Dra. Luz María Ferrada B. | [`PROYECTOS-2026`](https://github.com/mauriciovargas1516-ux/PROYECTOS-2026) | `consola_web.py` | [Abrir App](https://app-context-extractor-cl8x5kwfdodzvmx7m3vean.streamlit.app/) |
| **Desarrollo y Gestión Territorial** | Prof. Claudio Mancilla | [`DESARROLLO-Y-GESTION-TERRITORIAL-2026`](https://github.com/mauriciovargas1516-ux/DESARROLLO-Y-GESTION-TERRITORIAL-2026) | `app.py` | [Abrir App](https://app-context-extractor-cl8x5kwfdodzvmx7m3vean.streamlit.app/) |
| **Finanzas Avanzadas** | Prof.ª Camila Bustos Rosas | [`FINANZAS-AVANZADAS-2026`](https://github.com/mauriciovargas1516-ux/FINANZAS-AVANZADAS-2026) | `app.py` | [Abrir App](https://app-context-extractor-cl8x5kwfdodzvmx7m3vean.streamlit.app/) |
| **Gestión Tributaria para la Toma de Decisiones** | Prof. Richard Villanueva Soto | [`GESTION-TRIBUTARIA-2026`](https://github.com/mauriciovargas1516-ux/GESTION-TRIBUTARIA-2026) | `app.py` | [Abrir App](https://app-context-extractor-cl8x5kwfdodzvmx7m3vean.streamlit.app/) |
| **Sincronizador ULagos Virtual** | Automatización Moodle | [`moodle-hybrid-scraper`](https://github.com/mauriciovargas1516-ux/moodle-hybrid-scraper) | `scraper_moodle.py` | — |

### Proyectos Comerciales, FinOps e Ingeniería

| Repositorio | Enfoque |
| :--- | :--- |
| [`mauriciovargas1516-ux`](https://github.com/mauriciovargas1516-ux/mauriciovargas1516-ux) | Perfil principal de GitHub y presentación del portafolio técnico. |
| [`insumaes-woocommerce-automation`](https://github.com/mauriciovargas1516-ux/insumaes-woocommerce-automation) | Pipeline de automatización de inventario y catálogo WooCommerce con Python y GCP. |
| [`motor-planos-sec-te1-chile`](https://github.com/mauriciovargas1516-ux/motor-planos-sec-te1-chile) | Motor paramétrico (`ezdxf` + Streamlit) para planos eléctricos AutoCAD `.dxf` y cálculos SEC TE1. |
| [`motor-auditor-dte-finops`](https://github.com/mauriciovargas1516-ux/motor-auditor-dte-finops) | Extracción y auditoría automática de DTEs y prevención de pagos duplicados. |
| [`motor-conciliador-chile`](https://github.com/mauriciovargas1516-ux/motor-conciliador-chile) | Cruce y conciliación automatizada de cartolas bancarias y documentos tributarios. |

---

## 3. Configuración de Seguridad y Secrets (Streamlit Cloud)

Las credenciales **nunca** se guardan en el código fuente ni se envían al navegador del usuario. Para desplegar una instancia propia o mantener esta aplicación, configura las siguientes claves en **Streamlit Cloud → Manage app → Settings → Secrets** (o en `.streamlit/secrets.toml` para ejecución local):

```toml
# Token Personal de GitHub (Classic con permiso únicamente en 'repo'; NO marcar 'delete_repo')
GITHUB_TOKEN = "ghp_TU_TOKEN_DE_GITHUB"

# Contraseña personal para desbloquear el Modo Admin en la barra lateral
ADMIN_PASSWORD = "TuClaveSecretaDeAdmin"

# JSON de la Service Account de Google Cloud con acceso de lectura a los archivos compartidos en Drive
gcp_service_account_json = '''
{
  "type": "service_account",
  "project_id": "tu-proyecto-gcp",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "tu-service-account@tu-proyecto-gcp.iam.gserviceaccount.com",
  "client_id": "...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token"
}
'''
```

---

## 4. Arquitectura del Repositorio e Instalación Local

```text
github-context-extractor/
├── .streamlit/
│   └── config.toml                        # Configuración visual y límite de carga (1024 MB)
├── app.py                                 # Orquestador principal, seguridad, Visor PDF.js, Drive HTTP Range y Puente Remoto
├── extractor_github_avanzado.py           # Pestaña 1: Super Extractor (4 modos, AST, repos privados, ZIP y Tomos)
├── central_mando_github.py                # Pestaña 5: CMS remoto multi-repositorio (About, requirements, README, Broadcast y Puente)
├── Todos_Los_Ramos_Destilados_TXT.zip     # Bóveda pre-cargada con los ramos de Moodle destilados en .TXT
├── requirements.txt                       # Dependencias Python (streamlit, requests, pandas, pypdf, google-auth, openpyxl, etc.)
├── packages.txt                           # Dependencias de sistema Linux
└── README.md                              # Documentación y tutorial de uso
```

```bash
git clone https://github.com/mauriciovargas1516-ux/github-context-extractor.git
cd github-context-extractor
pip install -r requirements.txt
streamlit run app.py
```
