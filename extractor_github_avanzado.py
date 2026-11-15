# -*- coding: utf-8 -*-
"""
extractor_github_avanzado.py — SUPER EXTRACTOR MULTI-REPOSITORIO (PESTAÑA 1)
- Soporta 4 niveles de profundidad, incluyendo el SUPER EXTRACTOR TOTAL (todo en 1 solo .TXT)
  y el Mapa Arquitectónico con firmas AST para pasar 11+ repositorios sin recortes.
- Captura repositorios públicos y privados (cuando Modo Admin está activo), Topics,
  visibilidad, archivo principal de entrada y archivos de configuración (.gitignore, .ipynb, etc.).
- Entrega tabla de peso/tokens por repositorio y 3 formatos de descarga instantáneos:
  1) 1 solo .TXT maestro unificado.
  2) .ZIP con 1 .TXT individual por repositorio.
  3) .ZIP dividido automáticamente en tomos equilibrados (~350 KB por parte).
"""

import io
import os
import re
import ast
import json
import zipfile
import urllib.parse
import urllib.request
from datetime import datetime

import pandas as pd
import streamlit as st


EXTENSIONES_TEXTO = (
    ".py", ".md", ".txt", ".toml", ".json", ".yaml", ".yml",
    ".css", ".html", ".js", ".ts", ".rmd", ".r", ".sql", ".sh",
    ".csv", ".ipynb", ".ini", ".cfg"
)

EXTENSIONES_DATOS_PESADOS = (".csv", ".json", ".txt")

NOMBRES_CONFIG_ESPECIALES = {
    ".gitignore", "dockerfile", "procfile", "makefile",
    ".dockerignore", ".env.example", "license", "packages.txt"
}

CATALOGO_COMPLEMENTARIO = {
    "mauriciovargas1516-ux": {
        "ramo": "Perfil GitHub y Portafolio Principal",
        "categoria": "Perfil y Portafolio",
        "sigla_archivo": "PERFIL_PORTAFOLIO_GITHUB",
        "corto": "PERFIL",
        "docente": "Portafolio Técnico Profesional",
        "app_url": "https://github.com/mauriciovargas1516-ux",
        "descripcion": "README de perfil principal y presentación del portafolio técnico en GitHub.",
        "topics": ["portfolio", "python", "streamlit", "chile"],
    },
    "insumaes-woocommerce-automation": {
        "ramo": "Insumaes — Automatización WooCommerce e Inventario",
        "categoria": "Proyecto Comercial / Automatización",
        "sigla_archivo": "INSUMAES_WOOCOMMERCE",
        "corto": "INSUMAES",
        "docente": "Operación Comercial E-Commerce",
        "app_url": "",
        "descripcion": "Automatización de inventario, sincronización de catálogo y operaciones omnicanal en WooCommerce.",
        "topics": ["python", "woocommerce", "automation", "ecommerce", "inventory"],
    },
    "motor-planos-sec-te1-chile": {
        "ramo": "Motor Planos Eléctricos SEC TE1 Chile",
        "categoria": "Ingeniería y Automatización",
        "sigla_archivo": "MOTOR_PLANOS_SEC_TE1",
        "corto": "SEC_TE1",
        "docente": "Instalaciones Eléctricas Chile",
        "app_url": "",
        "descripcion": "Automatización de cuadros de carga, cálculos normativos y documentación técnica para declaraciones SEC TE1.",
        "topics": ["python", "sec-chile", "te1", "electrical-engineering", "automation"],
    },
    "motor-auditor-dte-finops": {
        "ramo": "Motor Auditor DTE y FinOps",
        "categoria": "FinOps y Tributario",
        "sigla_archivo": "MOTOR_AUDITOR_DTE_FINOPS",
        "corto": "AUDITOR_DTE",
        "docente": "Auditoría Tributaria y Cloud",
        "app_url": "",
        "descripcion": "Motor de auditoría de Documentos Tributarios Electrónicos (DTE SII) y control financiero operativo.",
        "topics": ["python", "sii-chile", "dte", "finops", "audit"],
    },
    "motor-conciliador-chile": {
        "ramo": "Motor Conciliador Financiero Chile",
        "categoria": "Finanzas y Conciliación",
        "sigla_archivo": "MOTOR_CONCILIADOR_CHILE",
        "corto": "CONCILIADOR",
        "docente": "Conciliación Bancaria y Facturación",
        "app_url": "",
        "descripcion": "Cruce y conciliación automatizada de cartolas bancarias, pagos y documentos tributarios en Chile.",
        "topics": ["python", "fintech", "reconciliation", "chile", "pandas"],
    },
}


