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
import urllib.request
import urllib.error
import pandas as pd
import streamlit as st


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
    "plotly",
    "matplotlib",
    "scipy",
    "networkx",
    "beautifulsoup4",
    "python-docx",
    "statsmodels",
    "scikit-learn",
]


# ==============================================================================
# 1. CLIENTE GITHUB REST API (COMPATIBLE CON TOKENS CLASSIC Y FINE-GRAINED)
# ==============================================================================

def _gh_request(method, url, token="", payload=None, timeout=20):
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "ULagos-Central-Mando-2026",
    }
    if token and token.strip():
        headers["Authorization"] = f"Bearer {token.strip()}"

    data_bytes = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data_bytes = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            body = json.loads(raw) if raw.strip() else {}
            return body, dict(resp.headers)
    except urllib.error.HTTPError as err:
        detalle = err.read().decode("utf-8", errors="replace")
        try:
            msg = json.loads(detalle).get("message", detalle)
        except Exception:
            msg = detalle
        raise RuntimeError(f"GitHub HTTP {err.code}: {msg}") from err


@st.cache_data(ttl=60, show_spinner=False)
def verificar_token_github(token):
    if not token or not token.strip():
        return False, "", 0, 0, "Sin token configurado."
    try:
        data, headers = _gh_request("GET", "https://api.github.com/user", token=token)
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
                "https://api.github.com/user/repos?per_page=100&sort=updated&affiliation=owner",
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
            f"https://api.github.com/users/{urllib.parse.quote(usuario)}/repos?per_page=100&sort=updated",
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
    url = f"https://api.github.com/repos/{usuario}/{repo}/git/trees/{branch}?recursive=1"
    try:
        data, _ = _gh_request("GET", url, token=token)
        rutas = [
            item["path"]
            for item in data.get("tree", [])
            if item.get("type") == "blob"
        ]
        return sorted(rutas)
    except Exception:
        return ["README.md", "requirements.txt", "app.py"]


def leer_archivo_repo(usuario, repo, ruta, token=""):
    ruta_enc = urllib.parse.quote(ruta.strip("/"), safe="/")
    url = f"https://api.github.com/repos/{usuario}/{repo}/contents/{ruta_enc}"
    data, _ = _gh_request("GET", url, token=token)
    contenido = base64.b64decode(data.get("content", "")).decode("utf-8", errors="replace")
    return contenido, data.get("sha", "")


def escribir_archivo_repo(usuario, repo, ruta, contenido_texto, token, mensaje_commit, sha=None):
    ruta_limpia = ruta.strip("/")
    ruta_enc = urllib.parse.quote(ruta_limpia, safe="/")
    url = f"https://api.github.com/repos/{usuario}/{repo}/contents/{ruta_enc}"

    if sha is None:
        try:
            _, sha = leer_archivo_repo(usuario, repo, ruta_limpia, token=token)
        except Exception:
            sha = ""

    payload = {
        "message": mensaje_commit,
        "content": base64.b64encode(contenido_texto.encode("utf-8")).decode("ascii"),
    }
    if sha:
        payload["sha"] = sha

    data, _ = _gh_request("PUT", url, token=token, payload=payload)
    return data


def actualizar_about_repo(usuario, repo, descripcion, homepage, topics_lista, token):
    url_repo = f"https://api.github.com/repos/{usuario}/{repo}"
    res, _ = _gh_request(
        "PATCH",
        url_repo,
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
        url_topics = f"https://api.github.com/repos/{usuario}/{repo}/topics"
        _gh_request("PUT", url_topics, token=token, payload={"names": limpios[:20]})

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
    msg = f"Central de Mando: requirements.txt ({' | '.join(resumen_cambios) or 'sin cambios'})"

    escribir_archivo_repo(usuario, repo, "requirements.txt", contenido_final, token, msg, sha=req_sha)
    return agregados, quitados, contenido_final


def generar_snippet_conector_puente(nombre_repo, usuario_hub="mauriciovargas1516-ux"):
    return (
        f"\n\n{MARCADOR_PUENTE_INI}\n"
        "try:\n"
        "    import urllib.request as _ureq\n"
        f'    _url_puente = "https://raw.githubusercontent.com/{usuario_hub}/github-context-extractor/main/app.py"\n'
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

    return f"""# {ramo} — Plataforma Interactiva ULagos 2026

{linea_badge}**Asignatura:** {ramo}  
**Docente:** {docente}  
**Autor:** Mauricio Alejandro Vargas Ortega — Ingeniería Comercial, Universidad de Los Lagos  
**Aplicación en Vivo:** {app_url or 'Pendiente de despliegue'}

---

## 1. Descripción del Sistema
{desc}

---

## 2. Respaldo Metodológico y Referencias
{bloque_lit}

---

## 3. Ejecución Local
```bash
git clone [https://github.com/mauriciovargas1516-ux/](https://github.com/mauriciovargas1516-ux/){repo_nom}.git
cd {repo_nom}
pip install -r requirements.txt
streamlit run app.py
