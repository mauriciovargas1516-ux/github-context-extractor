# -*- coding: utf-8 -*-
"""
central_mando_github.py — CENTRAL DE MANDO MULTI-REPOSITORIO (CMS REMOTO GITHUB)
Módulo dedicado para gestionar en lote About, Topics, requirements.txt, README.md,
config.toml, archivos arbitrarios y el Puente en Vivo desde github-context-extractor.
"""

import re
import json
import base64
import urllib.parse
import requests
import pandas as pd
import streamlit as st


GITHUB_API_BASE = "https://api.github.com"
GITHUB_RAW_BASE = "https://raw.githubusercontent.com"

MARCADOR_PUENTE_INI = "# === [INICIO PUENTE CENTRAL ULAGOS 2026] ==="
MARCADOR_PUENTE_FIN = "# === [FIN PUENTE CENTRAL ULAGOS 2026] ==="

CONFIG_TOML_CLARO = """[theme]
base = "light"
primaryColor = "#1D4ED8"
backgroundColor = "#F8FAFC"
secondaryBackgroundColor = "#FFFFFF"
textColor = "#0F172A"
font = "sans serif"

[client]
toolbarMode = "minimal"
"""

PAQUETES_CATALOGO = [
    "streamlit",
    "pandas",
    "numpy",
    "openpyxl",
    "pypdf",
    "google-auth",
    "requests",
    "beautifulsoup4",
    "plotly",
    "matplotlib",
    "scipy",
    "networkx",
    "python-docx",
    "statsmodels",
    "scikit-learn",
]

CATALOGO_EXTRA_ABOUT = {
    "mauriciovargas1516-ux": {
        "ramo": "Perfil GitHub y Portafolio Principal",
        "docente": "Portafolio Técnico Profesional",
        "app_url": "https://app-context-extractor-cl8x5kwfdodzvmx7m3vean.streamlit.app/",
        "descripcion": "Perfil principal de GitHub y portafolio de ingeniería comercial, automatización en Python, FinOps y aplicaciones analíticas en Streamlit.",
        "topics": ["portfolio", "python", "streamlit", "finops", "data-analytics", "chile"],
    },
    "insumaes-woocommerce-automation": {
        "ramo": "Insumaes — Automatización WooCommerce e Inventario",
        "docente": "Operación Comercial E-Commerce",
        "app_url": "",
        "descripcion": "Pipeline de automatización de inventario, sincronización de catálogo y operaciones omnicanal WooCommerce con Python y GCP.",
        "topics": ["python", "woocommerce", "gcp", "automation", "ecommerce", "inventory"],
    },
    "motor-planos-sec-te1-chile": {
        "ramo": "Motor Planos Eléctricos SEC TE1 Chile",
        "docente": "Instalaciones Eléctricas Chile",
        "app_url": "",
        "descripcion": "Motor paramétrico en Python (ezdxf + Streamlit) para generación automática de planos eléctricos AutoCAD (.dxf), cuadros de cargas y cálculos SEC TE1.",
        "topics": ["python", "streamlit", "ezdxf", "sec-chile", "te1", "electrical-engineering"],
    },
    "motor-auditor-dte-finops": {
        "ramo": "Motor Auditor DTE y FinOps",
        "docente": "Auditoría Tributaria y FinOps",
        "app_url": "",
        "descripcion": "Motor en Python para extracción y auditoría automática de Documentos Tributarios Electrónicos (DTE SII) y prevención de pagos duplicados.",
        "topics": ["python", "sii-chile", "dte", "finops", "audit"],
    },
    "motor-conciliador-chile": {
        "ramo": "Motor Conciliador Financiero Chile",
        "docente": "Conciliación Bancaria y Facturación",
        "app_url": "",
        "descripcion": "Motor en Python para cruce y conciliación automatizada de cartolas bancarias, pagos y documentos tributarios en Chile.",
        "topics": ["python", "pandas", "fintech", "reconciliation", "sii-chile", "automation"],
    },
}


# ==============================================================================
# 1. CLIENTE GITHUB REST API (VÍA REQUESTS — SIN ERRORES DE URL NI PROXIES)
# ==============================================================================

def _gh_request(method, endpoint_o_url, token="", payload=None, timeout=20):
    if endpoint_o_url.startswith("http://") or endpoint_o_url.startswith("https://"):
        url = endpoint_o_url
    else:
        url = f"{GITHUB_API_BASE}/{endpoint_o_url.lstrip('/')}"

    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "ULagos-Central-Mando-2026",
    }
    if token and token.strip():
        headers["Authorization"] = f"Bearer {token.strip()}"

    resp = requests.request(
        method=method.upper(),
        url=url,
        headers=headers,
        json=payload if payload is not None else None,
        timeout=timeout,
    )
    if resp.status_code >= 400:
        try:
            msg = resp.json().get("message", resp.text)
        except Exception:
            msg = resp.text
        raise RuntimeError(f"GitHub HTTP {resp.status_code}: {msg}")

    body = resp.json() if resp.text.strip() else {}
    return body, dict(resp.headers)


@st.cache_data(ttl=60, show_spinner=False)
def verificar_token_github(token):
    if not token or not token.strip():
        return False, "", 0, 0, "Sin token configurado."
    try:
        data, headers = _gh_request("GET", "/user", token=token)
        rem = int(headers.get("X-RateLimit-Remaining", headers.get("x-ratelimit-remaining", 0)))
        lim = int(headers.get("X-RateLimit-Limit", headers.get("x-ratelimit-limit", 5000)))
        return True, data.get("login", ""), rem, lim, ""
    except Exception as exc:
        return False, "", 0, 0, str(exc)