# ==============================================================================
# 1. UTILIDADES DE METADATOS, API GITHUB Y PARSEO DE ARCHIVOS
# ==============================================================================

def _obtener_meta_extendida(nombre_repo, mapa_repos, usuario_gh, desc_api="", homepage_api=""):
    if nombre_repo in mapa_repos:
        base = dict(mapa_repos[nombre_repo])
        base.setdefault("categoria", "Cátedra ULagos 2026")
        return base
    if nombre_repo in CATALOGO_COMPLEMENTARIO:
        base = dict(CATALOGO_COMPLEMENTARIO[nombre_repo])
        base.setdefault("repo_url", f"https://github.com/{usuario_gh}/{nombre_repo}")
        return base

    limpio = re.sub(r"[^A-Za-z0-9]+", "_", nombre_repo).strip("_").upper()
    return {
        "ramo": nombre_repo,
        "categoria": "Otros Proyectos",
        "sigla_archivo": limpio,
        "corto": limpio[:12],
        "docente": "Desarrollo Independiente",
        "app_url": homepage_api or "",
        "repo_url": f"https://github.com/{usuario_gh}/{nombre_repo}",
        "descripcion": desc_api or "Repositorio de código en GitHub.",
        "topics": [],
    }


def _gh_get_json(url, token=""):
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "ULagos-Super-Extractor-2026",
    }
    if token and token.strip():
        headers["Authorization"] = f"Bearer {token.strip()}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


@st.cache_data(ttl=180, show_spinner=False)
def listar_repos_completo(usuario, token="", mapa_repos_keys=()):
    """Lista repositorios con Topics, visibilidad y rama; incluye privados si hay token."""
    datos = []
    usando_fallback = False

    if token and token.strip():
        try:
            bruto = _gh_get_json(
                "https://api.github.com/user/repos?per_page=100&sort=updated&affiliation=owner",
                token=token,
            )
            datos = [
                d for d in bruto
                if d.get("owner", {}).get("login", "").lower() == usuario.lower()
            ]
        except Exception:
            datos = []

    if not datos:
        try:
            datos = _gh_get_json(
                f"https://api.github.com/users/{urllib.parse.quote(usuario)}/repos?per_page=100&sort=updated",
                token=token,
            )
        except Exception:
            usando_fallback = True
            nombres_vistos = []
            try:
                req = urllib.request.Request(
                    f"https://github.com/{usuario}?tab=repositories",
                    headers={"User-Agent": "Mozilla/5.0"},
                )
                with urllib.request.urlopen(req, timeout=15) as resp:
                    html_txt = resp.read().decode("utf-8", errors="replace")
                patron = rf'href="/{re.escape(usuario)}/([^/"?#]+)"[^>]*itemprop="name codeRepository"'
                for m in re.finditer(patron, html_txt):
                    r_n = m.group(1).strip()
                    if r_n and r_n not in nombres_vistos:
                        nombres_vistos.append(r_n)
            except Exception:
                pass
            for k in list(mapa_repos_keys) + list(CATALOGO_COMPLEMENTARIO.keys()):
                if k not in nombres_vistos:
                    nombres_vistos.append(k)
            return [
                {
                    "name": rn,
                    "description": "",
                    "html_url": f"https://github.com/{usuario}/{rn}",
                    "homepage": "",
                    "topics": [],
                    "private": False,
                    "default_branch": "main",
                    "updated_at": datetime.now().strftime("%Y-%m-%d"),
                    "language": "",
                }
                for rn in nombres_vistos
            ], True

    repos = []
    for d in datos:
        repos.append({
            "name": d.get("name", ""),
            "description": d.get("description") or "",
            "html_url": d.get("html_url", ""),
            "homepage": d.get("homepage") or "",
            "topics": d.get("topics") or [],
            "private": bool(d.get("private", False)),
            "default_branch": d.get("default_branch", "main"),
            "updated_at": (d.get("updated_at") or "")[:10],
            "language": d.get("language") or "",
        })
    return repos, usando_fallback


