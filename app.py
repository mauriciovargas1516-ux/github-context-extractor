# -*- coding: utf-8 -*-
"""
HUB DE APLICACIONES Y SUPER EXTRACTOR DE CONTEXTO (GITHUB + MOODLE ULAGOS + LIBROS)
Repositorio: github-context-extractor
Autor: Mauricio Alejandro Vargas Ortega — Ingeniería Comercial ULagos
"""

import io
import json
import os
import urllib.parse
import urllib.request
import zipfile

import openpyxl
import pandas as pd
import streamlit as st
from docx import Document
from pypdf import PdfReader

st.set_page_config(
    page_title="Hub de Aplicaciones y Extractor de Contexto (GitHub + Moodle) - Mauricio Vargas",
    layout="wide",
)

# Estilo corporativo limpio
st.markdown(
    """
    <style>
    .block-container {padding-top: 1.5rem !important; max-width: 1280px !important;}
    .corp-banner {
        background: linear-gradient(90deg, #0F172A 0%, #1E3A8A 100%);
        color: #FFFFFF;
        padding: 18px 24px;
        border-radius: 6px;
        margin-bottom: 18px;
        border-left: 5px solid #38BDF8;
    }
    .corp-title {font-size: 22px; font-weight: 700; margin: 0; letter-spacing: 0.3px;}
    .corp-sub {font-size: 13px; color: #CBD5E1; margin-top: 4px;}
    .sec-header {
        background-color: #F1F5F9;
        color: #0F172A;
        padding: 8px 14px;
        font-weight: 700;
        font-size: 14px;
        border-radius: 4px;
        border-left: 4px solid #1E3A8A;
        margin-top: 10px;
        margin-bottom: 12px;
    }
    </style>
    <div class="corp-banner">
        <div class="corp-title">HUB DE APLICACIONES Y SUPER EXTRACTOR DE CONTEXTO (GITHUB + MOODLE ULAGOS)</div>
        <div class="corp-sub">Conectado en tiempo real a la API de GitHub y Destilador Inteligente de Cátedras, Excels y Libros PDF para IA</div>
    </div>
    """,
    unsafe_allow_html=True,
)

USUARIO = "mauriciovargas1516-ux"
EXTENSIONES_GIT = (".py", ".md", ".txt", ".rmd", ".toml", ".json")
EXTENSIONES_IGNORADAS_MOODLE = (".mp4", ".avi", ".mov", ".mkv", ".exe", ".png", ".jpg", ".jpeg")

APPS_STREAMLIT = {
    "PROYECTOS-2026": "https://proyectos-2026-ubfvxgpqmpp5z7dn6wlnn3.streamlit.app/",
    "FINANZAS-AVANZADAS-2026": "https://finanzas-avanzadas-2026-nxvqzsfrrtgu9e92javcli.streamlit.app/",
    "DESARROLLO-Y-GESTION-TERRITORIAL-2026": "https://desarrollo-y-gestion-territorial-2026-ec6keylhsgra88s77bkl6f.streamlit.app/",
    "GESTION-TRIBUTARIA-2026": "https://gestion-tributaria-2026-avecwdhabftj7rjnx5knmb.streamlit.app/",
}