@st.cache_data(ttl=90, show_spinner=False)
def listar_repos_live(usuario, token=""):
    repos_raw = []
    if token and token.strip():
        try:
            data, _ = _gh_request(
                "GET",
                "/user/repos?per_page=100&sort=updated&affiliation=owner",
                token=token,
            )
            repos_raw = [
                r for r in data
                if r.get("owner", {}).get("login", "").lower() == usuario.lower()
            ]
        except Exception:
            repos_raw = []

    if not repos_raw:
        data, _ = _gh_request(
            "GET",
            f"/users/{urllib.parse.quote(usuario)}/repos?per_page=100&sort=updated",
            token=token,
        )
        repos_raw = data

    resultado = []
    for d in repos_raw:
        resultado.append({
            "name": d.get("name", ""),
            "description": d.get("description") or "",
            "homepage": d.get("homepage") or "",
            "topics": d.get("topics") or [],
            "default_branch": d.get("default_branch", "main"),
            "private": bool(d.get("private", False)),
            "updated_at": (d.get("updated_at") or "")[:10],
            "html_url": d.get("html_url", ""),
        })
    return resultado


@st.cache_data(ttl=90, show_spinner=False)
def listar_archivos_repo(usuario, repo, branch="main", token=""):
    try:
        data, _ = _gh_request(
            "GET",
            f"/repos/{usuario}/{repo}/git/trees/{branch}?recursive=1",
            token=token,
        )
        rutas = [
            item["path"]
            for item in data.get("tree", [])
            if item.get("type") == "blob"
        ]
        return sorted(rutas)
    except Exception:
        return ["README.md", "requirements.txt", "app.py"]


def detectar_archivo_entrada_repo(usuario, repo, branch="main", token=""):
    archivos = listar_archivos_repo(usuario, repo, branch=branch, token=token)
    mapa_low = {a.lower(): a for a in archivos}
    for cand in ["app.py", "consola_web.py", "main.py", "streamlit_app.py"]:
        if cand in mapa_low:
            return mapa_low[cand]
    return "app.py"


def leer_archivo_repo(usuario, repo, ruta, token=""):
    ruta_enc = urllib.parse.quote(ruta.strip("/"), safe="/")
    data, _ = _gh_request("GET", f"/repos/{usuario}/{repo}/contents/{ruta_enc}", token=token)
    contenido = base64.b64decode(data.get("content", "")).decode("utf-8", errors="replace")
    return contenido, data.get("sha", "")


def _obtener_sha_archivo_repo(usuario, repo, ruta, token=""):
    ruta_enc = urllib.parse.quote(ruta.strip("/"), safe="/")
    data, _ = _gh_request("GET", f"/repos/{usuario}/{repo}/contents/{ruta_enc}", token=token)
    return data.get("sha", "")


def escribir_archivo_repo(usuario, repo, ruta, contenido_texto, token, mensaje_commit, sha=None):
    """Sube o actualiza un archivo de texto (str) o binario (bytes) en GitHub."""
    ruta_limpia = ruta.strip("/")
    ruta_enc = urllib.parse.quote(ruta_limpia, safe="/")

    if sha is None:
        try:
            sha = _obtener_sha_archivo_repo(usuario, repo, ruta_limpia, token=token)
        except Exception:
            sha = ""

    raw_bytes = (
        bytes(contenido_texto)
        if isinstance(contenido_texto, (bytes, bytearray))
        else str(contenido_texto).encode("utf-8")
    )
    payload = {
        "message": mensaje_commit,
        "content": base64.b64encode(raw_bytes).decode("ascii"),
    }
    if sha:
        payload["sha"] = sha

    data, _ = _gh_request("PUT", f"/repos/{usuario}/{repo}/contents/{ruta_enc}", token=token, payload=payload)
    return data


def actualizar_about_repo(usuario, repo, descripcion, homepage, topics_lista, token):
    res, _ = _gh_request(
        "PATCH",
        f"/repos/{usuario}/{repo}",
        token=token,
        payload={
            "description": descripcion.strip(),
            "homepage": homepage.strip(),
        },
    )

    if topics_lista is not None:
        limpios = []
        for t in topics_lista:
            slug = re.sub(r"[^a-z0-9-]", "", t.strip().lower().replace(" ", "-"))[:50]
            if slug and slug not in limpios:
                limpios.append(slug)
        _gh_request(
            "PUT",
            f"/repos/{usuario}/{repo}/topics",
            token=token,
            payload={"names": limpios[:20]},
        )

    return res


def modificar_requirements_repo(usuario, repo, agregar_lista, quitar_lista, token):
    try:
        req_txt, req_sha = leer_archivo_repo(usuario, repo, "requirements.txt", token=token)
    except Exception:
        req_txt, req_sha = "", ""

    lineas = [l.strip() for l in req_txt.splitlines() if l.strip()]
    quitar_set = {re.split(r"[=<>~!\[]", q)[0].strip().lower() for q in quitar_lista if q.strip()}

    nuevas_lineas = []
    quitados = []
    for l in lineas:
        base = re.split(r"[=<>~!\[]", l)[0].strip().lower()
        if base in quitar_set:
            quitados.append(l)
        else:
            nuevas_lineas.append(l)

    existentes = {re.split(r"[=<>~!\[]", l)[0].strip().lower() for l in nuevas_lineas}
    agregados = []
    for pkg in agregar_lista:
        pkg_c = pkg.strip()
        base = re.split(r"[=<>~!\[]", pkg_c)[0].strip().lower()
        if pkg_c and base not in existentes:
            nuevas_lineas.append(pkg_c)
            existentes.add(base)
            agregados.append(pkg_c)

    contenido_final = "\n".join(nuevas_lineas) + ("\n" if nuevas_lineas else "")
    resumen_cambios = []
    if agregados:
        resumen_cambios.append("+" + ",".join(agregados))
    if quitados:
        resumen_cambios.append("-" + ",".join(quitados))
    detalle_msg = " | ".join(resumen_cambios) if resumen_cambios else "sin cambios"
    msg = f"Central de Mando: requirements.txt ({detalle_msg})"

    escribir_archivo_repo(usuario, repo, "requirements.txt", contenido_final, token, msg, sha=req_sha)
    return agregados, quitados, contenido_final