def _descargar_zip_codeload(usuario, nombre_repo, rama_preferida="main", token=""):
    ramas = []
    for r in [rama_preferida, "main", "master"]:
        if r and r not in ramas:
            ramas.append(r)

    ultimo_error = None
    for rama in ramas:
        url_zip = f"https://codeload.github.com/{usuario}/{nombre_repo}/zip/refs/heads/{rama}"
        headers = {"User-Agent": "Mozilla/5.0"}
        if token and token.strip():
            headers["Authorization"] = f"Bearer {token.strip()}"
        req = urllib.request.Request(url_zip, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read()
        except Exception as exc:
            ultimo_error = exc
    raise RuntimeError(f"No se pudo descargar ZIP de {nombre_repo}: {ultimo_error}")


def _es_archivo_extraible(ruta_rel):
    base = os.path.basename(ruta_rel).lower()
    if base in NOMBRES_CONFIG_ESPECIALES:
        return True
    return base.endswith(EXTENSIONES_TEXTO)


def _limpiar_notebook_ipynb(texto_json):
    """Convierte un .ipynb a texto legible conservando solo celdas markdown y código (sin imágenes base64)."""
    try:
        nb = json.loads(texto_json)
        salidas = []
        for idx, celda in enumerate(nb.get("cells", []), start=1):
            tipo = celda.get("cell_type", "code").upper()
            fuente = "".join(celda.get("source", []))
            if fuente.strip():
                salidas.append(f"# --- CELDA {idx} [{tipo}] ---\n{fuente}")
        return "\n\n".join(salidas) if salidas else "[Notebook sin celdas de texto/código]"
    except Exception:
        return texto_json


def _extraer_firmas_ast_python(codigo_py):
    """Extrae imports, clases, funciones y sus docstrings de un archivo .py para el Modo Mapa."""
    try:
        arbol = ast.parse(codigo_py)
    except Exception:
        lineas = [
            l for l in codigo_py.splitlines()
            if l.lstrip().startswith(("def ", "class ", "import ", "from "))
        ]
        return "\n".join(lineas[:80]) if lineas else "[Sin definiciones detectadas]"

    resumen = []
    imports = []
    for nodo in arbol.body:
        if isinstance(nodo, ast.Import):
            for alias in nodo.names:
                imports.append(alias.name)
        elif isinstance(nodo, ast.ImportFrom):
            mod = nodo.module or ""
            imports.append(mod)

    if imports:
        unicos = sorted(set(i for i in imports if i))
        resumen.append(f"Imports ({len(unicos)}): {', '.join(unicos)}")

    doc_mod = ast.get_docstring(arbol)
    if doc_mod:
        primera_lin = doc_mod.strip().splitlines()[0][:160]
        resumen.append(f"Docstring: {primera_lin}")

    for nodo in arbol.body:
        if isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = [a.arg for a in nodo.args.args]
            resumen.append(f"def {nodo.name}({', '.join(args)})  [línea {nodo.lineno}]")
        elif isinstance(nodo, ast.ClassDef):
            metodos = [
                f"{n.name}()"
                for n in nodo.body
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            ]
            resumen.append(f"class {nodo.name} [línea {nodo.lineno}] -> métodos: {', '.join(metodos[:15])}")

    return "\n".join(resumen) if resumen else "[Script procedural sin funciones/clases top-level]"


def _detectar_entrypoint(rutas_archivos):
    bajas = {r.lower(): r for r in rutas_archivos}
    for cand in ["app.py", "consola_web.py", "main.py", "streamlit_app.py", "index.py"]:
        if cand in bajas:
            return bajas[cand]
    pys = [r for r in rutas_archivos if r.lower().endswith(".py")]
    return pys[0] if pys else "-"


# ==============================================================================
# 2. EXTRACTOR DE REPOSITORIO POR NIVEL DE PROFUNDIDAD
# ==============================================================================

def extraer_repo_segun_modo(
    usuario,
    repo_info,
    mapa_repos,
    modo_profundidad,
    token="",
    incluir_literatura=True,
    fn_formatear_cuadrilla=None,
):
    nombre_repo = repo_info["name"]
    rama = repo_info.get("default_branch", "main")
    meta = _obtener_meta_extendida(
        nombre_repo, mapa_repos, usuario,
        repo_info.get("description", ""), repo_info.get("homepage", "")
    )
    topics = repo_info.get("topics") or meta.get("topics") or []
    visibilidad = "Privado" if repo_info.get("private") else "Público"
    homepage = repo_info.get("homepage") or meta.get("app_url") or "No especificada"

    bloques = [
        f"### REPOSITORIO: {nombre_repo} | {meta['ramo']}",
        f"Categoría: {meta.get('categoria', '-')} | Visibilidad: {visibilidad} | Rama: {rama} | Última actualización: {repo_info.get('updated_at', '-')}",
        f"Contexto / Docente: {meta['docente']}",
        f"About (Descripción): {repo_info.get('description') or meta['descripcion']}",
        f"Topics: {', '.join(topics) if topics else '(sin topics)'}",
        f"URL GitHub: {repo_info.get('html_url') or meta['repo_url']}",
        f"App / Homepage: {homepage}",
        "-" * 92,
    ]

    if incluir_literatura and callable(fn_formatear_cuadrilla):
        lit_txt = fn_formatear_cuadrilla(meta["ramo"])
        if lit_txt:
            bloques.append(lit_txt)

    archivos_incluidos = 0
    entrypoint = "-"

    try:
        zip_bytes = _descargar_zip_codeload(usuario, nombre_repo, rama_preferida=rama, token=token)
        with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
            archivos_zip = []
            for zinfo in zf.infolist():
                if zinfo.is_dir():
                    continue
                partes = zinfo.filename.split("/", 1)
                ruta_rel = partes[1] if len(partes) > 1 else zinfo.filename
                if ruta_rel:
                    archivos_zip.append((ruta_rel, zinfo))

            archivos_zip.sort(key=lambda x: x[0])
            rutas_todas = [r for r, _ in archivos_zip]
            entrypoint = _detectar_entrypoint(rutas_todas)

            bloques.append(f"#### INVENTARIO DE ARCHIVOS ({len(archivos_zip)} archivos | Entrypoint: {entrypoint}):")
            for ruta_rel, zinfo in archivos_zip:
                bloques.append(f"  - {ruta_rel} ({zinfo.file_size:,} bytes)")
            bloques.append("")

            for ruta_rel, zinfo in archivos_zip:
                if not _es_archivo_extraible(ruta_rel):
                    continue

                base_low = os.path.basename(ruta_rel).lower()
                ruta_low = ruta_rel.lower()
                es_meta_core = base_low in (
                    "readme.md", "requirements.txt", "packages.txt", "config.toml", ".gitignore"
                )

                if modo_profundidad == "Solo Auditoría CMS (About + README + requirements + config)":
                    if not es_meta_core:
                        continue

                try:
                    raw_bytes = zf.read(zinfo)
                    texto = raw_bytes.decode("utf-8", errors="replace")
                except Exception as exc:
                    bloques.append(f"#### ARCHIVO: {nombre_repo}/{ruta_rel}\n[No decodificable: {exc}]\n")
                    continue

                if ruta_low.endswith(".ipynb"):
                    texto = _limpiar_notebook_ipynb(texto)

                if modo_profundidad == "Mapa Arquitectónico (11+ repos sin cortes: README + config + firmas AST)":
                    if ruta_low.endswith(".py"):
                        bloques.append(f"#### FIRMAS PYTHON (AST): {nombre_repo}/{ruta_rel} ({zinfo.file_size:,} bytes)")
                        bloques.append("-" * 70)
                        bloques.append(_extraer_firmas_ast_python(texto))
                        bloques.append("\n")
                        archivos_incluidos += 1
                    elif es_meta_core or ruta_low.endswith((".toml", ".yml", ".yaml", ".sql")):
                        bloques.append(f"#### ARCHIVO: {nombre_repo}/{ruta_rel}")
                        bloques.append("-" * 70)
                        bloques.append(texto)
                        bloques.append("\n")
                        archivos_incluidos += 1
                    continue

                if modo_profundidad == "Código Limpio (Código completo, recorta .csv/.json/.txt pesados)":
                    if (
                        ruta_low.endswith(EXTENSIONES_DATOS_PESADOS)
                        and base_low not in ("requirements.txt", "packages.txt")
                        and zinfo.file_size > 15000
                    ):
                        lineas = texto.splitlines()
                        muestra = "\n".join(lineas[:40])
                        bloques.append(
                            f"#### ARCHIVO (MUESTRA 40/{len(lineas)} líneas): {nombre_repo}/{ruta_rel} ({zinfo.file_size:,} bytes)"
                        )
                        bloques.append("-" * 70)
                        bloques.append(muestra)
                        bloques.append(f"\n[... {len(lineas) - 40} líneas adicionales omitidas en Modo Código Limpio ...]\n\n")
                        archivos_incluidos += 1
                        continue

                # SUPER EXTRACTOR TOTAL (o archivo normal en Código Limpio / Auditoría)
                bloques.append(f"#### ARCHIVO: {nombre_repo}/{ruta_rel}")
                bloques.append("-" * 70)
                bloques.append(texto)
                bloques.append("\n")
                archivos_incluidos += 1

    except Exception as exc_zip:
        bloques.append(f"[Aviso al extraer {nombre_repo}: {exc_zip}]\n")

    texto_repo = "\n".join(bloques)
    stats = {
        "Repositorio": nombre_repo,
        "Categoría": meta.get("categoria", "-"),
        "Visibilidad": visibilidad,
        "Entrypoint": entrypoint,
        "Archivos Extraídos": archivos_incluidos,
        "Tamaño (KB)": round(len(texto_repo.encode("utf-8")) / 1024.0, 1),
        "Tokens Est.": int(len(texto_repo) / 4),
    }
    return texto_repo, stats


def _crear_zip_por_repo(bloques_por_repo, encabezado_global, fecha_hoy):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"00_INDICE_MAESTRO_{fecha_hoy}.txt", encabezado_global.encode("utf-8"))
        for idx, (r_nom, contenido) in enumerate(bloques_por_repo, start=1):
            zf.writestr(f"{idx:02d}_{r_nom}_{fecha_hoy}.txt", contenido.encode("utf-8"))
    return buf.getvalue()