# ==============================================================================
# FUNCIONES DEL EXTRACTOR DE GITHUB (PESTAÑA 1)
# ==============================================================================
@st.cache_data(ttl=300)
def obtener_repositorios(usuario):
    url = f"https://api.github.com/users/{usuario}/repos?per_page=100&sort=updated"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def compilar_contexto_txt(usuario, repos_seleccionados, lista_repos):
    bloques = [
        "=" * 90,
        f"SUPER EXTRACCIÓN EN VIVO DE PORTAFOLIO GITHUB: {usuario}",
        "=" * 90,
        "",
    ]
    for r in lista_repos:
        nombre = r["name"]
        if nombre not in repos_seleccionados:
            continue
        rama = r.get("default_branch", "main")
        bloques.append(f"### REPOSITORIO: {nombre}")
        bloques.append(f"Descripción: {r.get('description') or 'Sin descripción'}")
        bloques.append(f"URL GitHub: {r['html_url']}")
        if nombre in APPS_STREAMLIT:
            bloques.append(f"App Streamlit en Vivo: {APPS_STREAMLIT[nombre]}")
        bloques.append("-" * 90)

        try:
            url_tree = f"https://api.github.com/repos/{usuario}/{nombre}/git/trees/{rama}?recursive=1"
            req_t = urllib.request.Request(url_tree, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req_t) as resp_t:
                tree = json.loads(resp_t.read().decode("utf-8")).get("tree", [])

            bloques.append("#### INVENTARIO DE ARCHIVOS:")
            for item in tree:
                if item["type"] == "blob":
                    bloques.append(f"  - {item['path']} ({item.get('size', 0)} bytes)")
            bloques.append("")

            for item in tree:
                ruta = item["path"]
                if item["type"] == "blob" and ruta.lower().endswith(EXTENSIONES_GIT) and item.get("size", 0) <= 300_000:
                    url_raw = f"https://raw.githubusercontent.com/{usuario}/{nombre}/{rama}/{urllib.parse.quote(ruta)}"
                    req_r = urllib.request.Request(url_raw, headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(req_r) as resp_r:
                        codigo = resp_r.read().decode("utf-8", errors="replace")
                    bloques.append(f"#### ARCHIVO: {nombre}/{ruta}")
                    bloques.append("-" * 70)
                    bloques.append(codigo)
                    bloques.append("")
        except Exception as e:
            bloques.append(f"[Error leyendo {nombre}: {e}]")
        bloques.append("=" * 90 + "\n")

    return "\n".join(bloques)


# ==============================================================================
# FUNCIONES DEL DESTILADOR DE MOODLE Y LIBROS PDF (PESTAÑAS 2 Y 3)
# ==============================================================================
def leer_paginas_pdf_bytes(data_bytes: bytes, nombre_archivo: str) -> list:
    """Retorna lista de tuplas [(numero_pagina, texto_pagina), ...] desde un PDF."""
    try:
        lector = PdfReader(io.BytesIO(data_bytes))
        paginas = []
        for idx, pag in enumerate(lector.pages, start=1):
            txt = (pag.extract_text() or "").strip()
            if txt:
                paginas.append((idx, txt))
        return paginas if paginas else [(1, f"[PDF sin texto seleccionable: {nombre_archivo}]")]
    except Exception as e:
        return [(1, f"[Error leyendo PDF {nombre_archivo}: {e}]")]


def extraer_excel_con_formulas(data_bytes: bytes, nombre_archivo: str) -> str:
    """Extrae valores y fórmulas nativas (=SUM, =VNA, =TIR, etc.) de archivos Excel."""
    salida = []
    if nombre_archivo.lower().endswith(".xlsx"):
        try:
            wb_val = openpyxl.load_workbook(io.BytesIO(data_bytes), data_only=True)
            wb_for = openpyxl.load_workbook(io.BytesIO(data_bytes), data_only=False)
            for hoja in wb_val.sheetnames:
                ws_v = wb_val[hoja]
                ws_f = wb_for[hoja]
                salida.append(f"### Hoja Excel: {hoja} ({ws_v.max_row} filas x {ws_v.max_column} columnas)")
                max_r = min(ws_v.max_row, 120)
                max_c = min(ws_v.max_column, 20)
                for r in range(1, max_r + 1):
                    celdas = []
                    tiene_dato = False
                    for c in range(1, max_c + 1):
                        v = ws_v.cell(r, c).value
                        f = ws_f.cell(r, c).value
                        if v is not None or f is not None:
                            tiene_dato = True
                        if isinstance(f, str) and f.startswith("="):
                            celdas.append(f"{v} [fx: {f}]")
                        else:
                            celdas.append("" if v is None else str(v))
                    if tiene_dato:
                        salida.append(" | ".join(celdas))
                salida.append("")
            return "\n".join(salida)
        except Exception:
            pass

    try:
        xl = pd.ExcelFile(io.BytesIO(data_bytes))
        for h in xl.sheet_names:
            df = xl.parse(h).head(100)
            salida.append(f"### Hoja Excel: {h}\n{df.to_string(index=False)}\n")
        return "\n".join(salida)
    except Exception as e:
        return f"[No se pudo leer Excel {nombre_archivo}: {e}]"


def extraer_word_bytes(data_bytes: bytes, nombre_archivo: str) -> str:
    try:
        doc = Document(io.BytesIO(data_bytes))
        bloques = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        for idx_t, t in enumerate(doc.tables, start=1):
            bloques.append(f"\n[Tabla Word #{idx_t}]")
            for row in t.rows:
                bloques.append(" | ".join(c.text.strip().replace("\n", " ") for c in row.cells))
        return "\n".join(bloques)
    except Exception as e:
        return f"[Error leyendo Word {nombre_archivo}: {e}]"


def procesar_archivo_individual(nombre_arch: str, raw_bytes: bytes, modo_libros: str) -> str:
    """Convierte un archivo individual (PDF, Excel, Word, Rmd, TXT) en bloque de texto estructurado."""
    ext = os.path.splitext(nombre_arch)[1].lower()
    peso_mb = len(raw_bytes) / (1024.0 * 1024.0)

    if ext in EXTENSIONES_IGNORADAS_MOODLE:
        return f"### ARCHIVO MULTIMEDIA OMITIDO: {nombre_arch} ({peso_mb:.2f} MB)\n"

    encabezado = [
        f"### DOCUMENTO DE CÁTEDRA: {nombre_arch} ({peso_mb:.2f} MB)",
        "-" * 75,
    ]

    if ext == ".pdf":
        paginas = leer_paginas_pdf_bytes(raw_bytes, nombre_arch)
        n_pags = len(paginas)
        es_libro_grande = (peso_mb >= 4.0) or (n_pags >= 80)

        if es_libro_grande and "Índice" in modo_libros:
            encabezado.append(
                f"[LIBRO / MANUAL DE {n_pags} PÁGINAS DETECTADO — Mostrando las primeras 20 páginas (Índice y Marco General). "
                f"Usa la Pestaña 3 para extraer capítulos específicos o el libro completo en tomos.]"
            )
            for num_p, txt_p in paginas[:20]:
                encabezado.append(f"--- [{nombre_arch} | Página {num_p}] ---\n{txt_p}")
        else:
            for num_p, txt_p in paginas:
                encabezado.append(f"--- [{nombre_arch} | Página {num_p}] ---\n{txt_p}")

    elif ext in (".xlsx", ".xls"):
        encabezado.append(extraer_excel_con_formulas(raw_bytes, nombre_arch))
    elif ext == ".docx":
        encabezado.append(extraer_word_bytes(raw_bytes, nombre_arch))
    elif ext in (".txt", ".rmd", ".md", ".py", ".csv"):
        encabezado.append(raw_bytes.decode("utf-8", errors="replace"))
    else:
        encabezado.append(f"[Archivo {ext} registrado en inventario]")

    encabezado.append("\n" + "=" * 90 + "\n")
    return "\n".join(encabezado)


# ==============================================================================
# BARRA SUPERIOR DE ACCESO RÁPIDO A LAS 4 PLATAFORMAS
# ==============================================================================
st.markdown(
    "<div class='sec-header'>I. PLATAFORMAS INTERACTIVAS DESPLEGADAS EN STREAMLIT CLOUD</div>",
    unsafe_allow_html=True,
)
cols = st.columns(4)
for idx, (nombre_app, link_app) in enumerate(APPS_STREAMLIT.items()):
    with cols[idx % 4]:
        st.link_button(f"Abrir {nombre_app}", link_app, use_container_width=True)

st.divider()

# ==============================================================================
# NAVEGACIÓN POR PESTAÑAS DEL SUPER EXTRACTOR
# ==============================================================================
tab_git, tab_moodle, tab_libros = st.tabs([
    "1. Extractor de Código GitHub (API en Vivo)",
    "2. Destilador de Cátedras Moodle (PDFs + Excels con Fórmulas -> 1 .TXT)",
    "3. Destilador y Buscador en Libros Pesados (Ross, Gitman, Fontaine, CEPAL)",
])

# ------------------------------------------------------------------------------
# PESTAÑA 1: GITHUB API
# ------------------------------------------------------------------------------
with tab_git:
    repos = obtener_repositorios(USUARIO)
    nombres_todos = [r["name"] for r in repos]

    st.markdown(
        "<div class='sec-header'>EMPAQUETAR REPOSITORIOS DE GITHUB EN ARCHIVO MAESTRO (.TXT) PARA IA</div>",
        unsafe_allow_html=True,
    )
    seleccion = st.multiselect(
        "Repositorios incluidos en el archivo de contexto:",
        nombres_todos,
        default=nombres_todos,
    )

    if st.button("Generar Super Archivo de Contexto GitHub (.TXT)", type="primary"):
        with st.spinner("Extrayendo árbol de archivos y código fuente desde GitHub..."):
            texto_final = compilar_contexto_txt(USUARIO, seleccion, repos)
        st.success(f"Contexto compilado correctamente ({len(texto_final):,} caracteres de {len(seleccion)} repositorios).")
        st.download_button(
            label="Descargar SUPER_CONTEXTO_GITHUB_MAURICIO_2026.txt",
            data=texto_final,
            file_name="SUPER_CONTEXTO_GITHUB_MAURICIO_2026.txt",
            mime="text/plain",
            use_container_width=True,
        )
        with st.expander("Vista previa del archivo generado"):
            st.text(texto_final[:5000] + "\n\n... [Vista previa truncada] ...")

# ------------------------------------------------------------------------------
# PESTAÑA 2: DESTILADOR DE CÁTEDRAS MOODLE (ADIÓS A SUBIR DE 10 EN 10)
# ------------------------------------------------------------------------------
with tab_moodle:
    st.markdown(
        "<div class='sec-header'>CONVERTIR CARPETA DE MOODLE (APUNTES PDF, GUÍAS, EXCELS Y WORD) EN 1 SOLO ARCHIVO .TXT</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "Selecciona **todos los archivos PDF, Excel (`.xlsx`/`.xls`), Word (`.docx`) o RMarkdown (`.rmd`)** de una asignatura "
        "(o sube un archivo `.zip` sin los videos `.mp4`) y el motor generará **un único archivo `.txt`** con todo el contenido "
        "y las fórmulas ocultas de los Excels listo para subir a cualquier IA de una sola vez."
    )

    c_m1, c_m2 = st.columns([1.2, 1.8])
    with c_m1:
        nombre_ramo = st.selectbox(
            "Asignatura que estás empaquetando:",
            [
                "FINANZAS_AVANZADAS_2026",
                "TRIBUTARIA_2026",
                "PROYECTOS_2026",
                "TERRITORIAL_2026",
                "MARKETING_DIGITAL_2026",
                "OTRO_RAMO_ULAGOS",
            ],
        )
    with c_m2:
        modo_libros_moodle = st.radio(
            "Tratamiento de libros de más de 80 páginas dentro del ramo:",
            [
                "Incluir Índice y primeras 20 páginas (Recomendado para no saturar memoria con 900 págs)",
                "Incluir el 100% de todas las páginas de todos los PDFs sin límite",
            ],
        )

    archivos_subidos = st.file_uploader(
        "Arrastra aquí todos los PDFs, Excels (.xlsx/.xls), Word (.docx), .rmd o un .zip del ramo:",
        type=["pdf", "xlsx", "xls", "docx", "rmd", "txt", "md", "csv", "zip"],
        accept_multiple_files=True,
        key="uploader_moodle_multiple",
    )

    if archivos_subidos and st.button("Destilar Ramo Completo en 1 Archivo .TXT", type="primary"):
        bloques_ramo = [
            "=" * 90,
            f"SUPER CONTEXTO DE CÁTEDRA MOODLE ULAGOS: {nombre_ramo}",
            "=" * 90,
            "INVENTARIO DE ARCHIVOS PROCESADOS:",
        ]
        for f_up in archivos_subidos:
            bloques_ramo.append(f"  - {f_up.name} ({f_up.size / 1024.0:,.1f} KB)")
        bloques_ramo.append("\n" + "=" * 90 + "\n")

        with st.spinner("Extrayendo texto de PDFs y desglosando fórmulas de Excels..."):
            for f_up in archivos_subidos:
                raw_b = f_up.read()
                if f_up.name.lower().endswith(".zip"):
                    with zipfile.ZipFile(io.BytesIO(raw_b), "r") as zf:
                        for info in zf.infolist():
                            if info.is_dir():
                                continue
                            nom_interno = info.filename
                            if os.path.splitext(nom_interno)[1].lower() in EXTENSIONES_IGNORADAS_MOODLE:
                                continue
                            b_interno = zf.read(nom_interno)
                            bloques_ramo.append(procesar_archivo_individual(nom_interno, b_interno, modo_libros_moodle))
                else:
                    bloques_ramo.append(procesar_archivo_individual(f_up.name, raw_b, modo_libros_moodle))

        txt_ramo_final = "\n".join(bloques_ramo)
        nom_salida_ramo = f"CATEDRA_{nombre_ramo}.txt"
        st.success(
            f"¡Listo! Se destilaron {len(archivos_subidos)} archivos en `{nom_salida_ramo}` "
            f"({len(txt_ramo_final):,} caracteres)."
        )
        st.download_button(
            label=f"Descargar {nom_salida_ramo} (Listo para subir al chat de IA)",
            data=txt_ramo_final,
            file_name=nom_salida_ramo,
            mime="text/plain",
            use_container_width=True,
        )

# ------------------------------------------------------------------------------
# PESTAÑA 3: BUSCADOR COGNITIVO Y EXTRACTOR DE TOMOS EN LIBROS PESADOS
# ------------------------------------------------------------------------------
with tab_libros:
    st.markdown(
        "<div class='sec-header'>EXTRACTOR POR TEMA Y DIVISOR EN TOMOS PARA LIBROS GRANDES (ROSS, GITMAN, FONTAINE, CEPAL)</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "Sube aquí uno o varios **libros o manuales grandes en PDF** (como *Ross*, *Brealey*, *Gitman*, *Fontaine*, "
        "*Metodología MIDESO 2025*, *CEPAL Cadenas de Valor* o *SUBDERE PROT*) para:\n"
        "1. **Extraer solo las páginas donde aparece un tema específico** (con número de página exacto para citar en APA 7), o\n"
        "2. **Descargar el libro entero dividido en Tomos `.TXT`** (de ~400.000 caracteres cada uno) dentro de un `.zip`."
    )

    libros_subidos = st.file_uploader(
        "Sube aquí el libro o los libros PDF:",
        type=["pdf"],
        accept_multiple_files=True,
        key="uploader_libros_pesados",
    )

    modo_accion_libro = st.radio(
        "¿Qué deseas hacer con los libros cargados?",
        [
            "Buscar un concepto o fórmula y extraer todas las páginas donde se explica",
            "Convertir el libro completo en Tomos .TXT (empaquetados en un .ZIP)",
        ],
        horizontal=True,
    )

    if "Buscar un concepto" in modo_accion_libro:
        palabras_input = st.text_input(
            "Escribe las palabras clave separadas por coma (ej: Markowitz, frontera eficiente  |  WACC, CAPM  |  Rondinelli):",
            value="Markowitz, frontera",
        )
        if libros_subidos and st.button("Buscar en Libros y Generar Extracto Teórico (.TXT)", type="primary"):
            kws = [k.strip().lower() for k in palabras_input.split(",") if k.strip()]
            lineas_busq = [
                "=" * 90,
                f"EXTRACTO TEÓRICO DE BIBLIOTECA ULAGOS — CONCEPTOS: {', '.join(kws)}",
                "=" * 90,
                "",
            ]
            total_pags_halladas = 0
            with st.spinner("Escaneando todas las páginas de los libros cargados..."):
                for lib in libros_subidos:
                    pags = leer_paginas_pdf_bytes(lib.read(), lib.name)
                    hallazgos = []
                    for num_p, txt_p in pags:
                        txt_l = txt_p.lower()
                        if any(k in txt_l for k in kws):
                            score = sum(1 for k in kws if k in txt_l)
                            hallazgos.append((score, num_p, txt_p))

                    hallazgos.sort(key=lambda x: (-x[0], x[1]))
                    if hallazgos:
                        total_pags_halladas += len(hallazgos)
                        lineas_busq.append(
                            f"## LIBRO: {lib.name} ({len(hallazgos)} páginas relevantes encontradas de {len(pags)} totales)"
                        )
                        lineas_busq.append("-" * 75)
                        for sc, num_p, txt_p in hallazgos[:40]:
                            lineas_busq.append(f"### [{lib.name} — Página {num_p} | Coincidencias: {sc}/{len(kws)}]\n{txt_p}\n")
                        lineas_busq.append("=" * 90 + "\n")

            txt_busq_final = "\n".join(lineas_busq)
            st.success(f"Se encontraron {total_pags_halladas} páginas relevantes en los libros analizados.")
            st.download_button(
                label="Descargar EXTRACTO_TEORICO_LIBROS.txt",
                data=txt_busq_final,
                file_name="EXTRACTO_TEORICO_LIBROS.txt",
                mime="text/plain",
                use_container_width=True,
            )
    else:
        if libros_subidos and st.button("Convertir Libros Completos en Tomos .TXT (.ZIP)", type="primary"):
            buf_zip = io.BytesIO()
            with st.spinner("Convirtiendo libros completos en tomos de texto..."):
                with zipfile.ZipFile(buf_zip, "w", zipfile.ZIP_DEFLATED) as zf_out:
                    for lib in libros_subidos:
                        pags = leer_paginas_pdf_bytes(lib.read(), lib.name)
                        base_nom = os.path.splitext(lib.name)[0].replace(" ", "_")
                        tomo = 1
                        acum = [f"LIBRO COMPLETO: {lib.name} — TOMO {tomo}\n" + "=" * 80 + "\n"]
                        chars = 0
                        for num_p, txt_p in pags:
                            blq = f"\n--- [{lib.name} | Página {num_p}] ---\n{txt_p}\n"
                            if chars + len(blq) > 400_000 and chars > 0:
                                zf_out.writestr(f"{base_nom}_Tomo{tomo}.txt", "".join(acum))
                                tomo += 1
                                acum = [f"LIBRO COMPLETO: {lib.name} — TOMO {tomo}\n" + "=" * 80 + "\n"]
                                chars = 0
                            acum.append(blq)
                            chars += len(blq)
                        if chars > 0:
                            zf_out.writestr(f"{base_nom}_Tomo{tomo}.txt", "".join(acum))

            buf_zip.seek(0)
            st.success("¡Libros convertidos al 100% en tomos .TXT!")
            st.download_button(
                label="Descargar Biblioteca_Libros_Tomos_TXT.zip",
                data=buf_zip.getvalue(),
                file_name="Biblioteca_Libros_Tomos_TXT.zip",
                mime="application/zip",
                use_container_width=True,
            )