def generar_snippet_conector_puente(nombre_repo, usuario_hub="mauriciovargas1516-ux"):
    url_raw = f"{GITHUB_RAW_BASE}/{usuario_hub}/github-context-extractor/main/app.py"
    return (
        f"\n\n{MARCADOR_PUENTE_INI}\n"
        "try:\n"
        "    import urllib.request as _ureq\n"
        f'    _url_puente = "{url_raw}"\n'
        '    _req_p = _ureq.Request(_url_puente, headers={"User-Agent": "ULagos-Bridge/1.0"})\n'
        "    with _ureq.urlopen(_req_p, timeout=12) as _resp_p:\n"
        '        _cod_hub = _resp_p.read().decode("utf-8")\n'
        '    _ns_hub = {"__name__": "puente_remoto_ulagos"}\n'
        "    exec(_cod_hub, _ns_hub)\n"
        '    if "ejecutar_nodo_receptor_puente" in _ns_hub:\n'
        f'        _ns_hub["ejecutar_nodo_receptor_puente"]("{nombre_repo}")\n'
        "except Exception:\n"
        "    pass\n"
        f"{MARCADOR_PUENTE_FIN}\n"
    )


def inyectar_bloque_marcado_en_archivo(
    usuario, repo, ruta, marcador_ini, marcador_fin, bloque_completo, token, mensaje_commit
):
    actual, sha = leer_archivo_repo(usuario, repo, ruta, token=token)
    if marcador_ini in actual and marcador_fin in actual:
        ini = actual.find(marcador_ini)
        fin = actual.find(marcador_fin) + len(marcador_fin)
        nuevo = actual[:ini].rstrip() + "\n\n" + bloque_completo.strip() + "\n" + actual[fin:].lstrip()
    else:
        nuevo = actual.rstrip() + "\n\n" + bloque_completo.strip() + "\n"

    escribir_archivo_repo(usuario, repo, ruta, nuevo.rstrip() + "\n", token, mensaje_commit, sha=sha)
    return True


def quitar_bloque_marcado_de_archivo(
    usuario, repo, ruta, marcador_ini, marcador_fin, token, mensaje_commit
):
    actual, sha = leer_archivo_repo(usuario, repo, ruta, token=token)
    if marcador_ini not in actual or marcador_fin not in actual:
        return False
    ini = actual.find(marcador_ini)
    fin = actual.find(marcador_fin) + len(marcador_fin)
    limpio = (actual[:ini].rstrip() + "\n" + actual[fin:].lstrip()).rstrip() + "\n"
    escribir_archivo_repo(usuario, repo, ruta, limpio, token, mensaje_commit, sha=sha)
    return True


def inyectar_badge_streamlit_en_readme(usuario, repo, app_url, token):
    badge_md = f"[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)]({app_url.strip()})"
    try:
        readme_txt, sha = leer_archivo_repo(usuario, repo, "README.md", token=token)
    except Exception:
        readme_txt, sha = f"# {repo}\n\n", ""

    patron_badge = r"\[!\[Open in Streamlit\]\(https://static\.streamlit\.io/badges/[^)]+\)\]\([^)]+\)"
    if re.search(patron_badge, readme_txt):
        nuevo_txt = re.sub(patron_badge, badge_md, readme_txt, count=1)
    else:
        lineas = readme_txt.splitlines()
        if lineas and lineas[0].lstrip().startswith("#"):
            nuevo_txt = "\n".join([lineas[0], "", badge_md, ""] + lineas[1:]).rstrip() + "\n"
        else:
            nuevo_txt = badge_md + "\n\n" + readme_txt

    escribir_archivo_repo(
        usuario,
        repo,
        "README.md",
        nuevo_txt,
        token,
        f"Central de Mando: actualizar badge de Streamlit en README.md ({repo})",
        sha=sha,
    )
    return True


def generar_plantilla_readme(repo_nom, meta, cuadrillas_lit):
    ramo = meta.get("ramo", repo_nom)
    docente = meta.get("docente", "Universidad de Los Lagos")
    app_url = meta.get("app_url", "")
    desc = meta.get("descripcion", "Aplicación web interactiva desarrollada en Python y Streamlit.")

    linea_badge = (
        f"[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)]({app_url})\n\n"
        if app_url and app_url.startswith("http")
        else ""
    )

    tarjetas_md = []
    if cuadrillas_lit and ramo in cuadrillas_lit:
        for t in cuadrillas_lit[ramo].get("tarjetas", []):
            tarjetas_md.append(f"* **{t['titulo']}:** {t['tip']} *(Fuente: {t['fuente']})*")
    bloque_lit = (
        "\n".join(tarjetas_md)
        if tarjetas_md
        else "* Integrado al Super Hub Académico ULagos 2026 (`github-context-extractor`)."
    )

    bt = chr(96) * 3
    url_visible = app_url if app_url else "Pendiente de despliegue"

    return (
        f"# {ramo} — Plataforma Interactiva\n\n"
        f"{linea_badge}**Proyecto / Asignatura:** {ramo}  \n"
        f"**Contexto / Docente:** {docente}  \n"
        f"**Autor:** Mauricio Alejandro Vargas Ortega  \n"
        f"**Aplicación en Vivo:** {url_visible}\n\n"
        f"---\n\n"
        f"## 1. Descripción del Sistema\n"
        f"{desc}\n\n"
        f"---\n\n"
        f"## 2. Respaldo Metodológico y Referencias\n"
        f"{bloque_lit}\n\n"
        f"---\n\n"
        f"## 3. Ejecución Local\n"
        f"{bt}bash\n"
        f"git clone https://github.com/mauriciovargas1516-ux/{repo_nom}.git\n"
        f"cd {repo_nom}\n"
        f"pip install -r requirements.txt\n"
        f"streamlit run app.py\n"
        f"{bt}\n"
    )