def _crear_zip_en_tomos(bloques_por_repo, encabezado_global, fecha_hoy, max_kb_tomo=350):
    max_bytes = max_kb_tomo * 1024
    tomos = []
    actual = [encabezado_global]
    bytes_act = len(encabezado_global.encode("utf-8"))

    for r_nom, contenido in bloques_por_repo:
        c_bytes = len(contenido.encode("utf-8"))
        if bytes_act + c_bytes > max_bytes and len(actual) > 1:
            tomos.append("\n".join(actual))
            actual = [f"CONTINUACIÓN DE EXTRACCIÓN ({fecha_hoy}) — REPOSITORIO: {r_nom}\n" + "=" * 80 + "\n"]
            bytes_act = len(actual[0].encode("utf-8"))

        if c_bytes > max_bytes:
            # Si un solo repositorio supera el límite, trocearlo por líneas sin romper el archivo
            lineas = contenido.splitlines(keepends=True)
            trozo = []
            b_trozo = 0
            parte_r = 1
            for lin in lineas:
                lb = len(lin.encode("utf-8"))
                if b_trozo + lb > max_bytes and trozo:
                    tomos.append("".join(trozo))
                    parte_r += 1
                    cab = f"[CONTINUACIÓN {r_nom} — SUBPARTE {parte_r}]\n"
                    trozo = [cab, lin]
                    b_trozo = len(cab.encode("utf-8")) + lb
                else:
                    trozo.append(lin)
                    b_trozo += lb
            if trozo:
                actual.append("".join(trozo))
                bytes_act += b_trozo
        else:
            actual.append(contenido)
            bytes_act += c_bytes

    if actual:
        tomos.append("\n".join(actual))

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        total_t = len(tomos)
        for idx, txt_t in enumerate(tomos, start=1):
            cab_t = f"=== TOMO {idx} DE {total_t} ({fecha_hoy}) ===\n\n"
            zf.writestr(f"TOMO_{idx:02d}_DE_{total_t:02d}_{fecha_hoy}.txt", (cab_t + txt_t).encode("utf-8"))
    return buf.getvalue(), len(tomos)


