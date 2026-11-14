# -*- coding: utf-8 -*-
"""
HUB DE APLICACIONES Y SUPER EXTRACTOR DE CONTEXTO (GITHUB + BÓVEDA MOODLE ULAGOS)
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
    page_title="Hub de Aplicaciones y Extractor de Contexto - Mauricio Vargas",
    layout="wide",
)

# Estilo corporativo con margen superior amplio (3.4rem) para que jamás se corte el título arriba
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 3.4rem !important;
        padding-bottom: 2rem !important;
        max-width: 1280px !important;
    }
    .corp-banner {
        background: linear-gradient(90deg, #0F172A 0%, #1E3A8A 100%);
        color: #FFFFFF;
        padding: 20px 26px;
        border-radius: 6px;
        margin-bottom: 18px;
        border-left: 5px solid #38BDF8;
    }
    .corp-title {
        font-size: 21px;
        font-weight: 700;
        margin: 0;
        line-height: 1.35;
        letter-spacing: 0.3px;
    }
    .corp-sub {
        font-size: 13px;
        color: #CBD5E1;
        margin-top: 6px;
    }
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
        <div class="corp-sub">Conectado en tiempo real a la API de GitHub y Bóveda Instantánea de Cátedras, Excels y Libros PDF para IA</div>
    </div>
    """,
    unsafe_allow_html=True,
)

USUARIO = "mauriciovargas1516-ux"
ARCHIVO_BOVEDA_MOODLE = "Todos_Los_Ramos_Destilados_TXT.zip"
EXTENSIONES_GIT = (".py", ".md", ".txt", ".rmd", ".toml", ".json")
EXTENSIONES_IGNORADAS_MOODLE = (
    ".mp4", ".avi", ".mov", ".mkv", ".zip", ".rar", ".exe", ".png", ".jpg", ".jpeg", ".mp3", ".wav"
)

APPS_STREAMLIT = {
    "PROYECTOS-2026": ("Suite Proyectos 2026", "https://proyectos-2026-ubfvxgpqmpp5z7dn6wlnn3.streamlit.app/"),
    "FINANZAS-AVANZADAS-2026": ("Finanzas Avanzadas 2026", "https://finanzas-avanzadas-2026-nxvqzsfrrtgu9e92javcli.streamlit.app/"),
    "DESARROLLO-Y-GESTION-TERRITORIAL-2026": ("Gestión Territorial 2026", "https://desarrollo-y-gestion-territorial-2026-ec6keylhsgra88s77bkl6f.streamlit.app/"),
    "GESTION-TRIBUTARIA-2026": ("Gestión Tributaria 2026", "https://gestion-tributaria-2026-avecwdhabftj7rjnx5knmb.streamlit.app/"),
}


# ==============================================================================
# FUNCIONES DEL EXTRACTOR DE GITHUB
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
            bloques.append(f"App Streamlit en Vivo: {APPS_STREAMLIT[nombre][1]}")
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
# FUNCIONES DEL DESTILADOR DE MOODLE Y LIBROS PDF
# ==============================================================================
def leer_paginas_pdf_bytes(data_bytes: bytes, nombre_archivo: str) -> list:
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
# I. BARRA SUPERIOR DE ACCESO RÁPIDO A LAS 4 PLATAFORMAS (SIN TEXTO CORTADO)
# ==============================================================================
st.markdown(
    "<div class='sec-header'>I. PLATAFORMAS INTERACTIVAS DESPLEGADAS EN STREAMLIT CLOUD</div>",
    unsafe_allow_html=True,
)
cols = st.columns(4)
for idx, (_, (etiqueta_corta, link_app)) in enumerate(APPS_STREAMLIT.items()):
    with cols[idx % 4]:
        st.link_button(f"Abrir {etiqueta_corta}", link_app, use_container_width=True)