# ==============================================================================
# 2. INTERFAZ PRINCIPAL DE LA PESTAÑA 5 (SUPER CENTRAL DE MANDO)
# ==============================================================================

def renderizar_central_de_mando(
    usuario_gh,
    token_gh,
    mapa_repos=None,
    cuadrillas_lit=None,
    fn_preview_puente=None,
):
    mapa_combinado = dict(CATALOGO_EXTRA_ABOUT)
    if mapa_repos:
        mapa_combinado.update(mapa_repos)
    cuadrillas_lit = cuadrillas_lit or {}

    st.markdown(
        "<div class='sec-header'>5. SUPER CENTRAL DE MANDO — GESTIÓN REMOTA MULTI-REPOSITORIO (GITHUB API)</div>",
        unsafe_allow_html=True,
    )

    token_ok, login_gh, rem_api, lim_api, err_tok = verificar_token_github(token_gh)
    c_st1, c_st2 = st.columns([3.2, 0.8])
    with c_st1:
        if token_ok:
            st.success(
                f"Conectado a GitHub API como **@{login_gh}** | Cuota disponible: **{rem_api:,} / {lim_api:,}** peticiones."
            )
        else:
            st.warning(
                "Modo solo lectura. Ingresa tu Clave Admin en la barra lateral izquierda "
                "para habilitar la escritura remota con GITHUB_TOKEN protegido en servidor."
            )
            if token_gh and token_gh.strip() and err_tok:
                st.error(f"Detalle del token: {err_tok}")
    with c_st2:
        if st.button("Recargar Repos", use_container_width=True, key="cm_reload_repos"):
            verificar_token_github.clear()
            listar_repos_live.clear()
            listar_archivos_repo.clear()
            st.rerun()

    try:
        repos_live = listar_repos_live(usuario_gh, token=token_gh)
    except Exception:
        repos_live = [
            {
                "name": k,
                "description": v.get("descripcion", ""),
                "homepage": v.get("app_url", ""),
                "topics": v.get("topics", ["python", "streamlit"]),
                "default_branch": "main",
                "private": False,
                "updated_at": "",
                "html_url": v.get("repo_url", f"https://github.com/{usuario_gh}/{k}"),
            }
            for k, v in mapa_combinado.items()
        ]
        st.caption("Mostrando catálogo local de repositorios (activa Modo Admin para listar en vivo desde GitHub API).")

    mapa_live = {r["name"]: r for r in repos_live}
    nombres_repos = list(mapa_live.keys())
    if not nombres_repos:
        st.info("No se encontraron repositorios para este usuario.")
        return

    repos_default = [
        r for r in [
            "PROYECTOS-2026",
            "DESARROLLO-Y-GESTION-TERRITORIAL-2026",
            "FINANZAS-AVANZADAS-2026",
            "GESTION-TRIBUTARIA-2026",
        ]
        if r in mapa_live
    ] or nombres_repos[:1]

    sub_about, sub_req, sub_readme, sub_files, sub_puente = st.tabs([
        "5.1 About, URL y Topics",
        "5.2 requirements.txt y Config",
        "5.3 README.md y Badges",
        "5.4 Editor y Envío Masivo de Archivos",
        "5.5 Puente Drive en app.py",
    ])

    # --------------------------------------------------------------------------
    # 5.1 GESTOR DE ABOUT (RESUMEN + INDIVIDUAL + LOTE)
    # --------------------------------------------------------------------------
    with sub_about:
        df_resumen = pd.DataFrame([
            {
                "Repositorio": r["name"],
                "Visibilidad": "Privado" if r["private"] else "Público",
                "Descripción (About)": r["description"] or "(vacía)",
                "Sitio Web / Streamlit": r["homepage"] or "(vacío)",
                "Topics": ", ".join(r["topics"]) if r["topics"] else "(sin topics)",
                "Actualizado": r["updated_at"],
            }
            for r in repos_live
        ])
        st.dataframe(df_resumen, use_container_width=True, hide_index=True)

        c_ab1, c_ab2 = st.columns([1.4, 2.6])
        with c_ab1:
            repo_ab = st.selectbox(
                "Repositorio a editar:",
                options=nombres_repos,
                key="cm_ab_repo",
            )
            info_live = mapa_live[repo_ab]
            info_cat = mapa_combinado.get(repo_ab, {})

            st.caption(f"**Rama por defecto:** `{info_live['default_branch']}`")
            if info_cat:
                st.caption(f"**Proyecto / Ramo:** {info_cat.get('ramo', '-')}")

            st.divider()
            st.markdown("**Sincronización rápida desde catálogo:**")
            repos_vacios = [r["name"] for r in repos_live if not r["description"] and r["name"] in mapa_combinado]
            repos_sync_ab = st.multiselect(
                "Repos a sincronizar en lote:",
                options=[r for r in nombres_repos if r in mapa_combinado],
                default=repos_vacios or [r for r in repos_default if r in mapa_combinado],
                key="cm_ab_lote_sel",
            )
            if st.button("SINCRONIZAR ABOUT EN LOTE", use_container_width=True, key="cm_ab_lote_btn"):
                if not token_ok:
                    st.error("Activa el Modo Admin en la barra lateral.")
                else:
                    for r_nom in repos_sync_ab:
                        cat_r = mapa_combinado[r_nom]
                        live_r = mapa_live[r_nom]
                        url_usar = live_r["homepage"] or cat_r.get("app_url", "")
                        topics_usar = cat_r.get("topics") or live_r["topics"] or ["python", "streamlit"]
                        try:
                            actualizar_about_repo(
                                usuario_gh, r_nom, cat_r.get("descripcion", ""), url_usar, topics_usar, token_gh
                            )
                            st.success(f"`{r_nom}` actualizado.")
                        except Exception as ex:
                            st.error(f"Error en `{r_nom}`: {ex}")
                    listar_repos_live.clear()

        with c_ab2:
            desc_init = info_live["description"] or info_cat.get("descripcion", "")
            url_init = info_live["homepage"] or info_cat.get("app_url", "")
            top_init = ", ".join(info_live["topics"] or info_cat.get("topics", ["python", "streamlit"]))

            nueva_desc = st.text_input(
                "Descripción (About):",
                value=desc_init,
                key=f"cm_desc_{repo_ab}",
            )
            nueva_url = st.text_input(
                "URL App Streamlit (Homepage):",
                value=url_init,
                key=f"cm_url_{repo_ab}",
            )
            nuevos_topics = st.text_input(
                "Topics (separados por coma):",
                value=top_init,
                key=f"cm_top_{repo_ab}",
            )

            if st.button(f"GUARDAR ABOUT EN {repo_ab}", type="primary", use_container_width=True, key="cm_ab_save_one"):
                if not token_ok:
                    st.error("Activa el Modo Admin en la barra lateral.")
                else:
                    try:
                        lista_t = [t.strip() for t in nuevos_topics.split(",") if t.strip()]
                        actualizar_about_repo(usuario_gh, repo_ab, nueva_desc, nueva_url, lista_t, token_gh)
                        listar_repos_live.clear()
                        st.success(f"About, Homepage y Topics guardados en `{repo_ab}`.")
                    except Exception as ex:
                        st.error(f"No se pudo actualizar `{repo_ab}`: {ex}")

    # --------------------------------------------------------------------------
    # 5.2 INYECTOR MASIVO DE REQUIREMENTS.TXT Y CONFIG.TOML
    # --------------------------------------------------------------------------
    with sub_req:
        repos_req_dst = st.multiselect(
            "Repositorios destino (puedes elegir uno, varios o todos):",
            options=nombres_repos,
            default=repos_default,
            key="cm_req_repos",
        )

        col_r1, col_r2 = st.columns([1.8, 1.8])
        with col_r1:
            st.markdown("#### Inyectar o Quitar Librerías (`requirements.txt`)")
            pkgs_add = st.multiselect(
                "Librerías a asegurar / agregar:",
                options=PAQUETES_CATALOGO,
                default=["requests", "beautifulsoup4", "pypdf", "google-auth", "openpyxl"],
                key="cm_req_add",
            )
            pkgs_extra = st.text_input(
                "Otras librerías a agregar (separadas por coma):",
                placeholder="ej. yfinance, fpdf2, xlsxwriter",
                key="cm_req_extra",
            )
            pkgs_del = st.text_input(
                "Librerías a QUITAR en lote (opcional, separadas por coma):",
                placeholder="ej. selenium, lxml",
                key="cm_req_del",
            )

            if st.button("APLICAR CAMBIOS EN requirements.txt (LOTE)", type="primary", use_container_width=True, key="cm_req_apply"):
                if not token_ok:
                    st.error("Activa el Modo Admin en la barra lateral.")
                elif not repos_req_dst:
                    st.warning("Selecciona al menos un repositorio.")
                else:
                    lista_add = list(pkgs_add) + [p.strip() for p in pkgs_extra.split(",") if p.strip()]
                    lista_del = [p.strip() for p in pkgs_del.split(",") if p.strip()]
                    for r_dst in repos_req_dst:
                        try:
                            ag, qu, _ = modificar_requirements_repo(
                                usuario_gh, r_dst, lista_add, lista_del, token_gh
                            )
                            st.success(
                                f"`{r_dst}/requirements.txt` -> Agregados: {ag or 'ninguno'} | Quitados: {qu or 'ninguno'}"
                            )
                        except Exception as ex:
                            st.error(f"Error en `{r_dst}`: {ex}")

        with col_r2:
            st.markdown("#### Estandarizar `.streamlit/config.toml` en Lote")
            toml_edit = st.text_area(
                "Contenido de `.streamlit/config.toml` a desplegar:",
                value=CONFIG_TOML_CLARO,
                height=210,
                key="cm_toml_txt",
            )
            if st.button("INYECTAR .streamlit/config.toml EN LOTE", use_container_width=True, key="cm_toml_apply"):
                if not token_ok:
                    st.error("Activa el Modo Admin en la barra lateral.")
                elif not repos_req_dst:
                    st.warning("Selecciona al menos un repositorio.")
                else:
                    for r_dst in repos_req_dst:
                        try:
                            escribir_archivo_repo(
                                usuario_gh,
                                r_dst,
                                ".streamlit/config.toml",
                                toml_edit,
                                token_gh,
                                "Central de Mando: estandarizar .streamlit/config.toml",
                            )
                            st.success(f"`{r_dst}/.streamlit/config.toml` actualizado.")
                        except Exception as ex:
                            st.error(f"Error en `{r_dst}`: {ex}")

    # --------------------------------------------------------------------------
    # 5.3 GESTOR DE README.MD Y BADGES DE STREAMLIT
    # --------------------------------------------------------------------------
    with sub_readme:
        c_rm1, c_rm2 = st.columns([1.6, 2.4])
        with c_rm1:
            st.markdown("#### Inyectar / Actualizar Badge de Streamlit en Lote")
            st.caption(
                "Usa la URL guardada en el `Homepage` de cada repositorio (o en el catálogo) "
                "e inserta el botón `Open in Streamlit` sin borrar el resto de tu README."
            )
            repos_badge = st.multiselect(
                "Repositorios destino para Badge:",
                options=nombres_repos,
                default=repos_default,
                key="cm_rm_badge_repos",
            )
            if st.button("INYECTAR BADGE STREAMLIT EN LOTE", type="primary", use_container_width=True, key="cm_rm_badge_btn"):
                if not token_ok:
                    st.error("Activa el Modo Admin en la barra lateral.")
                else:
                    for r_nom in repos_badge:
                        url_app = mapa_live[r_nom]["homepage"] or mapa_combinado.get(r_nom, {}).get("app_url", "")
                        if not url_app or not url_app.startswith("http"):
                            st.warning(f"`{r_nom}` omitido: no tiene URL de Streamlit configurada en About.")
                            continue
                        try:
                            inyectar_badge_streamlit_en_readme(usuario_gh, r_nom, url_app, token_gh)
                            st.success(f"Badge actualizado en `{r_nom}/README.md` -> {url_app}")
                        except Exception as ex:
                            st.error(f"Error en `{r_nom}`: {ex}")

        with c_rm2:
            st.markdown("#### Generador y Editor Rápido de `README.md`")
            repo_rm = st.selectbox("Selecciona repositorio:", options=nombres_repos, key="cm_rm_one")
            ta_rm_key = f"cm_rm_ta_{repo_rm}"

            b_c1, b_c2 = st.columns(2)
            with b_c1:
                if st.button("Cargar README actual desde GitHub", use_container_width=True, key="cm_rm_load"):
                    try:
                        txt_act, _ = leer_archivo_repo(usuario_gh, repo_rm, "README.md", token=token_gh)
                        st.session_state[ta_rm_key] = txt_act
                        st.rerun()
                    except Exception as ex:
                        st.warning(f"No se pudo leer README actual ({ex}).")
            with b_c2:
                if st.button("Generar Plantilla Ejecutiva", use_container_width=True, key="cm_rm_tpl"):
                    meta_mix = dict(mapa_combinado.get(repo_rm, {}))
                    if mapa_live[repo_rm]["homepage"]:
                        meta_mix["app_url"] = mapa_live[repo_rm]["homepage"]
                    if mapa_live[repo_rm]["description"]:
                        meta_mix["descripcion"] = mapa_live[repo_rm]["description"]
                    st.session_state[ta_rm_key] = generar_plantilla_readme(repo_rm, meta_mix, cuadrillas_lit)
                    st.rerun()

            if ta_rm_key not in st.session_state:
                try:
                    txt_init, _ = leer_archivo_repo(usuario_gh, repo_rm, "README.md", token=token_gh)
                    st.session_state[ta_rm_key] = txt_init
                except Exception:
                    st.session_state[ta_rm_key] = f"# {repo_rm}\n"

            nuevo_readme = st.text_area(
                f"Editando `{repo_rm}/README.md`:",
                height=320,
                key=ta_rm_key,
            )
            if st.button(f"GUARDAR README.md EN {repo_rm}", type="primary", use_container_width=True, key="cm_rm_save"):
                if not token_ok:
                    st.error("Activa el Modo Admin en la barra lateral.")
                else:
                    try:
                        escribir_archivo_repo(
                            usuario_gh, repo_rm, "README.md", nuevo_readme, token_gh,
                            f"Central de Mando: actualizar README.md en {repo_rm}",
                        )
                        st.success(f"`{repo_rm}/README.md` guardado en GitHub.")
                    except Exception as ex:
                        st.error(f"Error al guardar README.md: {ex}")

    # --------------------------------------------------------------------------
    # 5.4 EDITOR EN VIVO Y ENVÍO MASIVO DE ARCHIVOS (BROADCAST)
    # --------------------------------------------------------------------------
    with sub_files:
        modo_arch = st.radio(
            "Operación sobre archivos:",
            options=[
                "Subir varios archivos a 1 repositorio (Lote)",
                "Editar o Crear 1 archivo en un repositorio",
                "Inyectar un mismo archivo en MÚLTIPLES repositorios a la vez",
            ],
            horizontal=True,
            key="cm_files_mode",
        )

        if modo_arch == "Subir varios archivos a 1 repositorio (Lote)":
            st.caption(
                "Arrastra todos los archivos que quieras actualizar (.py, .md, .toml, .xlsx, .docx, etc.), "
                "ajusta el nombre destino en la tabla si hace falta y súbelos al repositorio en 1 clic."
            )
            c_m1, c_m2 = st.columns([1.6, 1.4])
            with c_m1:
                repo_multi = st.selectbox("1. Repositorio destino:", options=nombres_repos, key="cm_multi_repo")
            with c_m2:
                carpeta_multi = st.text_input(
                    "2. Subcarpeta destino (opcional, ej. .streamlit):",
                    value="",
                    key="cm_multi_dir",
                ).strip().strip("/")

            archivos_lote = st.file_uploader(
                "3. Arrastra o selecciona uno o varios archivos locales:",
                accept_multiple_files=True,
                key="cm_multi_up",
            )

            if archivos_lote:
                filas_preview = []
                mapa_bytes_lote = {}
                for f_obj in archivos_lote:
                    raw_b = f_obj.getvalue()
                    ruta_sug = f"{carpeta_multi}/{f_obj.name}" if carpeta_multi else f_obj.name
                    filas_preview.append({
                        "Archivo local": f_obj.name,
                        "Ruta destino en GitHub (editable)": ruta_sug,
                        "Tamaño (KB)": round(len(raw_b) / 1024.0, 1),
                    })
                    mapa_bytes_lote[f_obj.name] = raw_b

                df_lote_edit = st.data_editor(
                    pd.DataFrame(filas_preview),
                    disabled=["Archivo local", "Tamaño (KB)"],
                    use_container_width=True,
                    hide_index=True,
                    key=f"cm_multi_tbl_{repo_multi}_{carpeta_multi}_{len(archivos_lote)}",
                )
                msg_multi = st.text_input(
                    "4. Mensaje de commit:",
                    value=f"Central de Mando: actualizar {len(archivos_lote)} archivo(s) en {repo_multi}",
                    key="cm_multi_commit",
                )
                if st.button(
                    f"SUBIR {len(archivos_lote)} ARCHIVO(S) A {repo_multi}",
                    type="primary",
                    use_container_width=True,
                    key="cm_multi_go",
                ):
                    if not token_ok:
                        st.error("Activa el Modo Admin en la barra lateral.")
                    else:
                        barra_m = st.progress(0.0, text="Subiendo archivos a GitHub...")
                        n_tot = len(df_lote_edit)
                        ok_cnt = 0
                        for idx_row, fila_m in enumerate(df_lote_edit.itertuples(index=False)):
                            nom_loc = fila_m[0]
                            ruta_dest = str(fila_m[1]).strip().strip("/")
                            barra_m.progress(idx_row / max(n_tot, 1), text=f"Subiendo {ruta_dest} ({idx_row + 1}/{n_tot})...")
                            if not ruta_dest:
                                st.warning(f"Se omitió `{nom_loc}` porque la ruta destino quedó vacía.")
                                continue
                            try:
                                escribir_archivo_repo(
                                    usuario_gh,
                                    repo_multi,
                                    ruta_dest,
                                    mapa_bytes_lote[nom_loc],
                                    token_gh,
                                    msg_multi,
                                )
                                st.success(f"`{repo_multi}/{ruta_dest}` actualizado.")
                                ok_cnt += 1
                            except Exception as ex:
                                st.error(f"Error al subir `{ruta_dest}`: {ex}")
                        barra_m.progress(1.0, text=f"Completado: {ok_cnt}/{n_tot} archivos subidos.")
                        listar_archivos_repo.clear()

        elif modo_arch == "Editar o Crear 1 archivo en un repositorio":
            c_e1, c_e2, c_e3 = st.columns([1.3, 1.5, 1.2])
            with c_e1:
                repo_ed = st.selectbox("1. Repositorio:", options=nombres_repos, key="cm_ed_repo")
            rama_ed = mapa_live[repo_ed]["default_branch"]
            lista_arch = listar_archivos_repo(usuario_gh, repo_ed, branch=rama_ed, token=token_gh)
            opciones_arch = lista_arch + ["[+ Crear archivo nuevo...]"]
            with c_e2:
                entry_def = detectar_archivo_entrada_repo(usuario_gh, repo_ed, branch=rama_ed, token=token_gh)
                idx_def = opciones_arch.index(entry_def) if entry_def in opciones_arch else 0
                arch_sel = st.selectbox("2. Archivo:", options=opciones_arch, index=idx_def, key=f"cm_ed_arch_{repo_ed}")
            with c_e3:
                if arch_sel == "[+ Crear archivo nuevo...]":
                    ruta_ed = st.text_input("Ruta del nuevo archivo:", value="utils_nuevo.py", key="cm_ed_new_path")
                else:
                    ruta_ed = arch_sel
                    st.caption(f"Rama `{rama_ed}`")
                    if st.button("Recargar desde GitHub", use_container_width=True, key="cm_ed_reload"):
                        ta_ed_key_tmp = f"cm_ed_ta_{repo_ed}_{ruta_ed}"
                        if ta_ed_key_tmp in st.session_state:
                            del st.session_state[ta_ed_key_tmp]
                        st.rerun()

            ta_ed_key = f"cm_ed_ta_{repo_ed}_{ruta_ed}"
            if ta_ed_key not in st.session_state:
                if arch_sel == "[+ Crear archivo nuevo...]":
                    st.session_state[ta_ed_key] = ""
                else:
                    try:
                        txt_f, _ = leer_archivo_repo(usuario_gh, repo_ed, ruta_ed, token=token_gh)
                        st.session_state[ta_ed_key] = txt_f
                    except Exception:
                        st.session_state[ta_ed_key] = ""

            contenido_ed = st.text_area(
                f"Contenido de `{repo_ed}/{ruta_ed}`:",
                height=380,
                key=ta_ed_key,
            )
            msg_commit_ed = st.text_input(
                "Mensaje de commit:",
                value=f"Central de Mando: actualizar {ruta_ed}",
                key="cm_ed_commit",
            )
            if st.button(f"GUARDAR {repo_ed}/{ruta_ed} EN GITHUB", type="primary", use_container_width=True, key="cm_ed_save"):
                if not token_ok:
                    st.error("Activa el Modo Admin en la barra lateral.")
                else:
                    try:
                        escribir_archivo_repo(usuario_gh, repo_ed, ruta_ed, contenido_ed, token_gh, msg_commit_ed)
                        listar_archivos_repo.clear()
                        st.success(f"Archivo `{repo_ed}/{ruta_ed}` actualizado correctamente.")
                    except Exception as ex:
                        st.error(f"Error al guardar `{ruta_ed}`: {ex}")

        else:
            st.caption(
                "Ideal para distribuir en 1 clic un mismo archivo (.gitignore, packages.txt, módulo común) "
                "a múltiples repositorios a la vez."
            )
            repos_bcast = st.multiselect(
                "1. Repositorios destino:",
                options=nombres_repos,
                default=repos_default,
                key="cm_bcast_repos",
            )
            ruta_bcast = st.text_input(
                "2. Ruta exacta del archivo a crear/sobrescribir en todos:",
                value=".gitignore",
                key="cm_bcast_path",
            )
            archivo_subido = st.file_uploader(
                "Opcional: sube un archivo local para cargar su contenido automáticamente",
                key="cm_bcast_up",
            )

            # Sincronización segura entre file_uploader y text_area (evita sobrescribir con .gitignore por defecto)
            if "cm_bcast_txt" not in st.session_state:
                st.session_state["cm_bcast_txt"] = "__pycache__/\n*.pyc\n.env\n.streamlit/secrets.toml\n"

            if archivo_subido is not None:
                firma_up = (archivo_subido.name, archivo_subido.size)
                if st.session_state.get("cm_bcast_last_up") != firma_up:
                    st.session_state["cm_bcast_txt"] = archivo_subido.getvalue().decode("utf-8", errors="replace")
                    st.session_state["cm_bcast_last_up"] = firma_up
                st.info(f"Contenido cargado desde `{archivo_subido.name}` ({archivo_subido.size:,} bytes).")
            elif "cm_bcast_last_up" in st.session_state:
                del st.session_state["cm_bcast_last_up"]

            contenido_bcast = st.text_area(
                "3. Contenido del archivo a distribuir:",
                height=240,
                key="cm_bcast_txt",
            )
            if st.button("DESPLEGAR ARCHIVO EN TODOS LOS REPOS SELECCIONADOS", type="primary", use_container_width=True, key="cm_bcast_go"):
                if not token_ok:
                    st.error("Activa el Modo Admin en la barra lateral.")
                elif not repos_bcast or not ruta_bcast.strip():
                    st.warning("Selecciona al menos un repositorio e indica la ruta del archivo.")
                else:
                    for r_dst in repos_bcast:
                        try:
                            escribir_archivo_repo(
                                usuario_gh,
                                r_dst,
                                ruta_bcast,
                                contenido_bcast,
                                token_gh,
                                f"Central de Mando: desplegar {ruta_bcast}",
                            )
                            st.success(f"`{r_dst}/{ruta_bcast}` desplegado.")
                        except Exception as ex:
                            st.error(f"Error en `{r_dst}`: {ex}")
                    listar_archivos_repo.clear()

    # --------------------------------------------------------------------------
    # 5.5 INYECTOR NO DESTRUCTIVO DEL PUENTE EN VIVO (DETECTA app.py / consola_web.py)
    # --------------------------------------------------------------------------
    with sub_puente:
        st.write(
            "Inyecta o actualiza el bloque conector al final del archivo principal (`app.py` o `consola_web.py`) "
            "en los repositorios seleccionados **sin borrar ni alterar tu código original**, y asegura las librerías en `requirements.txt`."
        )

        c_p1, c_p2 = st.columns([1.7, 2.3])
        with c_p1:
            repos_puente_sel = st.multiselect(
                "Repositorios donde conectar/desacoplar el Puente en Vivo:",
                options=[r for r in nombres_repos if r != "github-context-extractor"],
                default=[r for r in repos_default if r != "github-context-extractor"],
                key="cm_puente_repos",
            )
            asegurar_reqs_puente = st.checkbox(
                "Asegurar también `requests`, `pypdf`, `google-auth` y `openpyxl` en requirements.txt",
                value=True,
                key="cm_puente_reqs",
            )
            btn_iny = st.button(
                "INYECTAR / ACTUALIZAR PUENTE EN LOTE",
                type="primary",
                use_container_width=True,
                key="cm_puente_iny",
            )
            btn_des = st.button(
                "Desacoplar Puente y Restaurar Archivo Original",
                use_container_width=True,
                key="cm_puente_des",
            )

        with c_p2:
            repo_prev = st.selectbox(
                "Vista previa del snippet que se añade al final del archivo principal:",
                options=repos_puente_sel or nombres_repos,
                key="cm_puente_prev",
            )
            st.code(generar_snippet_conector_puente(repo_prev, usuario_gh).strip(), language="python")

        if btn_iny:
            if not token_ok:
                st.error("Activa el Modo Admin en la barra lateral.")
            elif not repos_puente_sel:
                st.warning("Selecciona al menos un repositorio.")
            else:
                for r_dst in repos_puente_sel:
                    try:
                        if asegurar_reqs_puente:
                            modificar_requirements_repo(
                                usuario_gh, r_dst, ["requests", "pypdf", "google-auth", "openpyxl"], [], token_gh
                            )
                        rama_dst = mapa_live[r_dst]["default_branch"]
                        archivo_entry = detectar_archivo_entrada_repo(usuario_gh, r_dst, branch=rama_dst, token=token_gh)
                        snippet = generar_snippet_conector_puente(r_dst, usuario_gh)
                        inyectar_bloque_marcado_en_archivo(
                            usuario_gh,
                            r_dst,
                            archivo_entry,
                            MARCADOR_PUENTE_INI,
                            MARCADOR_PUENTE_FIN,
                            snippet,
                            token_gh,
                            f"Central de Mando: conectar Puente en Vivo en {r_dst}/{archivo_entry}",
                        )
                        st.success(f"`{r_dst}/{archivo_entry}` conectado correctamente.")
                    except Exception as ex:
                        st.error(f"Error en `{r_dst}`: {ex}")

        if btn_des:
            if not token_ok:
                st.error("Activa el Modo Admin en la barra lateral.")
            else:
                for r_dst in repos_puente_sel:
                    try:
                        rama_dst = mapa_live[r_dst]["default_branch"]
                        archivo_entry = detectar_archivo_entrada_repo(usuario_gh, r_dst, branch=rama_dst, token=token_gh)
                        removido = quitar_bloque_marcado_de_archivo(
                            usuario_gh,
                            r_dst,
                            archivo_entry,
                            MARCADOR_PUENTE_INI,
                            MARCADOR_PUENTE_FIN,
                            token_gh,
                            f"Central de Mando: desacoplar Puente en {r_dst}/{archivo_entry}",
                        )
                        if removido:
                            st.success(f"Puente desacoplado limpiamente de `{r_dst}/{archivo_entry}`.")
                        else:
                            st.info(f"`{r_dst}/{archivo_entry}` no tenía el bloque del puente instalado.")
                    except Exception as ex:
                        st.error(f"Error al desacoplar `{r_dst}`: {ex}")

        if callable(fn_preview_puente):
            st.divider()
            st.markdown("#### Previsualización del Nodo Receptor")
            repo_sim = st.selectbox(
                "Simular cómo se ve el módulo dentro de:",
                options=repos_default or nombres_repos,
                key="cm_sim_nodo",
            )
            fn_preview_puente(repo_sim)