# ==============================================================================
# 3. INTERFAZ DE LA PESTAÑA 1 (SUPER EXTRACTOR GITHUB)
# ==============================================================================

def renderizar_extractor_github(
    usuario_gh,
    token_gh,
    mapa_repos,
    incluir_lit_en_txt=True,
    fn_formatear_cuadrilla=None,
    fn_cargar_boveda=None,
):
    st.markdown(
        "<div class='sec-header'>1. SUPER EXTRACTOR GITHUB — TODO EN 1 .TXT, MAPA ARQUITECTÓNICO Y DESCARGA EN TOMOS</div>",
        unsafe_allow_html=True,
    )

    lista_repos, usando_fallback = listar_repos_completo(
        usuario_gh, token=token_gh, mapa_repos_keys=tuple(mapa_repos.keys())
    )
    mapa_objetos = {r["name"]: r for r in lista_repos}
    nombres_disp = list(mapa_objetos.keys())

    if usando_fallback:
        st.caption("Modo directo Codeload activo (sin consumir cuota de GitHub API).")
    elif token_gh and token_gh.strip():
        n_priv = sum(1 for r in lista_repos if r.get("private"))
        st.caption(f"Conectado con Token Admin: {len(lista_repos)} repositorios detectados ({n_priv} privados incluidos).")

    if not nombres_disp:
        st.warning("No se encontraron repositorios para este usuario.")
        return

    c_mod, c_prof = st.columns([1.4, 2.6])
    with c_mod:
        modo_seleccion = st.radio(
            "1. Qué repositorios empaquetar:",
            options=[
                "Portafolio Completo (Todos los repos)",
                "Por Repositorio / Asignatura Específica",
                "Selección Manual Múltiple",
            ],
            key="ext_modo_sel",
        )

    with c_prof:
        modo_profundidad = st.selectbox(
            "2. Nivel de captura y profundidad:",
            options=[
                "SUPER EXTRACTOR TOTAL (Todo el código + docs en 1 solo .TXT)",
                "Código Limpio (Código completo, recorta .csv/.json/.txt pesados)",
                "Mapa Arquitectónico (11+ repos sin cortes: README + config + firmas AST)",
                "Solo Auditoría CMS (About + README + requirements + config)",
            ],
            key="ext_modo_prof",
        )

        if modo_seleccion == "Portafolio Completo (Todos los repos)":
            repos_seleccionados = nombres_disp
            st.caption(f"Se procesarán los {len(repos_seleccionados)} repositorios de `{usuario_gh}`.")
        elif modo_seleccion == "Por Repositorio / Asignatura Específica":
            opciones_etq = []
            for rn in nombres_disp:
                m = _obtener_meta_extendida(rn, mapa_repos, usuario_gh)
                opciones_etq.append(f"[{m.get('categoria', 'Repo')}] {rn} — {m['ramo']}")
            elegido = st.selectbox("Selecciona el repositorio:", options=opciones_etq, key="ext_one_sel")
            clave_r = elegido.split("] ", 1)[1].split(" — ", 1)[0].strip()
            repos_seleccionados = [clave_r] if clave_r in mapa_objetos else [nombres_disp[0]]
        else:
            def_sel = [r for r in ["PROYECTOS-2026", "DESARROLLO-Y-GESTION-TERRITORIAL-2026"] if r in nombres_disp] or nombres_disp[:1]
            repos_seleccionados = st.multiselect(
                "Elige los repositorios a incluir:",
                options=nombres_disp,
                default=def_sel,
                key="ext_multi_sel",
            )

    incluir_boveda_moodle = False
    if callable(fn_cargar_boveda):
        incluir_boveda_moodle = st.checkbox(
            "Modo Mega-Contexto: anexar también la Bóveda Moodle destilada (.txt del servidor) al final del Super .TXT",
            value=False,
            key="ext_inc_boveda",
        )

    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    if len(repos_seleccionados) == len(nombres_disp) and len(repos_seleccionados) > 1:
        tag_modo = {
            "SUPER EXTRACTOR TOTAL (Todo el código + docs en 1 solo .TXT)": "SUPER_TOTAL",
            "Código Limpio (Código completo, recorta .csv/.json/.txt pesados)": "CODIGO_LIMPIO",
            "Mapa Arquitectónico (11+ repos sin cortes: README + config + firmas AST)": "MAPA_ARQUITECTURA",
            "Solo Auditoría CMS (About + README + requirements + config)": "AUDITORIA_CMS",
        }[modo_profundidad]
        nombre_sugerido = f"CONTEXTO_PORTAFOLIO_{tag_modo}_{fecha_hoy}.txt"
    elif len(repos_seleccionados) == 1:
        m0 = _obtener_meta_extendida(repos_seleccionados[0], mapa_repos, usuario_gh)
        nombre_sugerido = f"CONTEXTO_{m0['sigla_archivo']}_{fecha_hoy}.txt"
    else:
        siglas = [_obtener_meta_extendida(r, mapa_repos, usuario_gh)["corto"] for r in repos_seleccionados[:4]]
        suf = "_".join(siglas)
        if len(repos_seleccionados) > 4:
            suf += f"_Y_{len(repos_seleccionados) - 4}_MAS"
        nombre_sugerido = f"CONTEXTO_MULTIRAMO_{suf}_{fecha_hoy}.txt"

    nombre_final = st.text_input(
        "Nombre del archivo .TXT unificado:",
        value=nombre_sugerido,
        key="ext_fname_out",
    )

    if st.button("COMPILAR SUPER CONTEXTO DE LOS REPOSITORIOS SELECCIONADOS", type="primary", use_container_width=True, key="ext_btn_run"):
        if not repos_seleccionados:
            st.warning("Selecciona al menos un repositorio.")
        else:
            lista_resumen = "\n".join(
                f"  * {r} [{_obtener_meta_extendida(r, mapa_repos, usuario_gh).get('categoria', '-')}] -> "
                f"{_obtener_meta_extendida(r, mapa_repos, usuario_gh)['ramo']}"
                for r in repos_seleccionados
            )
            encabezado = (
                "=" * 94 + "\n"
                f"SUPER EXTRACCIÓN DE CONTEXTO ({len(repos_seleccionados)} REPOSITORIOS) — {modo_profundidad}\n"
                f"Usuario GitHub: {usuario_gh} | Fecha: {fecha_hoy}\n"
                "Repositorios incluidos:\n"
                f"{lista_resumen}\n"
                + "=" * 94 + "\n\n"
            )

            bloques_por_repo = []
            filas_stats = []
            barra = st.progress(0.0, text="Descargando repositorios en memoria desde GitHub...")

            for idx, r_nom in enumerate(repos_seleccionados):
                barra.progress(idx / len(repos_seleccionados), text=f"Procesando {r_nom} ({idx + 1}/{len(repos_seleccionados)})...")
                r_obj = mapa_objetos.get(r_nom, {"name": r_nom, "default_branch": "main"})
                txt_r, stat_r = extraer_repo_segun_modo(
                    usuario=usuario_gh,
                    repo_info=r_obj,
                    mapa_repos=mapa_repos,
                    modo_profundidad=modo_profundidad,
                    token=token_gh,
                    incluir_literatura=incluir_lit_en_txt,
                    fn_formatear_cuadrilla=fn_formatear_cuadrilla,
                )
                bloques_por_repo.append((r_nom, txt_r))
                filas_stats.append(stat_r)

            if incluir_boveda_moodle and callable(fn_cargar_boveda):
                nom_bov, txt_bov, _ = fn_cargar_boveda()
                if txt_bov:
                    bloques_por_repo.append(("BOVEDA_MOODLE_DESTILADA", f"\n### BÓVEDA MOODLE ({nom_bov})\n" + txt_bov))
                    filas_stats.append({
                        "Repositorio": f"Bóveda Moodle ({nom_bov})",
                        "Categoría": "Literatura Destilada",
                        "Visibilidad": "Servidor",
                        "Entrypoint": nom_bov,
                        "Archivos Extraídos": 1,
                        "Tamaño (KB)": round(len(txt_bov.encode("utf-8")) / 1024.0, 1),
                        "Tokens Est.": int(len(txt_bov) / 4),
                    })

            barra.progress(1.0, text="Compilación completada.")

            texto_unificado = encabezado + "\n".join(c for _, c in bloques_por_repo)
            zip_por_repo = _crear_zip_por_repo(bloques_por_repo, encabezado, fecha_hoy)
            zip_tomos, num_tomos = _crear_zip_en_tomos(bloques_por_repo, encabezado, fecha_hoy, max_kb_tomo=350)

            st.session_state["ext_res"] = {
                "nombre_txt": nombre_final,
                "bytes_txt": texto_unificado.encode("utf-8"),
                "zip_por_repo": zip_por_repo,
                "zip_tomos": zip_tomos,
                "num_tomos": num_tomos,
                "stats": filas_stats,
                "fecha": fecha_hoy,
            }

    if "ext_res" in st.session_state:
        res_c = st.session_state["ext_res"]
        df_st = pd.DataFrame(res_c["stats"])
        kb_tot = len(res_c["bytes_txt"]) / 1024.0
        tok_tot = int(df_st["Tokens Est."].sum()) if not df_st.empty else 0

        st.success(
            f"Compilación lista: **{res_c['nombre_txt']}** — {kb_tot:,.1f} KB totales (~{tok_tot:,} tokens estimados)."
        )
        st.dataframe(df_st, use_container_width=True, hide_index=True)

        d1, d2, d3 = st.columns(3)
        with d1:
            st.download_button(
                label=f"1. DESCARGAR TODO EN 1 .TXT ({kb_tot:,.0f} KB)",
                data=res_c["bytes_txt"],
                file_name=res_c["nombre_txt"],
                mime="text/plain",
                type="primary",
                use_container_width=True,
                key="ext_dl_one",
            )
        with d2:
            st.download_button(
                label=f"2. DESCARGAR .ZIP (1 .TXT por Repo)",
                data=res_c["zip_por_repo"],
                file_name=f"REPOS_SEPARADOS_{res_c['fecha']}.zip",
                mime="application/zip",
                use_container_width=True,
                key="ext_dl_zip_repo",
            )
        with d3:
            st.download_button(
                label=f"3. DESCARGAR EN {res_c['num_tomos']} TOMOS (.ZIP)",
                data=res_c["zip_tomos"],
                file_name=f"CONTEXTO_EN_{res_c['num_tomos']}_TOMOS_{res_c['fecha']}.zip",
                mime="application/zip",
                use_container_width=True,
                key="ext_dl_zip_tomos",
            )
