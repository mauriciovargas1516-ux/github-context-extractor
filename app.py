import urllib.request
import urllib.parse
import json
import streamlit as st

st.set_page_config(
    page_title="Hub de Aplicaciones y Extractor de Contexto GitHub",
    layout="wide",
)

# Estilo Corporativo Limpio (Conservando paleta de colores ejecutiva)
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
    .sec-label {
        font-size: 15px; font-weight: 700; color: #0F172A;
        border-bottom: 2px solid #E2E8F0; padding-bottom: 6px; margin-bottom: 12px;
    }
    </style>
    <div class="corp-banner">
        <div class="corp-title">HUB DE APLICACIONES Y EXTRACTOR DE CONTEXTO GITHUB</div>
        <div class="corp-sub">Ingeniería de Contexto y Consolidación de Código Fuente en Tiempo Real vía API REST | mauriciovargas1516-ux</div>
    </div>
    """,
    unsafe_allow_html=True,
)

USUARIO = "mauriciovargas1516-ux"
EXTENSIONES = (".py", ".md", ".txt", ".rmd", ".toml", ".json")

APPS_STREAMLIT = {
    "PROYECTOS-2026": "https://proyectos-2026-ubfvxgpqmpp5z7dn6wlnn3.streamlit.app/",
    "FINANZAS-AVANZADAS-2026": "https://finanzas-avanzadas-2026-nxvqzsfrrtgu9e92javcli.streamlit.app/",
    "DESARROLLO-Y-GESTION-TERRITORIAL-2026": "https://desarrollo-y-gestion-territorial-2026-9yq3jazfc52x93tfumxwpz.streamlit.app/",
    "GESTION-TRIBUTARIA-2026": "https://gestion-tributaria-2026-avecwdhabftj7rjnx5knmb.streamlit.app/",
}


@st.cache_data(ttl=300)
def obtener_repositorios(usuario):
    url = f"https://api.github.com/users/{usuario}/repos?per_page=100&sort=updated"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def compilar_contexto_txt(usuario, repos_seleccionados, lista_repos):
    bloques = [
        "=" * 90,
        f"EXTRACCION DE PORTAFOLIO GITHUB: {usuario}",
        "=" * 90,
        "",
    ]
    for r in lista_repos:
        nombre = r["name"]
        if nombre not in repos_seleccionados:
            continue
        rama = r.get("default_branch", "main")
        bloques.append(f"### REPOSITORIO: {nombre}")
        bloques.append(f"Descripcion: {r.get('description') or 'Sin descripcion'}")
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
                if item["type"] == "blob" and ruta.lower().endswith(EXTENSIONES) and item.get("size", 0) <= 300_000:
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


st.markdown('<div class="sec-label">I. PLATAFORMAS INTERACTIVAS EN PRODUCCIÓN (STREAMLIT CLOUD)</div>', unsafe_allow_html=True)
cols = st.columns(4)
for idx, (nombre_app, link_app) in enumerate(APPS_STREAMLIT.items()):
    with cols[idx % 4]:
        st.link_button(f"Abrir {nombre_app}", link_app, use_container_width=True)

st.write("")
st.markdown('<div class="sec-label">II. COMPILADOR DE REPOSITORIOS EN ARCHIVO MAESTRO (.TXT) PARA IA</div>', unsafe_allow_html=True)

repos = obtener_repositorios(USUARIO)
nombres_todos = [r["name"] for r in repos]

seleccion = st.multiselect("Seleccione los repositorios a incluir en el archivo maestro:", nombres_todos, default=nombres_todos)

if st.button("Compilar Archivo Maestro de Contexto (.TXT)", type="primary"):
    with st.spinner("Consultando estructura de directorios y extrayendo código fuente desde GitHub..."):
        texto_final = compilar_contexto_txt(USUARIO, seleccion, repos)
    st.success(f"Extracción finalizada: {len(texto_final):,} caracteres compilados desde {len(seleccion)} repositorios.")
    st.download_button(
        label="Descargar SUPER_CONTEXTO_GITHUB_MAURICIO_2026.txt",
        data=texto_final,
        file_name="SUPER_CONTEXTO_GITHUB_MAURICIO_2026.txt",
        mime="text/plain",
    )
    with st.expander("Inspeccionar vista previa del archivo generado"):
        st.text(texto_final[:5000] + "\n\n... [Vista previa truncada] ...")
