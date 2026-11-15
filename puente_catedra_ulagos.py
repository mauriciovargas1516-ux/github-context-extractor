# -*- coding: utf-8 -*-
"""
puente_catedra_ulagos.py — PUENTE CENTRALIZADO DE LITERATURA, CUADRILLAS Y VISOR PDF/DRIVE
Alojado en: https://github.com/mauriciovargas1516-ux/github-context-extractor
- Sirve como fuente única de verdad (Single Source of Truth) para todas las aplicaciones
  Streamlit de Mauricio Vargas (PROYECTOS-2026, TERRITORIAL, FINANZAS, TRIBUTARIA).
- Permite vincular enlaces de Google Drive (2 TB) o archivos PDF del repositorio para
  visualizar el documento original incrustado en pantalla al pulsar una referencia.
- Incluye el Despachador Remoto (Push Bridge) para inyectar el conector en otros repositorios.
"""

import io
import os
import re
import json
import base64
import urllib.request
import streamlit as st


# ==============================================================================
# 1. DICCIONARIO CENTRALIZADO DE ENLACES GOOGLE DRIVE (2 TB) / PDF POR DOCUMENTO
# ==============================================================================
# Puedes pegar aquí el enlace de la carpeta general de tu Google Drive o el link/ID
# de cada PDF específico. Si un archivo tiene su link de Google Drive, el botón
# "Abrir Documento Original en Visor" lo renderiza directamente en la aplicación.

CARPETA_DRIVE_GENERAL_URL = "https://drive.google.com/drive/my-drive"

DOCUMENTOS_DRIVE_MAP = {
    # PROYECTOS 2026 (Dra. Luz María Ferrada B.)
    "Precios-Sociales-2026.pdf": {
        "ramo": "Evaluación Integrada de Proyectos (FDIC26)",
        "url_oficial": "https://sni.gob.cl/formulacion-de-iniciativas/precios-sociales/",
        "drive_url": "",  # Pega aquí el link de Google Drive si lo subes a tu nube
    },
    "Clase1 (18 ago).pdf": {
        "ramo": "Evaluación Integrada de Proyectos (FDIC26)",
        "url_oficial": "https://sni.gob.cl/wp-content/uploads/METODOLOGIA-GENERAL-2025.pdf#page=74",
        "drive_url": "",
    },
    "Clase2.pdf": {
        "ramo": "Evaluación Integrada de Proyectos (FDIC26)",
        "url_oficial": "https://economicas.unsa.edu.ar/iie/archivos/syc/Fontaine.pdf#page=207",
        "drive_url": "",
    },
    "Proceso2 RA1.pdf": {
        "ramo": "Evaluación Integrada de Proyectos (FDIC26)",
        "url_oficial": "https://sni.gob.cl/wp-content/uploads/METODOLOGIA-GENERAL-2025.pdf#page=55",
        "drive_url": "",
    },
    "MARCO LOGICO.pdf": {
        "ramo": "Evaluación Integrada de Proyectos (FDIC26)",
        "url_oficial": "https://www.cepal.org/fr/node/19467",
        "drive_url": "",
    },
    "GuiaVEdelosBSA.pdf": {
        "ramo": "Evaluación Integrada de Proyectos (FDIC26)",
        "url_oficial": "https://www.cepal.org/es/publicaciones/80999-estimacion-precio-social-carbono-la-evaluacion-la-inversion-publica-chile",
        "drive_url": "",
    },
    # FINANZAS AVANZADAS 2026 (Prof.ª Camila Bustos Rosas)
    "Consumo - Inversión.pdf": {
        "ramo": "Finanzas Avanzadas",
        "url_oficial": "https://finanzas-avanzadas-2026.streamlit.app/",
        "drive_url": "",
    },
    "Relación riesgo rentabilidad.pdf": {
        "ramo": "Finanzas Avanzadas",
        "url_oficial": "https://finanzas-avanzadas-2026.streamlit.app/",
        "drive_url": "",
    },
    "Teoría de mercado de capitales.pdf": {
        "ramo": "Finanzas Avanzadas",
        "url_oficial": "https://finanzas-avanzadas-2026.streamlit.app/",
        "drive_url": "",
    },
    "Instrucciones taller frontera eficiente.pdf": {
        "ramo": "Finanzas Avanzadas",
        "url_oficial": "https://si3.bcentral.cl/Siete/ES/Siete/Cuadro/CAP_TASA_INTERES/MN_TASA_INTERES_09/TMS_15",
        "drive_url": "",
    },
    # DESARROLLO Y GESTIÓN TERRITORIAL 2026 (Prof. Claudio Mancilla)
    "La_teoria_de_la_localizacion.pdf": {
        "ramo": "Desarrollo y Gestión Territorial",
        "url_oficial": "https://desarrollo-y-gestion-territorial-2026.streamlit.app/",
        "drive_url": "",
    },
    "06 OT 2024.pdf": {
        "ramo": "Desarrollo y Gestión Territorial",
        "url_oficial": "http://www.subdere.gov.cl/sites/default/noticiasold/articles-77172_recurso_1.pdf",
        "drive_url": "",
    },
    "Unidad 5. Redes y Cadena de Valor.dcx.pdf": {
        "ramo": "Desarrollo y Gestión Territorial",
        "url_oficial": "https://desarrollo-y-gestion-territorial-2026.streamlit.app/",
        "drive_url": "",
    },
    # GESTIÓN TRIBUTARIA 2026 (Prof. RVS)
    "Apunte IVA 2026.pdf": {
        "ramo": "Gestión Tributaria para la Toma de Decisiones",
        "url_oficial": "https://www.bcn.cl/leychile/navegar?idNorma=6369",
        "drive_url": "",
    },
    "Caso GTTD Emision Facturas Falsas (Datos).pdf": {
        "ramo": "Gestión Tributaria para la Toma de Decisiones",
        "url_oficial": "https://www.bcn.cl/leychile/navegar?idNorma=6374",
        "drive_url": "",
    },
}