# ==============================================================================
# II. BÓVEDA INSTANTÁNEA EN EL REPOSITORIO (SE ACTIVA AL SUBIR EL ZIP DE 2 MB)
# ==============================================================================
if os.path.exists(ARCHIVO_BOVEDA_MOODLE):
    st.markdown(
        "<div class='sec-header'>II. BÓVEDA MOODLE PRE-CARGADA (DESCARGA EN 1 CLIC SIN SUBIR ARCHIVOS)</div>",
        unsafe_allow_html=True,
    )
    with zipfile.ZipFile(ARCHIVO_BOVEDA_MOODLE, "r") as zf_bov:
        archivos_txt_boveda = sorted([n for n in zf_bov.namelist() if n.endswith(".txt")])

    c_bov1, c_bov2, c_bov3 = st.columns([1.8, 1.1, 1.1])
    with c_bov1:
        txt_elegido = st.selectbox(
            "Selecciona el Ramo Destilado en la Bóveda:",
            archivos_txt_boveda,
            label_visibility="collapsed",
        )
    with c_bov2:
        with zipfile.ZipFile(ARCHIVO_BOVEDA_MOODLE, "r") as zf_bov:
            bytes_ramo = zf_bov.read(txt_elegido)
        st.download_button(
            label=f"Descargar {txt_elegido}",
            data=bytes_ramo,
            file_name=txt_elegido,
            mime="text/plain",
            type="primary",
            use_container_width=True,
        )
    with c_bov3:
        with open(ARCHIVO_BOVEDA_MOODLE, "rb") as f_z:
            bytes_zip_total = f_z.read()
        st.download_button(
            label="Descargar ZIP Completo (Todos los Ramos)",
            data=bytes_zip_total,
            file_name=ARCHIVO_BOVEDA_MOODLE,
            mime="application/zip",
            use_container_width=True,
        )

st.divider()

