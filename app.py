import urllib.request
import urllib.parse
import json
import streamlit as st

st.set_page_config(
    page_title="Hub & Super Extractor GitHub - Mauricio Vargas",
    page_icon="🚀",
    layout="wide",
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


st.title("🚀 Hub de Aplicaciones y Super Extractor de Contexto GitHub")
st.caption(f"Conectado en tiempo real a la API pública de GitHub de **{USUARIO}**")

st.subheader("🌐 Mis Plataformas Interactivas Desplegadas en Streamlit Cloud")
cols = st.columns(4)
for idx, (nombre_app, link_app) in enumerate(APPS_STREAMLIT.items()):
    with cols[idx % 4]:
        st.link_button(f"🚀 {nombre_app}", link_app, use_container_width=True)

st.divider()

repos = obtener_repositorios(USUARIO)
nombres_todos = [r["name"] for r in repos]

st.subheader("📦 Selecciona los Repositorios a Empaquetar en un solo .TXT para IA")
seleccion = st.multiselect("Repositorios incluidos en el archivo de contexto:", nombres_todos, default=nombres_todos)

if st.button("⚡ Generar Super Archivo de Contexto (.TXT)", type="primary"):
    with st.spinner("Extrayendo árbol de archivos y código fuente desde GitHub..."):
        texto_final = compilar_contexto_txt(USUARIO, seleccion, repos)
    st.success(f"✅ Contexto compilado ({len(texto_final):,} caracteres de {len(seleccion)} repositorios).")
    st.download_button(
        label="📥 Descargar SUPER_CONTEXTO_GITHUB_MAURICIO_2026.txt",
        data=texto_final,
        file_name="SUPER_CONTEXTO_GITHUB_MAURICIO_2026.txt",
        mime="text/plain",
    )
    with st.expander("Vista previa del archivo generado"):
        st.text(texto_final[:5000] + "\n\n... [Vista previa truncada] ...")