# ==============================================================================
# 2. VISOR INTERACTIVO DE DOCUMENTOS (GOOGLE DRIVE EMBED + PDF EN PÁGINA EXACTA)
# ==============================================================================

def _extraer_id_google_drive(url_o_id):
    if not url_o_id:
        return None
    s = url_o_id.strip()
    m = re.search(r"/d/([a-zA-Z0-9_-]{15,})", s)
    if m:
        return m.group(1)
    m2 = re.search(r"id=([a-zA-Z0-9_-]{15,})", s)
    if m2:
        return m2.group(1)
    if re.match(r"^[a-zA-Z0-9_-]{20,}$", s):
        return s
    return None


def renderizar_visor_documento_en_vivo(clave_unica="visor_global"):
    """
    Componente universal que permite abrir cualquier PDF local, URL oficial (#page=N)
    o documento de tus 2 TB de Google Drive incrustado directamente dentro de Streamlit.
    """
    with st.expander("Visor Integrado de Literatura y Documentos de Cátedra (Google Drive / PDF en Página Exacta)", expanded=False):
        c1, c2, c3 = st.columns([1.8, 1.8, 0.8])
        with c1:
            doc_sel = st.selectbox(
                "Documento de Cátedra:",
                options=list(DOCUMENTOS_DRIVE_MAP.keys()),
                key=f"sel_doc_{clave_unica}",
            )
        meta_doc = DOCUMENTOS_DRIVE_MAP[doc_sel]
        with c2:
            url_custom = st.text_input(
                "Enlace Google Drive del archivo o PDF directo (opcional):",
                value=meta_doc.get("drive_url") or meta_doc.get("url_oficial", ""),
                key=f"url_doc_{clave_unica}",
            )
        with c3:
            pag_num = st.number_input(
                "Página / Lámina:",
                min_value=1,
                max_value=1200,
                value=1,
                step=1,
                key=f"pag_doc_{clave_unica}",
            )

        # Verificar si el archivo PDF existe localmente en una carpeta docs_catedra/
        carpeta_base = os.path.dirname(os.path.abspath(__file__))
        posibles_rutas = [
            os.path.join(carpeta_base, "docs_catedra", doc_sel),
            os.path.join(carpeta_base, doc_sel),
        ]
        ruta_local_pdf = next((r for r in posibles_rutas if os.path.exists(r)), None)

        if ruta_local_pdf and ruta_local_pdf.lower().endswith(".pdf"):
            with open(ruta_local_pdf, "rb") as f_pdf:
                b64_pdf = base64.b64encode(f_pdf.read()).decode("utf-8")
            st.markdown(
                f'<iframe src="data:application/pdf;base64,{b64_pdf}#page={int(pag_num)}" '
                f'width="100%" height="680" style="border:1px solid #94A3B8;border-radius:6px;"></iframe>',
                unsafe_allow_html=True,
            )
        else:
            drive_id = _extraer_id_google_drive(url_custom)
            if drive_id:
                preview_url = f"https://drive.google.com/file/d/{drive_id}/preview"
                st.caption(
                    f"Mostrando vista previa directa desde tu Google Drive (Archivo: {doc_sel} | Sugerencia: ir a página {int(pag_num)}):"
                )
                st.markdown(
                    f'<iframe src="{preview_url}" width="100%" height="650" '
                    f'style="border:1px solid #94A3B8;border-radius:6px;" allow="autoplay"></iframe>',
                    unsafe_allow_html=True,
                )
            elif url_custom.lower().split("#")[0].endswith(".pdf"):
                url_limpia = url_custom.split("#")[0] + f"#page={int(pag_num)}"
                st.caption(f"Abriendo PDF externo en página {int(pag_num)}: {url_limpia}")
                st.markdown(
                    f"<a href='{url_limpia}' target='_blank' "
                    f"style='background:#1D4ED8;color:white;padding:8px 14px;border-radius:5px;text-decoration:none;font-weight:700;'>"
                    f"Abrir {doc_sel} directamente en Página {int(pag_num)} &#8599;</a>",
                    unsafe_allow_html=True,
                )
            else:
                st.info(
                    "Pega arriba el enlace de compartir de tu Google Drive (de tus 2 TB) para ver el documento "
                    "incrustado aquí mismo, o usa el botón inferior para abrir la fuente oficial."
                )
                if url_custom:
                    st.markdown(f"[Abrir referencia externa de {doc_sel}]({url_custom})")