# ==============================================================================
# NAVEGACIÓN POR PESTAÑAS (TÍTULOS COMPACTOS PARA EVITAR RECORTE LATERAL)
# ==============================================================================
tab_git, tab_moodle, tab_libros = st.tabs([
    "1. Extractor GitHub (API en Vivo)",
    "2. Destilador Moodle (ZIP Completo o Archivos)",
    "3. Buscador en Libros PDF (Ross, Gitman, Fontaine, CEPAL)",
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
# PESTAÑA 2: DESTILADOR DE CÁTEDRAS MOODLE (ZIP COMPLETO EN STREAMING O SUELTOS)
# ------------------------------------------------------------------------------
with tab_moodle:
    st.markdown(
        "<div class='sec-header'>DESTILAR RESPALDO_ULAGOS_2026.ZIP COMPLETO (IGNORA VIDEOS MP4 EN STREAMING) O ARCHIVOS SUELTOS</div>",
        unsafe_allow_html=True,
    )
    st.info(
        "**Bóveda Permanente:** Si subes el archivo liviano **`Todos_Los_Ramos_Destilados_TXT.zip`** a la raíz de este "
        "repositorio en GitHub, quedará habilitado para siempre el panel de descarga en 1 clic en la parte superior."
    )

    c_m1, c_m2 = st.columns([1.3, 1.7])
    with c_m1:
        filtro_ramo_zip = st.selectbox(
            "¿Qué carpeta(s) deseas procesar si subes el ZIP completo?",
            [
                "TODAS LAS CARPETAS DEL ZIP (Genera Todos_Los_Ramos_Destilados_TXT.zip)",
                "Solo FINANZAS AVANZADAS 2026 (Genera 1 archivo .TXT directo)",
                "Solo TRIBUTARIA 2026 (Genera 1 archivo .TXT directo)",
                "Solo PROYECTOS 2026 (Genera 1 archivo .TXT directo)",
                "Solo TERRITORIAL 2026 (Genera 1 archivo .TXT directo)",
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
        "Arrastra aquí tu Respaldo_ULagos_2026.zip completo o los PDFs / Excels sueltos del ramo:",
        type=["zip", "pdf", "xlsx", "xls", "docx", "rmd", "txt", "md", "csv"],
        accept_multiple_files=True,
        key="uploader_moodle_multiple",
    )

    if archivos_subidos and st.button("Destilar e Ignorar Videos Automáticamente", type="primary"):
        es_un_zip = (len(archivos_subidos) == 1) and archivos_subidos[0].name.lower().endswith(".zip")

        if es_un_zip and filtro_ramo_zip.startswith("TODAS"):
            f_zip = archivos_subidos[0]
            f_zip.seek(0)
            buf_out_zip = io.BytesIO()
            conteo_ignorados = 0
            conteo_procesados = 0

            with st.spinner("Leyendo Respaldo_ULagos_2026.zip en streaming, saltando videos MP4 y separando por ramo..."):
                with zipfile.ZipFile(f_zip, "r") as zf_in:
                    cursos_map = {}
                    for info in zf_in.infolist():
                        if info.is_dir():
                            continue
                        partes = info.filename.split("/")
                        carpeta_curso = partes[0] if len(partes) > 1 else "RAIZ_ULAGOS"
                        cursos_map.setdefault(carpeta_curso, []).append(info)

                    with zipfile.ZipFile(buf_out_zip, "w", zipfile.ZIP_DEFLATED) as zf_out:
                        for curso_nom, lista_infos in cursos_map.items():
                            bloques_c = [
                                "=" * 90,
                                f"SUPER CONTEXTO DE CÁTEDRA MOODLE ULAGOS: {curso_nom}",
                                "=" * 90,
                                "INVENTARIO COMPLETO DE LA CARPETA (INCLUYENDO MULTIMEDIA OMITIDO):",
                            ]
                            for inf in lista_infos:
                                bloques_c.append(f"  - {inf.filename} ({inf.file_size / 1024.0:,.1f} KB)")
                            bloques_c.append("\n" + "=" * 90 + "\n")

                            for inf in lista_infos:
                                ext_i = os.path.splitext(inf.filename)[1].lower()
                                peso_mb_i = inf.file_size / (1024.0 * 1024.0)
                                if ext_i in EXTENSIONES_IGNORADAS_MOODLE:
                                    conteo_ignorados += 1
                                    bloques_c.append(
                                        f"### VIDEO / COMPRIMIDO IGNORADO SIN DESCOMPRIMIR: {inf.filename} ({peso_mb_i:.1f} MB)\n"
                                    )
                                    continue

                                conteo_procesados += 1
                                b_doc = zf_in.read(inf.filename)
                                bloques_c.append(procesar_archivo_individual(inf.filename, b_doc, modo_libros_moodle))

                            nom_txt_c = f"CATEDRA_{curso_nom.replace(' ', '_').replace('[', '').replace(']', '')}.txt"
                            zf_out.writestr(nom_txt_c, "\n".join(bloques_c))

            buf_out_zip.seek(0)
            st.success(
                f"¡ZIP completo procesado! Se extrajeron {conteo_procesados} documentos académicos y se "
                f"ignoraron {conteo_ignorados} videos/binarios pesados."
            )
            st.download_button(
                label="Descargar Todos_Los_Ramos_Destilados_TXT.zip (Súbelo a tu GitHub para dejarlo fijo)",
                data=buf_out_zip.getvalue(),
                file_name="Todos_Los_Ramos_Destilados_TXT.zip",
                mime="application/zip",
                use_container_width=True,
            )

        else:
            filtro_clave = ""
            if "FINANZAS" in filtro_ramo_zip:
                filtro_clave = "FINANZAS"
            elif "TRIBUTARIA" in filtro_ramo_zip:
                filtro_clave = "TRIBUTARIA"
            elif "PROYECTOS" in filtro_ramo_zip:
                filtro_clave = "PROYECTOS"
            elif "TERRITORIAL" in filtro_ramo_zip:
                filtro_clave = "TERRITORIAL"

            etiqueta_ramo = filtro_clave if filtro_clave else "RAMO_ULAGOS_2026"
            bloques_ramo = [
                "=" * 90,
                f"SUPER CONTEXTO DE CÁTEDRA MOODLE ULAGOS: {etiqueta_ramo}",
                "=" * 90,
                "",
            ]
            conteo_ok = 0
            conteo_skip = 0

            with st.spinner("Extrayendo documentos y fórmulas de Excel (saltando videos MP4)..."):
                for f_up in archivos_subidos:
                    f_up.seek(0)
                    if f_up.name.lower().endswith(".zip"):
                        with zipfile.ZipFile(f_up, "r") as zf_in:
                            for info in zf_in.infolist():
                                if info.is_dir():
                                    continue
                                if filtro_clave and filtro_clave.lower() not in info.filename.lower():
                                    continue
                                ext_i = os.path.splitext(info.filename)[1].lower()
                                if ext_i in EXTENSIONES_IGNORADAS_MOODLE:
                                    conteo_skip += 1
                                    bloques_ramo.append(
                                        f"### VIDEO / COMPRIMIDO IGNORADO: {info.filename} ({info.file_size/1024/1024:.1f} MB)\n"
                                    )
                                    continue
                                conteo_ok += 1
                                b_interno = zf_in.read(info.filename)
                                bloques_ramo.append(
                                    procesar_archivo_individual(info.filename, b_interno, modo_libros_moodle)
                                )
                    else:
                        ext_s = os.path.splitext(f_up.name)[1].lower()
                        if ext_s in EXTENSIONES_IGNORADAS_MOODLE:
                            conteo_skip += 1
                            continue
                        conteo_ok += 1
                        bloques_ramo.append(
                            procesar_archivo_individual(f_up.name, f_up.read(), modo_libros_moodle)
                        )

            txt_ramo_final = "\n".join(bloques_ramo)
            nom_salida_ramo = f"CATEDRA_{etiqueta_ramo}_2026.txt"
            st.success(
                f"¡Listo! Se procesaron {conteo_ok} documentos ({conteo_skip} videos/binarios ignorados) "
                f"en `{nom_salida_ramo}` ({len(txt_ramo_final):,} caracteres)."
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
                    lib.seek(0)
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
                        lib.seek(0)
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