# ==============================================================================
# 3. CONECTOR REMOTO (CÓDIGO QUE SE INYECTA EN TUS OTROS REPOSITORIOS)
# ==============================================================================

CODIGO_CONECTOR_LIGERO = '''# ==============================================================================
# CONECTOR EN VIVO AL PUENTE DE LITERATURA Y CUADRILLAS ULAGOS 2026
# ==============================================================================
def cargar_puente_literatura_en_vivo(nombre_asignatura):
    import urllib.request
    import streamlit as st
    url_raw = "https://raw.githubusercontent.com/mauriciovargas1516-ux/github-context-extractor/main/puente_catedra_ulagos.py"
    try:
        req = urllib.request.Request(url_raw, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            codigo_remoto = resp.read().decode("utf-8")
        ns = {}
        exec(codigo_remoto, ns)
        if "renderizar_visor_documento_en_vivo" in ns:
            ns["renderizar_visor_documento_en_vivo"](clave_unica=nombre_asignatura)
    except Exception as exc:
        st.caption(f"Puente de literatura en modo local: {exc}")
'''


def enviar_archivo_a_repo_github(usuario, repo_destino, ruta_destino, contenido_texto, token_gh, mensaje_commit):
    """
    Envía o actualiza un archivo en cualquiera de tus otros repositorios usando la API REST de GitHub
    (igual que un webhook/trigger de Google Cloud).
    """
    url_api = f"https://api.github.com/repos/{usuario}/{repo_destino}/contents/{ruta_destino}"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "ULagos-Bridge-Dispatcher",
        "Authorization": f"token {token_gh.strip()}",
        "Content-Type": "application/json",
    }

    sha_actual = None
    try:
        req_get = urllib.request.Request(url_api, headers=headers)
        with urllib.request.urlopen(req_get, timeout=15) as r_get:
            datos_existentes = json.loads(r_get.read().decode("utf-8"))
            sha_actual = datos_existentes.get("sha")
    except Exception:
        sha_actual = None

    payload = {
        "message": mensaje_commit,
        "content": base64.b64encode(contenido_texto.encode("utf-8")).decode("utf-8"),
    }
    if sha_actual:
        payload["sha"] = sha_actual

    data_bytes = json.dumps(payload).encode("utf-8")
    req_put = urllib.request.Request(url_api, data=data_bytes, headers=headers, method="PUT")
    with urllib.request.urlopen(req_put, timeout=20) as r_put:
        return json.loads(r_put.read().decode("utf-8"))
