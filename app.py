# -*- coding: utf-8 -*-
"""
app.py — SUPER HUB ACADÉMICO Y CENTRAL DE MANDO MULTI-REPOSITORIO ULAGOS 2026
Repositorio Maestro: https://github.com/mauriciovargas1516-ux/github-context-extractor
- Pestaña 1 conectada modularmente a extractor_github_avanzado.py (Super Extractor Total,
  Código Limpio, Mapa AST, Auditoría CMS y descarga en 1 .TXT / .ZIP / Tomos).
- Pestañas 2 a 4: Cuadrillas Metodológicas, Visor PDF.js vía Google Drive API (HTTP Byte-Range)
  y Bóveda Moodle local.
- Pestaña 5 conectada modularmente a central_mando_github.py (CMS remoto de GitHub).
- Credenciales de Google Cloud (gcp_service_account_json) y GitHub (GITHUB_TOKEN +
  ADMIN_PASSWORD) gestionadas exclusivamente en Streamlit Secrets.
"""

import io
import os
import re
import hmac
import json
import zlib
import struct
import base64
import zipfile
import unicodedata
import urllib3

import requests
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ES_MODO_PUENTE_REMOTO = (__name__ == "puente_remoto_ulagos")


# ==============================================================================
# 1. CONFIGURACIÓN DE PÁGINA (SOLO SI NO ESTÁ EN MODO PUENTE REMOTO)
# ==============================================================================

if not ES_MODO_PUENTE_REMOTO:
    st.set_page_config(
        page_title="Super Hub Académico y Central de Mando ULagos 2026",
        layout="wide",
    )

    st.markdown(
        """
        <style>
        .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
            background-color: #F8FAFC !important;
            color: #0F172A !important;
        }
        .block-container {
            padding-top: 1.3rem !important;
            padding-bottom: 2.5rem !important;
            max-width: 1280px !important;
        }
        .top-banner {
            background-color: #0F172A;
            color: #FFFFFF;
            padding: 18px 24px;
            border-radius: 8px;
            border-left: 6px solid #2563EB;
            margin-bottom: 16px;
        }
        .top-banner h1 {
            color: #FFFFFF !important;
            font-size: 21px !important;
            font-weight: 700 !important;
            margin: 0 0 6px 0 !important;
        }
        .top-banner p {
            color: #CBD5E1 !important;
            font-size: 13.5px !important;
            margin: 0 !important;
        }
        .sec-header {
            background-color: #DBEAFE;
            color: #1E3A8A;
            padding: 9px 14px;
            font-weight: 700;
            font-size: 14px;
            border-radius: 5px;
            margin-top: 14px;
            margin-bottom: 10px;
            border-left: 4px solid #1D4ED8;
        }
        .tip-card {
            background-color: #FFFFFF;
            border: 1px solid #CBD5E1;
            border-top: 4px solid #1E3A8A;
            border-radius: 6px;
            padding: 14px;
            margin-bottom: 10px;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
        }
        .tip-title {
            font-weight: 700;
            color: #0F172A;
            font-size: 14px;
            margin-bottom: 6px;
        }
        .tip-body {
            color: #334155;
            font-size: 12.8px;
            line-height: 1.45;
            margin-bottom: 10px;
        }
        .tip-source {
            background-color: #F1F5F9;
            border-left: 3px solid #0284C7;
            padding: 7px 10px;
            font-size: 11.8px;
            color: #0F172A;
            font-weight: 600;
            margin-bottom: 8px;
        }
        .link-bar {
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-top: 6px;
        }
        .lit-link {
            display: inline-block;
            background-color: #EFF6FF;
            color: #1D4ED8 !important;
            border: 1px solid #BFDBFE;
            border-radius: 4px;
            padding: 4px 9px;
            font-size: 11.5px;
            font-weight: 700;
            text-decoration: none !important;
        }
        .lit-link:hover {
            background-color: #DBEAFE;
            border-color: #1D4ED8;
            color: #1E3A8A !important;
        }
        .lit-link-internal {
            display: inline-block;
            background-color: #F0FDF4;
            color: #15803D !important;
            border: 1px solid #BBF7D0;
            border-radius: 4px;
            padding: 4px 9px;
            font-size: 11.5px;
            font-weight: 700;
            text-decoration: none !important;
        }
        .lit-link-internal:hover {
            background-color: #DCFCE7;
            border-color: #15803D;
            color: #14532D !important;
        }
        .cita-box {
            background-color: #FEFCE8;
            border: 1px solid #FDE047;
            border-left: 5px solid #CA8A04;
            border-radius: 6px;
            padding: 14px 18px;
            margin-bottom: 16px;
        }
        div[data-baseweb="input"] > div,
        div[data-baseweb="select"] > div,
        div[data-baseweb="textarea"] > div {
            background-color: #FFFFFF !important;
            color: #0F172A !important;
            border: 1px solid #94A3B8 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ==============================================================================
# 2. CREDENCIALES GOOGLE CLOUD (SOLO SECRETS) Y MOTOR HTTP RANGE PARA .ZIP
# ==============================================================================

SERVICE_ACCOUNT_EMAIL = "drive-ulagos@motor-sii-python.iam.gserviceaccount.com"


def obtener_dict_credenciales_gcp():
    """Lee las credenciales de Google Cloud exclusivamente desde Streamlit Secrets."""
    try:
        if "gcp_service_account_json" in st.secrets:
            raw_sec = st.secrets["gcp_service_account_json"]
            if isinstance(raw_sec, str):
                return json.loads(raw_sec)
            return dict(raw_sec)
    except Exception as exc:
        raise RuntimeError(f"Error al leer 'gcp_service_account_json' en Secrets: {exc}") from exc

    raise RuntimeError(
        "Configura 'gcp_service_account_json' en Streamlit Cloud -> Manage app -> Settings -> Secrets "
        "para conectar con Google Drive API."
    )


def obtener_token_bearer_drive():
    from google.oauth2 import service_account
    from google.auth.transport.requests import Request

    info = obtener_dict_credenciales_gcp()
    creds = service_account.Credentials.from_service_account_info(
        info,
        scopes=["https://www.googleapis.com/auth/drive.readonly"],
    )
    creds.refresh(Request())
    return creds.token


def _normalizar_clave_nombre(nombre):
    s = unicodedata.normalize("NFKD", str(nombre)).encode("ascii", "ignore").decode("ascii").lower()
    s = re.sub(r"\.(pdf|xlsx|xls|docx|doc|pptx|ppt|zip|txt|mp4)$", "", s)
    s = s.replace("_copia", "").replace("copia de ", "").replace("copy of ", "")
    return re.sub(r"[^a-z0-9]+", "", s)


@st.cache_data(ttl=180, show_spinner=False)
def listar_archivos_google_drive_service_account():
    token = obtener_token_bearer_drive()
    headers = {"Authorization": f"Bearer {token}", "User-Agent": "ULagos-Academic-Hub"}
    url = (
        "https://www.googleapis.com/drive/v3/files"
        "?q=trashed=false&pageSize=1000"
        "&fields=files(id,name,mimeType,size,webViewLink)"
        "&supportsAllDrives=true&includeItemsFromAllDrives=true"
    )
    res = requests.get(url, headers=headers, timeout=20)
    res.raise_for_status()
    return res.json().get("files", [])


def _descargar_rango_bytes_drive(file_id, start_byte, end_byte):
    token = obtener_token_bearer_drive()
    headers = {
        "Authorization": f"Bearer {token}",
        "Range": f"bytes={int(start_byte)}-{int(end_byte)}",
        "User-Agent": "ULagos-Surgical-Zip-Reader",
    }
    url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media&supportsAllDrives=true"
    res = requests.get(url, headers=headers, timeout=30)
    res.raise_for_status()
    return res.content


@st.cache_data(ttl=600, show_spinner=False)
def listar_indice_interno_zip_en_drive(file_id, file_size):
    file_size = int(file_size)
    tail_len = min(file_size, 131072)
    tail_start = max(0, file_size - tail_len)
    tail_bytes = _descargar_rango_bytes_drive(file_id, tail_start, file_size - 1)

    eocd_pos = tail_bytes.rfind(b"PK\x05\x06")
    if eocd_pos == -1:
        return []

    eocd = tail_bytes[eocd_pos : eocd_pos + 22]
    _, _, _, _, total_entries, cd_size, cd_offset, _ = struct.unpack("<4sHHHHIIH", eocd)

    if cd_offset >= tail_start and (cd_offset + cd_size) <= file_size:
        rel_ini = cd_offset - tail_start
        cd_bytes = tail_bytes[rel_ini : rel_ini + cd_size]
    else:
        cd_bytes = _descargar_rango_bytes_drive(file_id, cd_offset, cd_offset + cd_size - 1)

    entradas = []
    pos = 0
    while pos + 46 <= len(cd_bytes):
        if cd_bytes[pos : pos + 4] != b"PK\x01\x02":
            break
        (
            sig, ver_made, ver_need, flags, comp_method, mod_time, mod_date,
            crc, comp_size, uncomp_size, fname_len, extra_len, comment_len,
            disk_start, int_attr, ext_attr, lfh_offset
        ) = struct.unpack("<4sHHHHHHIIIHHHHHII", cd_bytes[pos : pos + 46])

        fname_raw = cd_bytes[pos + 46 : pos + 46 + fname_len]
        encoding = "utf-8" if (flags & 0x800) else "cp437"
        fname = fname_raw.decode(encoding, errors="replace")

        if not fname.endswith("/"):
            partes = fname.split("/", 1)
            carpeta = partes[0] if len(partes) > 1 else "Raíz"
            archivo_base = partes[1] if len(partes) > 1 else fname
            ext = os.path.splitext(archivo_base)[1].lower()
            entradas.append({
                "ruta_completa": fname,
                "asignatura_carpeta": carpeta,
                "nombre_archivo": archivo_base,
                "extension": ext,
                "comp_method": comp_method,
                "comp_size": comp_size,
                "uncomp_size": uncomp_size,
                "kb_real": round(uncomp_size / 1024.0, 1),
                "lfh_offset": lfh_offset,
            })
        pos += 46 + fname_len + extra_len + comment_len

    return entradas


@st.cache_data(ttl=600, show_spinner=False)
def extraer_archivo_individual_de_zip_drive(file_id, lfh_offset, comp_size, comp_method):
    inicio = int(lfh_offset)
    fin = inicio + 30 + 1024 + int(comp_size)
    chunk = _descargar_rango_bytes_drive(file_id, inicio, fin)

    if chunk[:4] != b"PK\x03\x04":
        raise RuntimeError("Cabecera Local File Header (PK\\x03\\x04) no encontrada en el desplazamiento indicado.")

    _, _, _, _, _, _, _, _, _, lfh_fname_len, lfh_extra_len = struct.unpack("<4sHHHHHIIIHH", chunk[:30])
    data_start = 30 + lfh_fname_len + lfh_extra_len
    comp_data = chunk[data_start : data_start + int(comp_size)]

    if int(comp_method) == 0:
        return comp_data
    elif int(comp_method) == 8:
        return zlib.decompress(comp_data, -15)
    else:
        raise RuntimeError(f"Método de compresión ZIP no soportado directamente: {comp_method}")


@st.cache_data(ttl=600, show_spinner=False)
def descargar_bytes_archivo_drive_por_id(file_id):
    token = obtener_token_bearer_drive()
    headers = {"Authorization": f"Bearer {token}", "User-Agent": "ULagos-Academic-Hub"}
    url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media&supportsAllDrives=true"
    res = requests.get(url, headers=headers, timeout=45)
    res.raise_for_status()
    return res.content


# ==============================================================================
# 3. VISOR GRÁFICO HTML5 CANVAS (MOZILLA PDF.JS) ANTI-BLOQUEO DE CHROME
# ==============================================================================

def renderizar_visor_pdf_canvas_js(b64_pdf, nombre_doc, pag_ini, pag_fin):
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
      <style>
        body {{
          margin: 0;
          padding: 0;
          background-color: #0F172A;
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
          color: #F8FAFC;
        }}
        .toolbar {{
          position: sticky;
          top: 0;
          z-index: 100;
          background-color: #1E293B;
          border-bottom: 1px solid #334155;
          padding: 8px 14px;
          display: flex;
          justify-content: space-between;
          align-items: center;
          flex-wrap: wrap;
          gap: 8px;
        }}
        .toolbar-title {{
          font-size: 13px;
          font-weight: 700;
          color: #E2E8F0;
        }}
        .toolbar-btns {{
          display: flex;
          gap: 6px;
          align-items: center;
        }}
        button.btn-tool {{
          background-color: #2563EB;
          color: #FFFFFF;
          border: none;
          border-radius: 4px;
          padding: 5px 11px;
          font-size: 12px;
          font-weight: 700;
          cursor: pointer;
        }}
        button.btn-tool:hover {{
          background-color: #1D4ED8;
        }}
        button.btn-sec {{
          background-color: #334155;
          color: #F8FAFC;
          border: 1px solid #475569;
          border-radius: 4px;
          padding: 5px 10px;
          font-size: 12px;
          font-weight: 600;
          cursor: pointer;
        }}
        button.btn-sec:hover {{
          background-color: #475569;
        }}
        #canvas-container {{
          display: flex;
          flex-direction: column;
          align-items: center;
          padding: 16px;
          gap: 18px;
          height: 620px;
          overflow-y: auto;
        }}
        canvas {{
          background-color: #FFFFFF;
          box-shadow: 0 4px 16px rgba(0, 0, 0, 0.5);
          border-radius: 4px;
          max-width: 98%;
          height: auto;
        }}
      </style>
    </head>
    <body>
      <div class="toolbar">
        <div class="toolbar-title">{nombre_doc} — Lámina / Página {pag_ini} a {pag_fin}</div>
        <div class="toolbar-btns">
          <button class="btn-sec" onclick="cambiarZoom(-0.25)">Zoom -</button>
          <span id="zoom-label" style="font-size:12px;min-width:45px;text-align:center;">150%</span>
          <button class="btn-sec" onclick="cambiarZoom(0.25)">Zoom +</button>
          <button class="btn-tool" onclick="abrirEnPestanaNueva()">Abrir en Pestaña Nueva &#8599;</button>
        </div>
      </div>
      <div id="canvas-container"></div>

      <script>
        const b64Data = "{b64_pdf}";
        const rawBin = atob(b64Data);
        const uint8Array = new Uint8Array(rawBin.length);
        for (let i = 0; i < rawBin.length; i++) {{
          uint8Array[i] = rawBin.charCodeAt(i);
        }}

        const pdfjsLib = window['pdfjs-dist/build/pdf'];
        pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';

        let pdfDoc = null;
        let currentScale = 1.5;

        function renderAllPages() {{
          const container = document.getElementById('canvas-container');
          container.innerHTML = '';
          document.getElementById('zoom-label').innerText = Math.round(currentScale * 100) + '%';

          for (let num = 1; num <= pdfDoc.numPages; num++) {{
            const canvas = document.createElement('canvas');
            canvas.id = 'pdf-canvas-' + num;
            container.appendChild(canvas);

            pdfDoc.getPage(num).then(function(page) {{
              const viewport = page.getViewport({{ scale: currentScale }});
              const ctx = canvas.getContext('2d');
              canvas.height = viewport.height;
              canvas.width = viewport.width;
              page.render({{ canvasContext: ctx, viewport: viewport }});
            }});
          }}
        }}

        function cambiarZoom(delta) {{
          currentScale = Math.max(0.75, Math.min(3.0, currentScale + delta));
          if (pdfDoc) renderAllPages();
        }}

        function abrirEnPestanaNueva() {{
          const blob = new Blob([uint8Array], {{ type: 'application/pdf' }});
          const blobUrl = URL.createObjectURL(blob);
          window.open(blobUrl, '_blank');
        }}

        pdfjsLib.getDocument({{ data: uint8Array }}).promise.then(function(pdf) {{
          pdfDoc = pdf;
          renderAllPages();
        }});
      </script>
    </body>
    </html>
    """
    components.html(html_code, height=690, scrolling=False)


# ==============================================================================
# 4. CATÁLOGO DE REPOSITORIOS Y CUADRILLAS METODOLÓGICAS CON CITAS EXACTAS
# ==============================================================================

GITHUB_USER_DEFAULT = "mauriciovargas1516-ux"

MAPA_REPOS_A_RAMOS = {
    "PROYECTOS-2026": {
        "ramo": "Evaluación Integrada de Proyectos (FDIC26)",
        "sigla_archivo": "EVALUACION_INTEGRADA_PROYECTOS_FDIC26",
        "corto": "PROYECTOS",
        "docente": "Dra. Luz María Ferrada B.",
        "app_url": "https://proyectos-2026-ubfvxgpqmpp5z7dn6wlnn3.streamlit.app/",
        "repo_url": "https://github.com/mauriciovargas1516-ux/PROYECTOS-2026",
        "descripcion": "Formulación, evaluación financiera privada, evaluación social SNI/MIDESO 2026 y valoración ambiental RA1/RA2.",
        "topics": ["python", "streamlit", "evaluacion-de-proyectos", "sni-chile", "ulagos", "ingenieria-comercial"],
    },
    "DESARROLLO-Y-GESTION-TERRITORIAL-2026": {
        "ramo": "Desarrollo y Gestión Territorial",
        "sigla_archivo": "DESARROLLO_Y_GESTION_TERRITORIAL",
        "corto": "TERRITORIAL",
        "docente": "Prof. Claudio Mancilla",
        "app_url": "https://desarrollo-y-gestion-territorial-2026-ec6keylhsgra88s77bkl6f.streamlit.app/",
        "repo_url": "https://github.com/mauriciovargas1516-ux/DESARROLLO-Y-GESTION-TERRITORIAL-2026",
        "descripcion": "Indicadores de especialización regional (Qij, CE, Silva Lira), Gini/Theil, Ordenamiento Territorial (Guttman/Rondinelli) y Redes UCINET/Dini.",
        "topics": ["python", "streamlit", "desarrollo-territorial", "sii-chile", "ucinet", "ulagos"],
    },
    "FINANZAS-AVANZADAS-2026": {
        "ramo": "Finanzas Avanzadas",
        "sigla_archivo": "FINANZAS_AVANZADAS",
        "corto": "FINANZAS",
        "docente": "Prof.ª Camila Bustos Rosas",
        "app_url": "https://finanzas-avanzadas-2026-nxvqzsfrrtgu9e92javcli.streamlit.app/",
        "repo_url": "https://github.com/mauriciovargas1516-ux/FINANZAS-AVANZADAS-2026",
        "descripcion": "Modelo Consumo-Inversión de Fisher, DuPont/PGU, Frontera Eficiente de Markowitz (5 vs. 30 títulos IPSA), CAPM y Beta de Hamada.",
        "topics": ["python", "streamlit", "finanzas-corporativas", "markowitz", "capm", "ulagos"],
    },
    "FINANZAS-AVANZADAS": {
        "ramo": "Finanzas Avanzadas",
        "sigla_archivo": "FINANZAS_AVANZADAS",
        "corto": "FINANZAS",
        "docente": "Prof.ª Camila Bustos Rosas",
        "app_url": "https://finanzas-avanzadas-2026-nxvqzsfrrtgu9e92javcli.streamlit.app/",
        "repo_url": "https://github.com/mauriciovargas1516-ux/FINANZAS-AVANZADAS",
        "descripcion": "Simulación financiera, teoría de carteras de Markowitz, CAPM, WACC y valoración bajo incertidumbre.",
        "topics": ["python", "streamlit", "finanzas", "montecarlo", "markowitz", "ulagos"],
    },
    "GESTION-TRIBUTARIA-2026": {
        "ramo": "Gestión Tributaria para la Toma de Decisiones",
        "sigla_archivo": "GESTION_TRIBUTARIA_TOMA_DECISIONES",
        "corto": "TRIBUTARIA",
        "docente": "Prof. Richard Villanueva Soto",
        "app_url": "https://gestion-tributaria-2026-avecwdhabftj7rjnx5knmb.streamlit.app/",
        "repo_url": "https://github.com/mauriciovargas1516-ux/GESTION-TRIBUTARIA-2026",
        "descripcion": "Determinación de IVA (D.L. 825), Libros de Compras/Ventas/Honorarios/Remuneraciones, F29 e Infracciones Art. 97 Código Tributario.",
        "topics": ["python", "streamlit", "tributaria-chile", "iva-f29", "sii", "ulagos"],
    },
    "moodle-hybrid-scraper": {
        "ramo": "Sincronizador Automatizado ULagos Virtual (Moodle Scraper)",
        "sigla_archivo": "SINCRONIZADOR_MOODLE_ULAGOS",
        "corto": "MOODLE",
        "docente": "Automatización Web Híbrida (Selenium + Requests)",
        "app_url": "https://app-context-extractor-cl8x5kwfdodzvmx7m3vean.streamlit.app/",
        "repo_url": "https://github.com/mauriciovargas1516-ux/moodle-hybrid-scraper",
        "descripcion": "Rastreador web híbrido integrado para extraer y empaquetar todos los PDFs, Excels y apuntes de ULagos Virtual.",
        "topics": ["python", "selenium", "moodle-scraper", "streamlit", "ulagos"],
    },
    "github-context-extractor": {
        "ramo": "Hub Central & Extractor de Contexto Académico",
        "sigla_archivo": "HUB_EXTRACTOR_CONTEXTO_ULAGOS",
        "corto": "HUB",
        "docente": "Portafolio Ingeniería Comercial ULagos",
        "app_url": "https://app-context-extractor-cl8x5kwfdodzvmx7m3vean.streamlit.app/",
        "repo_url": "https://github.com/mauriciovargas1516-ux/github-context-extractor",
        "descripcion": "Super Hub centralizado de compilación vía GitHub API, conexión Google Drive API (5 TB) y gestión remota multi-repositorio.",
        "topics": ["python", "streamlit", "google-drive-api", "github-api", "context-engineering", "ulagos"],
    },
}

CUADRILLAS_LITERATURA_POR_RAMO = {
    "Evaluación Integrada de Proyectos (FDIC26)": {
        "docente": "Dra. Luz María Ferrada B.",
        "app_url": "https://proyectos-2026-ubfvxgpqmpp5z7dn6wlnn3.streamlit.app/",
        "tarjetas": [
            {
                "id": "proy_sni_2026",
                "doc_pdf": "Precios-Sociales-2026.pdf",
                "pag_pdf": 5,
                "titulo": "1. Precios Sociales Vigentes SNI 2026 (Mano de Obra, Divisa y TSD)",
                "formula": r"TSD = 5,5\% \quad | \quad PSMO = Salario_{Bruto} \times FCSMO \quad (MOC=0,97;\; MOSC=0,95;\; MONC=0,91;\; Divisa=1,00)",
                "tip": (
                    "El Precio Social de la Mano de Obra (PSMO) es siempre menor o igual al salario privado. "
                    "Según la tabla CIUO-08 del SNI, los choferes de buses interregionales u operadores de máquinas "
                    "corresponden a Mano de Obra Semicalificada (MOSC = 0,95), no a MONC. Además, aunque un terreno sea "
                    "municipal, siempre debe valorizarse a su costo de oportunidad social."
                ),
                "fuente": (
                    "MDSF (2026), 'Precios-Sociales-2026.pdf', Cap. 1, Tablas 1.1 a 1.4, págs. 4-6; y "
                    "Dra. Luz María Ferrada (2026), 'Proceso2 RA1.pdf', Preguntas I.11, I.15 y II.3, págs. 1-2."
                ),
                "marcador_moodle": "PROYECTOS 2026/Precios-Sociales-2026.pdf | Página 5",
                "extracto_literal": (
                    "--- [PROYECTOS 2026/Precios-Sociales-2026.pdf | Página 5] ---\n"
                    "Tabla 1.2 Clasificación de la Mano de Obra de acuerdo con CIUO-08:\n"
                    "1-3 Directores, Profesionales y Técnicos nivel medio -> MOC (0,97)\n"
                    "4-8 Administrativos, Servicios, Agropecuarios, Oficiales y Operadores de máquinas -> MOSC (0,95)\n"
                    "9 Ocupaciones elementales -> MONC (0,91)\n"
                    "PSMO = Salario bruto * FCSMO | Tasa Social de Descuento (TSD) 2026 = 5,5% | Divisa (FCSD) = 1,00."
                ),
                "links": [
                    ("Portal Precios Sociales SNI 2026", "https://sni.gob.cl/formulacion-de-iniciativas/precios-sociales/"),
                    ("Estudio Oficial PSMO (CIUO-08 PDF)", "https://sni.gob.cl/storage/docs/Informe_Final_PSMO.pdf"),
                    ("Abrir Simulador Proyectos 2026", "https://proyectos-2026-ubfvxgpqmpp5z7dn6wlnn3.streamlit.app/"),
                ],
            },
            {
                "id": "proy_fontaine_leche",
                "doc_pdf": "Clase2.pdf",
                "pag_pdf": 20,
                "titulo": "2. Valor Social de la Producción (Fontaine): Eficiencia vs. Agencia",
                "formula": r"VSP = AD + LR = VPP + \Delta EC + \Delta EP \quad | \quad P_{social} = \frac{P_0 + P_1}{2}",
                "tip": (
                    "En un mercado sin distorsiones ni comercio exterior, al entrar el proyecto la oferta se desplaza "
                    "(Q' = Q + 1.470) y el precio baja de P0 ($187,36) a P1 ($170,80). El Aumento en Disponibilidad (AD = $144.645) "
                    "se mide bajo la curva de demanda entre Q0 y Qd1; la Liberación de Recursos (LR = $118.609) se mide bajo la "
                    "curva de oferta antigua entre Qo1 y Q0, sumando VSP = $263.253."
                ),
                "fuente": (
                    "Ernesto R. Fontaine (2008), 'Evaluación Social de Proyectos' (13.ª ed.), Cap. V (págs. 199-255) y "
                    "Cap. VII (págs. 373-385); y Dra. Luz María Ferrada (2026), 'Clase2.pdf', Ejercicio Mercado de la Leche, láminas 15-25."
                ),
                "marcador_moodle": "PROYECTOS 2026/Clase2.pdf | Página 20",
                "extracto_literal": (
                    "--- [PROYECTOS 2026/Clase2.pdf | Páginas 15, 20-25] ---\n"
                    "ENFOQUE EFICIENCIA: VSP = Liberación de recursos (LR) + Aumento en disponibilidad (AD)\n"
                    "ENFOQUE DE AGENCIA: VSP = VPP (Inversionista) + Delta Excedente del Consumidor + Delta Excedente del Productor\n"
                    "EJERCICIO MERCADO DE LA LECHE (Lámina 20):\n"
                    "Po = 50 + 0,025*Qo  |  Pd = 300 - 0,0205*Qd  |  Q' = Q + 1.470."
                ),
                "links": [
                    ("Libro Fontaine (2008) PDF — Cap. V (Pág. 207)", "https://economicas.unsa.edu.ar/iie/archivos/syc/Fontaine.pdf#page=207"),
                    ("Libro Fontaine (2008) PDF — Cap. VII (Pág. 381)", "https://economicas.unsa.edu.ar/iie/archivos/syc/Fontaine.pdf#page=381"),
                    ("Ver Gráfico Interactivo en App Proyectos", "https://proyectos-2026-ubfvxgpqmpp5z7dn6wlnn3.streamlit.app/"),
                ],
            },
            {
                "id": "proy_van_vac_cae",
                "doc_pdf": "Proceso2 RA1.pdf",
                "pag_pdf": 2,
                "titulo": "3. Cuándo elegir entre VAN, VAC y CAE en el SNI",
                "formula": r"VAC = \sum_{t=0}^{n} \frac{C_t}{(1 + r)^t} \quad | \quad CAE = VAC \cdot \frac{r(1 + r)^n}{(1 + r)^n - 1}",
                "tip": (
                    "Usa VAN cuando las alternativas tienen igual vida útil y los beneficios son medibles. "
                    "Usa VAC cuando los beneficios son iguales o difíciles de medir y las alternativas tienen igual horizonte. "
                    "Usa CAE (o CAE por tonelada/producto) cuando las alternativas tienen distinta vida útil o distinto volumen de producción."
                ),
                "fuente": (
                    "Dra. Luz María Ferrada (2026), 'Clase2.pdf' (lámina 12) y 'Proceso2 RA1.pdf' (Sección II.1, pág. 2); "
                    "MDSF (2025), 'METODOLOGIA-GENERAL-2025.pdf', Sección III.4, págs. 55-58; y 'Metodologia_GIRS_vf.pdf', pág. 10."
                ),
                "marcador_moodle": "PROYECTOS 2026/Proceso2 RA1.pdf | Página 2",
                "extracto_literal": (
                    "--- [PROYECTOS 2026/Proceso2 RA1.pdf | Página 2] ---\n"
                    "• VAC se usa cuando las alternativas tienen igual años de evaluación y los beneficios son muy difíciles de medir o son idénticos.\n"
                    "• CAE se usa cuando las alternativas tienen distintos años de evaluación."
                ),
                "links": [
                    ("Metodología General SNI 2025 (Pág. 55: VAN/VAC/CAE)", "https://sni.gob.cl/wp-content/uploads/METODOLOGIA-GENERAL-2025.pdf#page=55"),
                    ("Metodología GIRS Residuos (Pág. 10: CAE/ton)", "https://sni.gob.cl/wp-content/uploads/220818_Metodologia_GIRS_vf.pdf#page=10"),
                ],
            },
            {
                "id": "proy_arboles_mml",
                "doc_pdf": "MARCO LOGICO.pdf",
                "pag_pdf": 8,
                "titulo": "4. Árboles Causales, Población SNI y Matriz de Marco Lógico (MML)",
                "formula": r"\text{Población Referencia} \supset \text{Población Afectada (Con Problema)} \supset \text{Población Objetivo}",
                "tip": (
                    "Nunca redactes el problema como 'falta de una solución' (ej. 'falta un camión recolector' o 'no hay consultorio'). "
                    "En el Marco Lógico: (1) cada programa tiene un único Propósito (que nace del Objetivo Central del árbol), "
                    "(2) los indicadores se dividen en Eficacia, Eficiencia, Calidad y Economía, y (3) a nivel de Actividades no se definen supuestos."
                ),
                "fuente": (
                    "Ortegón, Pacheco y Roura (2005), 'Serie Manuales CEPAL N° 39', Cap. I, págs. 10-21; "
                    "Dra. Luz María Ferrada (2026), 'Presentación_2.pdf' (láminas 5-21), 'Clase3.pdf' (láminas 7-8) y 'MARCO LOGICO.pdf' (láminas 6-21)."
                ),
                "marcador_moodle": "PROYECTOS 2026/MARCO LOGICO.pdf | Página 8",
                "extracto_literal": (
                    "--- [PROYECTOS 2026/MARCO LOGICO.pdf | Páginas 8 y 14] ---\n"
                    "Cada programa tiene un solo propósito.\n"
                    "CATEGORÍAS DE INDICADORES: EFICACIA, CALIDAD, EFICIENCIA y ECONOMÍA."
                ),
                "links": [
                    ("Manual CEPAL N° 39 — Ortegón, Pacheco y Roura (2005)", "https://www.cepal.org/fr/node/19467"),
                    ("Metodología General SNI 2025 (Pág. 18: El Problema)", "https://sni.gob.cl/wp-content/uploads/METODOLOGIA-GENERAL-2025.pdf#page=18"),
                    ("Ley REP N° 20.920 en Biblioteca del Congreso Nacional", "https://www.bcn.cl/leychile/navegar?idNorma=1090894"),
                ],
            },
            {
                "id": "proy_ambiental_barzev",
                "doc_pdf": "GuiaVEdelosBSA.pdf",
                "pag_pdf": 15,
                "titulo": "5. Valoración Económica Ambiental (RA2) y Gases de Efecto Invernadero",
                "formula": r"CO_2eq = t_{CO_2} + 28 \cdot t_{CH_4} + 265 \cdot t_{N_2O} \quad | \quad P_{Social\,CO_2} = \$71.801\text{ CLP/t}",
                "tip": (
                    "Bienes ambientales son tangibles y se gastan o transforman al usarse (agua, madera); servicios ambientales "
                    "son funciones ecosistémicas intangibles que no se gastan (belleza escénica, captura de carbono). "
                    "Para valorar recreación con Costo de Viaje en Chile, el VST Deportivo/Recreativo 2026 es de $2.792 CLP/h-pax."
                ),
                "fuente": (
                    "Radoslav Barzev (2002), 'GuiaVEdelosBSA.pdf', Cap. I (Tablas 1-2, págs. 12-17) y Cap. IV (págs. 59-78); "
                    "y MDSF (2026), 'Precios-Sociales-2026.pdf', Cap. 2.4 (pág. 11) y Cap. 5 (págs. 17-19)."
                ),
                "marcador_moodle": "PROYECTOS 2026/Precios-Sociales-2026.pdf | Página 18",
                "extracto_literal": (
                    "--- [PROYECTOS 2026/GuiaVEdelosBSA.pdf | Página 15] ---\n"
                    "Bienes Ambientales vs. Servicios Ambientales.\n"
                    "--- [PROYECTOS 2026/Precios-Sociales-2026.pdf | Páginas 17-18] ---\n"
                    "Tabla 5.1 Precio Social del Carbono 2026: 71.801 CLP / t CO2 eq."
                ),
                "links": [
                    ("Estudio CEPAL Precio Social del Carbono en Chile (Pica et al., 2024)", "https://www.cepal.org/es/publicaciones/80999-estimacion-precio-social-carbono-la-evaluacion-la-inversion-publica-chile"),
                    ("Decreto N° 189 Condiciones Sanitarias Rellenos Sanitarios (BCN)", "https://www.bcn.cl/leychile/navegar?idNorma=268137"),
                ],
            },
            {
                "id": "proy_flujo_financiado",
                "doc_pdf": "Clase1 (18 ago).pdf",
                "pag_pdf": 29,
                "titulo": "6. Flujo Privado Puro vs. Flujo Financiado y Capital de Trabajo",
                "formula": r"Cuota = P \cdot \frac{r(1+r)^n}{(1+r)^n - 1} \quad | \quad CT_{desfase} = \frac{\text{Costos Anuales} \times \text{Días Desfase}}{365}",
                "tip": (
                    "En el flujo con deuda, solo los intereses bancarios se restan antes de impuestos (creando escudo fiscal), "
                    "mientras que la amortización del principal se resta después de impuestos en el Flujo de Capitales. "
                    "Los costos hundidos son obligaciones contraídas en el pasado e inevitables, por lo que no entran al flujo incremental."
                ),
                "fuente": (
                    "Dra. Luz María Ferrada (2026), 'Clase1 (18 ago).pdf', láminas 17-18 (Capital de Trabajo), "
                    "láminas 23-32 (Flujo Puro vs. Financiado y Tabla de Crédito) y láminas 33-36 (Flujos Incrementales y Costos Hundidos)."
                ),
                "marcador_moodle": "PROYECTOS 2026/Clase1 (18 ago).pdf | Página 29",
                "extracto_literal": (
                    "--- [PROYECTOS 2026/Clase1 (18 ago).pdf | Páginas 25, 29-30 y 34] ---\n"
                    "• Flujo de caja del proyecto puro vs. con deuda (escudo tributario de intereses y amortización).\n"
                    "• Costos Hundidos (Lámina 34): inevitables e irrelevantes para la evaluación."
                ),
                "links": [
                    ("Metodología General SNI 2025 (Pág. 74: Anexo 4 Flujos Privados)", "https://sni.gob.cl/wp-content/uploads/METODOLOGIA-GENERAL-2025.pdf#page=74"),
                    ("Información SII Impuestos Directos e Indirectos", "https://www.sii.cl/ayudas/aprenda_sobre/3072-.html"),
                ],
            },
        ],
    },
    "Finanzas Avanzadas": {
        "docente": "Prof.ª Camila Bustos Rosas",
        "app_url": "https://finanzas-avanzadas-2026-nxvqzsfrrtgu9e92javcli.streamlit.app/",
        "tarjetas": [
            {
                "id": "fin_fisher",
                "doc_pdf": "Consumo - Inversión.pdf",
                "pag_pdf": 9,
                "titulo": "1. Modelo Consumo-Inversión y Principio de Separación de Fisher",
                "formula": r"U = f(C_0, C_1) \quad | \quad \text{Óptimo Productivo: } RMgI = r_f \quad | \quad \text{Óptimo Consumo: } TMS(C_0, C_1) = -(1 + r_f)",
                "tip": (
                    "En un mercado de capitales perfecto (sin fricciones, costos de transacción ni impuestos), la decisión de inversión "
                    "de la empresa es objetiva y delegable a los administradores (ejecutar proyectos hasta que la rentabilidad marginal "
                    "iguale la tasa de interés de mercado rf), independientemente de las preferencias subjetivas de consumo de los dueños."
                ),
                "fuente": (
                    "Camila Bustos Rosas (2026), 'Consumo - Inversión.pdf', láminas 2-10; y "
                    "Brealey, Myers y Allen (2010), 'Principios de Finanzas Corporativas' (9.ª ed.), Cap. 2, Sección 2.2, págs. 19-22."
                ),
                "marcador_moodle": "FINANZAS AVANZADAS 2026/Consumo - Inversi",
                "extracto_literal": (
                    "--- [FINANZAS AVANZADAS 2026/Consumo - Inversión.pdf | Páginas 9 y 10] ---\n"
                    "Principio de separación de Fisher: la decisión de inversión está representada solamente por el criterio objetivo de mercado."
                ),
                "links": [
                    ("Abrir Simulador Finanzas Avanzadas en Streamlit", "https://finanzas-avanzadas-2026-nxvqzsfrrtgu9e92javcli.streamlit.app/"),
                    ("Repositorio GitHub Finanzas Avanzadas", "https://github.com/mauriciovargas1516-ux/FINANZAS-AVANZADAS-2026"),
                ],
            },
            {
                "id": "fin_riesgo_dupont",
                "doc_pdf": "Relación riesgo rentabilidad.pdf",
                "pag_pdf": 28,
                "titulo": "2. Actitudes frente al Riesgo, Juego Justo y Poder Generador de Utilidades (PGU / DuPont)",
                "formula": r"PGU = \underbrace{\left(\frac{\text{Resultado Operacional}}{\text{Ventas}}\right)}_{\text{Margen Operacional}} \times \underbrace{\left(\frac{\text{Ventas}}{\text{Activos Operacionales}}\right)}_{\text{Rotación de Activos}}",
                "tip": (
                    "Un juego es 'justo' cuando el valor esperado de la riqueza si aceptas es igual al valor seguro si rechazas. "
                    "El individuo averso al riesgo tiene utilidad marginal decreciente y prefiere renta segura antes que incierta de igual valor esperado. "
                    "En la empresa, el PGU mide la rentabilidad contable de los activos operacionales combinando margen y rotación."
                ),
                "fuente": (
                    "Camila Bustos Rosas (2026), 'Relación riesgo rentabilidad.pdf', láminas 7-21 y 26-35; y "
                    "Ross, Westerfield y Jordan (2010), Cap. 3, pág. 64."
                ),
                "marcador_moodle": "FINANZAS AVANZADAS 2026/Relaci",
                "extracto_literal": (
                    "--- [FINANZAS AVANZADAS 2026/Relación riesgo rentabilidad.pdf | Páginas 8, 14, 21 y 28] ---\n"
                    "• Juego justo (Lámina 8) | PGU (Lámina 28): Margen de Utilidad Operacional x Rotación de Activos Operacionales."
                ),
                "links": [
                    ("Abrir Calculadora DuPont y Utilidad en Finanzas App", "https://finanzas-avanzadas-2026-nxvqzsfrrtgu9e92javcli.streamlit.app/"),
                ],
            },
            {
                "id": "fin_markowitz_capm",
                "doc_pdf": "Teoría de mercado de capitales.pdf",
                "pag_pdf": 40,
                "titulo": "3. Frontera Eficiente de Markowitz (252 días), CAPM y Ecuación de Hamada",
                "formula": r"\sigma_{anual} = \sigma_{diaria}\sqrt{252} \quad | \quad R_e = R_f + \beta_L(R_m - R_f) \quad | \quad \beta_L = \beta_U\left[1 + (1 - t)\frac{B}{S}\right]",
                "tip": (
                    "El efecto diversificación opera siempre que la correlación sea menor a +1 (rho < 1). "
                    "En el Taller de Frontera Eficiente ($65.000.000; 5 vs. 30 acciones del IPSA; Dupla 13: Parque Arauco, Andina-B, "
                    "Cenco Malls, Banco de Chile y Vapores), la tasa libre de riesgo es el promedio de los bonos BCP/BTP a 5 años del Banco Central."
                ),
                "fuente": (
                    "Camila Bustos Rosas (2026), 'Teoría de mercado de capitales.pdf' (láminas 11-50), "
                    "'Instrucciones taller frontera eficiente.pdf' (págs. 1-2) y 'Taller Frontera Eficiente Ing Comercial.xlsx'."
                ),
                "marcador_moodle": "FINANZAS AVANZADAS 2026/Instrucciones taller frontera eficiente.pdf | Página 1",
                "extracto_literal": (
                    "--- [FINANZAS AVANZADAS 2026/Teoría de mercado de capitales.pdf | Páginas 31, 40 y 49] ---\n"
                    "• CAPM (Lámina 40): Re = Rf + Beta * (Rm - Rf).\n"
                    "• Ecuación de Hamada (Lámina 49): Beta_L = Beta_U * [1 + (1 - t)*(B / S)]."
                ),
                "links": [
                    ("Base de Datos Estadísticos Banco Central de Chile (BCP/BTP 5 años)", "https://si3.bcentral.cl/Siete/ES/Siete/Cuadro/CAP_TASA_INTERES/MN_TASA_INTERES_09/TMS_15"),
                    ("Abrir Optimizador Markowitz / CAPM en Vivo", "https://finanzas-avanzadas-2026-nxvqzsfrrtgu9e92javcli.streamlit.app/"),
                ],
            },
        ],
    },
    "Desarrollo y Gestión Territorial": {
        "docente": "Prof. Claudio Mancilla",
        "app_url": "https://desarrollo-y-gestion-territorial-2026-ec6keylhsgra88s77bkl6f.streamlit.app/",
        "tarjetas": [
            {
                "id": "terr_localizacion",
                "doc_pdf": "La_teoria_de_la_localizacion.pdf",
                "pag_pdf": 7,
                "titulo": "1. Teoría de la Localización: Von Thünen, Weber, Hotelling, Christaller-Lösch y Krugman",
                "formula": r"LR = Y(m - c) - Ytd \quad | \quad IM = \frac{\text{Peso MP Localizadas}}{\text{Peso Producto Final}} \quad | \quad p^*(x) = \frac{aW(x)}{\rho}",
                "tip": (
                    "En Von Thünen la renta agrícola decrece con la distancia formando anillos concéntricos. "
                    "En Weber, si IM > 1 la fábrica se ubica cerca de los insumos; si IM < 1 se ubica cerca del mercado, "
                    "desviándose hacia un enclave laboral barato solo si éste cae dentro de la isodápana crítica."
                ),
                "fuente": (
                    "Néstor Duch Brown (Universitat de Barcelona), 'La_teoria_de_la_localizacion.pdf', "
                    "Secciones 1.1 a 1.4 (págs. 6-23) y Secciones 2.1 a 3 (págs. 34-66)."
                ),
                "marcador_moodle": "TERRITORIAL 2026/La_teoria_de_la_localizacion.pdf | Página 7",
                "extracto_literal": (
                    "--- [TERRITORIAL 2026/La_teoria_de_la_localizacion.pdf | Páginas 7, 12, 13 y 43] ---\n"
                    "• Von Thünen (Pág. 7): LR = Y(m - c) - Y*t*d.\n"
                    "• Weber (Pág. 12-13): IM = peso de las materias primas localizadas / peso del producto final."
                ),
                "links": [
                    ("Abrir Plataforma Desarrollo y Gestión Territorial", "https://desarrollo-y-gestion-territorial-2026-ec6keylhsgra88s77bkl6f.streamlit.app/"),
                    ("Repositorio GitHub Territorial 2026", "https://github.com/mauriciovargas1516-ux/DESARROLLO-Y-GESTION-TERRITORIAL-2026"),
                ],
            },
            {
                "id": "terr_ot_guttman",
                "doc_pdf": "06 OT 2024.pdf",
                "pag_pdf": 11,
                "titulo": "2. Indicadores de Ordenamiento Territorial: Primacía, Guttman/Rondinelli y Aislamiento",
                "formula": r"IP = \frac{P_1}{P_2 + P_3 + P_4} \quad | \quad \text{Matriz de Rondinelli: } 1 = \text{Presente},\; 0 = \text{Ausente}",
                "tip": (
                    "El Índice de Primacía relaciona la comuna más poblada con la suma de las tres siguientes (alto valor = macrocefalia). "
                    "En la Escala de Guttman / Matriz de Rondinelli (para las 10 comunas más pobladas y mínimo 7 variables), "
                    "las variables elegidas deben discriminar entre comunas: si todas tienen valor 1, debes reemplazar la variable."
                ),
                "fuente": (
                    "Prof. Claudio Mancilla (2024/2026), '06 OT 2024.pdf' (láminas 10-16), 'Unidad 5. Ordenamiento Territorial.pdf' (pág. 1) "
                    "y 'SUBDERE articles-83896_recurso_1_1.pdf' (PROT, págs. 11-22)."
                ),
                "marcador_moodle": "TERRITORIAL 2026/06 OT 2024.pdf | Página 11",
                "extracto_literal": (
                    "--- [TERRITORIAL 2026/06 OT 2024.pdf | Páginas 11, 12 y 15] ---\n"
                    "• Índice de Primacía y Escala de Gutmann / Matriz de Rondinelli."
                ),
                "links": [
                    ("Manual Elaboración PLADECO (SUBDERE PDF)", "http://www.subdere.gov.cl/sites/default/noticiasold/articles-77172_recurso_1.pdf"),
                    ("Abrir Módulo Guttman / Rondinelli en App Territorial", "https://desarrollo-y-gestion-territorial-2026-ec6keylhsgra88s77bkl6f.streamlit.app/"),
                ],
            },
            {
                "id": "terr_dini_ucinet",
                "doc_pdf": "Unidad 5. Redes y Cadena de Valor.dcx.pdf",
                "pag_pdf": 2,
                "titulo": "3. Redes Empresariales (Dini 2010), UCINET y Cadenas de Valor (Control 4)",
                "formula": r"\text{Densidad Dirigida} = \frac{L}{N(N - 1)} \quad | \quad \text{Diagonal Principal } A_{ii} = 0",
                "tip": (
                    "En el Taller de Sistemas Productivos Locales y Cadenas de Valor (Control 4), se entrevista a 3 personas de "
                    "organizaciones distintas cubriendo al menos 2 eslabones (1 gremio + 2 empresas). Regla de entrevista del profesor: "
                    "no sugieras que debe existir un clúster ni uses la palabra 'debilidades' (pregunta por desafíos o aspectos por fortalecer)."
                ),
                "fuente": (
                    "Marco Dini (2010), 'Competitividad, redes de empresas y cooperación empresarial' (CEPAL); y "
                    "Prof. Claudio Mancilla (2026), 'Unidad 5. Redes y Cadena de Valor.dcx.pdf', págs. 1-4."
                ),
                "marcador_moodle": "TERRITORIAL 2026/Unidad 5. Redes y Cadena de Valor.dcx.pdf | Página 2",
                "extracto_literal": (
                    "--- [TERRITORIAL 2026/Unidad 5. Redes y Cadena de Valor.dcx.pdf | Páginas 1 y 2] ---\n"
                    "No sugieran que necesariamente debe existir un clúster. No hablen de DEBILIDADES; indiquen desafíos, mejoras o aspectos para fortalecer."
                ),
                "links": [
                    ("Abrir Simulador Redes de Dini y UCINET en Vivo", "https://desarrollo-y-gestion-territorial-2026-ec6keylhsgra88s77bkl6f.streamlit.app/"),
                ],
            },
        ],
    },
    "Gestión Tributaria para la Toma de Decisiones": {
        "docente": "Prof. Richard Villanueva Soto",
        "app_url": "https://gestion-tributaria-2026-avecwdhabftj7rjnx5knmb.streamlit.app/",
        "tarjetas": [
            {
                "id": "trib_iva_dl825",
                "doc_pdf": "IVA y Toma de Decisiones.pdf",
                "pag_pdf": 3,
                "titulo": "1. Determinación Mensual del IVA, Crédito Fiscal y Exclusión de Automóviles (D.L. N° 825)",
                "formula": r"\text{Neto Boleta} = \frac{\text{Total Bruto}}{1,19} \quad | \quad \text{Remanente UTM} = \frac{\text{Remanente CLP}}{\text{UTM}_{\text{mes declaración}}}",
                "tip": (
                    "El IVA en la compra de automóviles o station wagons (Art. 23 N° 4 D.L. 825) NO da derecho a crédito fiscal "
                    "y se registra como 'IVA no recuperable' (a diferencia de un furgón de reparto o una grúa horquilla, que sí dan crédito)."
                ),
                "fuente": (
                    "Prof. RVS (2026), 'Apunte IVA 2026.pdf' (págs. 1-8), 'IVA y Toma de Decisiones.pdf' (pág. 3) "
                    "y 'Ejerc-03 / Ejerc-04 Ejercicio IVA (Datos).xlsx'."
                ),
                "marcador_moodle": "TRIBUTARIA 2026/IVA y Toma de Decisiones.pdf | Página 3",
                "extracto_literal": (
                    "--- [TRIBUTARIA 2026/IVA y Toma de Decisiones.pdf | Página 3] ---\n"
                    "Remanente Anterior en UTM = Remanente Anterior $ / UTM Mes declaración."
                ),
                "links": [
                    ("D.L. N° 825 Ley sobre Impuesto a las Ventas y Servicios (BCN)", "https://www.bcn.cl/leychile/navegar?idNorma=6369"),
                    ("Abrir Suite Tributaria 2026 en Streamlit", "https://gestion-tributaria-2026-avecwdhabftj7rjnx5knmb.streamlit.app/"),
                ],
            },
            {
                "id": "trib_art97_delitos",
                "doc_pdf": "Caso GTTD Emision Facturas Falsas (Datos).pdf",
                "pag_pdf": 1,
                "titulo": "2. Infracciones y Delitos Tributarios (Art. 97 Código Tributario y Ley N° 20.393)",
                "formula": r"\text{Art. 97 N° 4 CT (Facturas Falsas): Multa } 50\%\text{–}400\% \text{ del tributo eludido} + \text{Presidio}",
                "tip": (
                    "En el caso 'El Espejo Tributario (Constructora del Sur S.A.)', ingresar 3 facturas falsas por $50.000.000 netos "
                    "($9.500.000 de IVA) obliga a restituir el IVA Crédito Fiscal, rechaza el gasto en Renta y configura delito penal (Art. 97 N° 4 CT)."
                ),
                "fuente": (
                    "Prof. RVS (2026), 'Caso GTTD Emision Facturas Falsas (Datos).pdf' (págs. 1-2) y "
                    "'Clase Infracciones Sanciones Delitos GTD.pdf' (láminas 4-21)."
                ),
                "marcador_moodle": "TRIBUTARIA 2026/Caso GTTD Emision Facturas Falsas (Datos).pdf | Página 1",
                "extracto_literal": (
                    "--- [TRIBUTARIA 2026/Caso GTTD Emision Facturas Falsas (Datos).pdf | Páginas 1 y 2] ---\n"
                    "Servicios y Asesorías Global SpA emite a Constructora del Sur S.A. tres facturas electrónicas por $50.000.000 netos más $9.500.000 de IVA sin prestación real."
                ),
                "links": [
                    ("Código Tributario D.L. N° 830 en Biblioteca del Congreso Nacional", "https://www.bcn.cl/leychile/navegar?idNorma=6374"),
                ],
            },
        ],
    },
    "Introducción al Deporte Paralímpico": {
        "docente": "Prof. Exal García Carrillo",
        "app_url": "https://app-context-extractor-cl8x5kwfdodzvmx7m3vean.streamlit.app/",
        "tarjetas": [
            {
                "id": "para_taller2_casos",
                "doc_pdf": "Taller_II_Deporte_Paralimpico.pdf",
                "pag_pdf": 1,
                "titulo": "1. Análisis de Casos y Clasificación Funcional (Para Atletismo vs. Para Powerlifting)",
                "formula": r"\text{Para Atletismo: } T\text{ (Pista)} / F\text{ (Campo)} \quad | \quad \text{Para Powerlifting: Categorías solo por Peso Corporal}",
                "tip": (
                    "Caso 1 (Martín): amputación transtibial unilateral con prótesis, clase T64. Caso 2 (Carolina, lesión medular T10): "
                    "Para Powerlifting compite en clase única dividida por sexo y peso corporal. Caso 3 (Diego, PC espástica): F35-F38. "
                    "Caso 4 (Valentina, discapacidad visual): elegible en disco (F11-F13), pero NO en Para Powerlifting."
                ),
                "fuente": (
                    "Prof. Exal García Carrillo (2026), 'Taller_II_Deporte_Paralimpico.pdf', Casos 1 al 4, págs. 1-3."
                ),
                "marcador_moodle": "Taller_II_Deporte_Paralimpico.pdf | Página 1",
                "extracto_literal": (
                    "--- [[2026]A1 INTRODUCCIÓN AL DEPORTE PARALÍMPICO 2026/Taller_II_Deporte_Paralimpico.pdf | Páginas 1-3] ---\n"
                    "Casos 1 (Martín), 2 (Carolina), 3 (Diego) y 4 (Valentina)."
                ),
                "links": [
                    ("Clasificación Oficial Comité Paralímpico Internacional (IPC)", "https://www.paralympic.org/classification"),
                ],
            },
        ],
    },
}


# ==============================================================================
# 5. BUSCADOR QUIRÚRGICO DE PDFS EN GOOGLE DRIVE (SUELTOS O DENTRO DEL .ZIP)
# ==============================================================================

def _buscar_bytes_pdf_en_drive_moodle_o_repo(nombre_pdf):
    clave_obj = _normalizar_clave_nombre(nombre_pdf)

    try:
        archivos_drive = listar_archivos_google_drive_service_account()

        for arch in archivos_drive:
            nom_d = arch.get("name", "")
            if nom_d.lower().endswith(".pdf"):
                clave_d = _normalizar_clave_nombre(nom_d)
                if clave_d == clave_obj or (len(clave_obj) >= 6 and (clave_obj in clave_d or clave_d in clave_obj)):
                    pdf_bytes = descargar_bytes_archivo_drive_por_id(arch["id"])
                    return pdf_bytes, f"Google Drive PDF directo ({nom_d})"

        for arch in archivos_drive:
            nom_d = arch.get("name", "")
            tam_d = int(arch.get("size", 0))
            if nom_d.lower().endswith(".zip") and tam_d > 0:
                entradas_zip = listar_indice_interno_zip_en_drive(arch["id"], tam_d)
                elegida = None
                for e in entradas_zip:
                    if e["extension"] == ".pdf":
                        c_e = _normalizar_clave_nombre(e["nombre_archivo"])
                        if c_e == clave_obj:
                            elegida = e
                            break
                if not elegida:
                    for e in entradas_zip:
                        if e["extension"] == ".pdf":
                            c_e = _normalizar_clave_nombre(e["nombre_archivo"])
                            if len(clave_obj) >= 5 and (clave_obj in c_e or c_e in clave_obj):
                                elegida = e
                                break
                if elegida:
                    pdf_bytes = extraer_archivo_individual_de_zip_drive(
                        arch["id"],
                        elegida["lfh_offset"],
                        elegida["comp_size"],
                        elegida["comp_method"],
                    )
                    return pdf_bytes, f"Google Drive ZIP Quirúrgico ({nom_d} -> {elegida['ruta_completa']})"
    except Exception:
        pass

    return None, None


def _recortar_paginas_pdf_en_base64(pdf_bytes, pag_inicio, pag_fin=None):
    try:
        from pypdf import PdfReader, PdfWriter
        lector = PdfReader(io.BytesIO(pdf_bytes))
        total_pags = len(lector.pages)
        p_ini = max(1, min(int(pag_inicio), total_pags))
        p_fin = max(p_ini, min(int(pag_fin if pag_fin else p_ini), total_pags))

        escritor = PdfWriter()
        for idx_p in range(p_ini - 1, p_fin):
            escritor.add_page(lector.pages[idx_p])

        out_buf = io.BytesIO()
        escritor.write(out_buf)
        b64_str = base64.b64encode(out_buf.getvalue()).decode("utf-8")
        return b64_str, total_pags, p_ini, p_fin
    except Exception:
        return None, 0, 1, 1


def mostrar_visor_documento_citado(nombre_pdf, pagina_objetivo=1, prefijo_key="hub"):
    c_pag1, c_pag2, c_pag3 = st.columns([1.1, 1.1, 2.8])
    with c_pag1:
        p_ini_sel = st.number_input(
            "Desde Página / Lámina:",
            min_value=1,
            max_value=1500,
            value=int(pagina_objetivo),
            step=1,
            key=f"{prefijo_key}_v_ini_{nombre_pdf}",
        )
    with c_pag2:
        p_fin_sel = st.number_input(
            "Hasta Página / Lámina:",
            min_value=1,
            max_value=1500,
            value=int(pagina_objetivo),
            step=1,
            key=f"{prefijo_key}_v_fin_{nombre_pdf}",
        )
    with c_pag3:
        st.caption(
            f"**Extracción Quirúrgica HTTP Range Activa:** `{SERVICE_ACCOUNT_EMAIL}`  \n"
            f"Documento objetivo dentro de `Respaldo_ULagos_2026.zip`: `{nombre_pdf}`"
        )

    with st.spinner(f"Extrayendo solo los bytes de '{nombre_pdf}' desde Google Drive y recortando página {int(p_ini_sel)}..."):
        pdf_bytes, fuente_origen = _buscar_bytes_pdf_en_drive_moodle_o_repo(nombre_pdf)

    if pdf_bytes:
        b64_recorte, tot_p, r_i, r_f = _recortar_paginas_pdf_en_base64(pdf_bytes, p_ini_sel, p_fin_sel)
        if b64_recorte:
            st.success(
                f"Documento extraído en vivo vía {fuente_origen} — Mostrando página/lámina {r_i} a {r_f} (de {tot_p} páginas totales)."
            )
            renderizar_visor_pdf_canvas_js(b64_recorte, nombre_pdf, r_i, r_f)
            st.download_button(
                label=f"Descargar PDF completo ({nombre_pdf})",
                data=pdf_bytes,
                file_name=nombre_pdf,
                mime="application/pdf",
                use_container_width=True,
                key=f"{prefijo_key}_dl_{nombre_pdf}",
            )
            return

    st.warning(
        f"No se encontró `{nombre_pdf}` o falta configurar `gcp_service_account_json` en Streamlit Secrets."
    )


# ==============================================================================
# 6. NODO RECEPTOR DEL PUENTE (SE EJECUTA DENTRO DE TUS OTRAS APPS STREAMLIT)
# ==============================================================================

def ejecutar_nodo_receptor_puente(nombre_repo_hijo="PROYECTOS-2026"):
    meta_hijo = MAPA_REPOS_A_RAMOS.get(nombre_repo_hijo, MAPA_REPOS_A_RAMOS["PROYECTOS-2026"])
    ramo_defecto = meta_hijo["ramo"]
    if ramo_defecto not in CUADRILLAS_LITERATURA_POR_RAMO:
        ramo_defecto = "Evaluación Integrada de Proyectos (FDIC26)"

    st.divider()
    st.markdown(
        f"""
        <div style="background-color:#0F172A;color:#FFFFFF;padding:14px 20px;border-radius:8px;
                    border-left:6px solid #2563EB;margin-top:12px;margin-bottom:12px;">
            <div style="font-size:16px;font-weight:700;color:#FFFFFF;">
                PUENTE CENTRAL DE LITERATURA OFICIAL Y VISOR GOOGLE DRIVE (5 TB) — {ramo_defecto.upper()}
            </div>
            <div style="font-size:12.5px;color:#CBD5E1;margin-top:3px;">
                Conectado en tiempo real con <code>github-context-extractor</code> y Google Cloud (<code>{SERVICE_ACCOUNT_EMAIL}</code>).
                Pulsa cualquier referencia para abrir la lámina o página exacta del PDF original sin salir de esta aplicación.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander(f"Abrir Cuadrillas Metodológicas, Fórmulas y Visor PDF en Página Exacta — {ramo_defecto}", expanded=True):
        info_r = CUADRILLAS_LITERATURA_POR_RAMO[ramo_defecto]
        tarjetas_r = info_r["tarjetas"]

        for i in range(0, len(tarjetas_r), 2):
            cols = st.columns(2)
            for j in range(2):
                if i + j < len(tarjetas_r):
                    t = tarjetas_r[i + j]
                    with cols[j]:
                        enlaces_ext = " ".join(
                            f"<a href='{u}' target='_blank' style='display:inline-block;background:#EFF6FF;color:#1D4ED8;"
                            f"border:1px solid #BFDBFE;border-radius:4px;padding:3px 8px;font-size:11px;font-weight:700;"
                            f"text-decoration:none;margin-right:4px;margin-top:4px;'>{lbl} &#8599;</a>"
                            for lbl, u in t.get("links", [])
                        )
                        st.markdown(
                            f"""
                            <div style="background:#FFFFFF;border:1px solid #CBD5E1;border-top:4px solid #1E3A8A;
                                        border-radius:6px;padding:12px;margin-bottom:8px;">
                                <div style="font-weight:700;color:#0F172A;font-size:13.5px;margin-bottom:5px;">{t['titulo']}</div>
                                <div style="color:#334155;font-size:12.5px;line-height:1.45;margin-bottom:8px;">{t['tip']}</div>
                                <div style="background:#F1F5F9;border-left:3px solid #0284C7;padding:6px 9px;
                                            font-size:11.5px;color:#0F172A;font-weight:600;margin-bottom:6px;">
                                    Ubicación en la Literatura: {t['fuente']}
                                </div>
                                <div>{enlaces_ext}</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                        if t.get("formula"):
                            st.latex(t["formula"])

        st.markdown("#### Visor Directo de Láminas y Páginas Citadas (Extracción Quirúrgica desde Google Drive):")
        opciones_tarjetas = [
            f"{t['titulo']} -> Abrir '{t['doc_pdf']}' en Página/Lámina {t['pag_pdf']}"
            for t in tarjetas_r
        ]
        idx_t_sel = st.selectbox(
            "Selecciona la referencia cuyo documento PDF original deseas visualizar aquí mismo:",
            options=range(len(opciones_tarjetas)),
            format_func=lambda k: opciones_tarjetas[k],
            key=f"puente_sel_{nombre_repo_hijo}",
        )
        t_elegida = tarjetas_r[idx_t_sel]
        mostrar_visor_documento_citado(
            t_elegida["doc_pdf"],
            pagina_objetivo=t_elegida["pag_pdf"],
            prefijo_key=f"p_{nombre_repo_hijo}_{t_elegida['id']}",
        )


# ==============================================================================
# 7. BÓVEDA LOCAL (.TXT O .ZIP) Y UTILIDADES DE LITERATURA
# ==============================================================================

@st.cache_data(show_spinner=False)
def cargar_boveda_moodle_del_repo():
    """Carga la bóveda destilada desde un .txt local o desde Todos_Los_Ramos_Destilados_TXT.zip."""
    carpeta = os.path.dirname(os.path.abspath(__file__))

    candidatos_txt = [
        f for f in os.listdir(carpeta)
        if os.path.isfile(os.path.join(carpeta, f))
        and f.lower().endswith(".txt")
        and f not in ("requirements.txt", "packages.txt")
    ]
    if candidatos_txt:
        candidatos_txt.sort(key=lambda x: os.path.getsize(os.path.join(carpeta, x)), reverse=True)
        archivo_maestro = candidatos_txt[0]
        ruta_m = os.path.join(carpeta, archivo_maestro)
        with open(ruta_m, "r", encoding="utf-8", errors="replace") as fp:
            texto_total = fp.read()

        marcador = "==========================================================================================\nSUPER CONTEXTO DE CÁTEDRA MOODLE ULAGOS:"
        partes = texto_total.split(marcador)
        secciones = {}
        for p in partes[1:]:
            lineas = p.splitlines()
            nombre_sec = lineas[0].strip() if lineas else "SECCIÓN"
            secciones[nombre_sec] = marcador + p
        if not secciones and texto_total.strip():
            secciones[os.path.splitext(archivo_maestro)[0]] = texto_total
        return archivo_maestro, texto_total, secciones

    candidatos_zip = [
        f for f in os.listdir(carpeta)
        if os.path.isfile(os.path.join(carpeta, f)) and f.lower().endswith(".zip")
    ]
    if candidatos_zip:
        candidatos_zip.sort(key=lambda x: os.path.getsize(os.path.join(carpeta, x)), reverse=True)
        archivo_zip = candidatos_zip[0]
        ruta_z = os.path.join(carpeta, archivo_zip)
        secciones = {}
        bloques_tot = []
        try:
            with zipfile.ZipFile(ruta_z, "r") as zf:
                for zi in sorted(zf.infolist(), key=lambda x: x.filename):
                    if not zi.is_dir() and zi.filename.lower().endswith(".txt"):
                        txt_i = zf.read(zi).decode("utf-8", errors="replace")
                        nom_s = os.path.splitext(os.path.basename(zi.filename))[0]
                        secciones[nom_s] = txt_i
                        bloques_tot.append(f"\n{'=' * 90}\nASIGNATURA: {nom_s}\n{'=' * 90}\n{txt_i}")
            if secciones:
                return archivo_zip, "\n".join(bloques_tot), secciones
        except Exception:
            pass

    return None, "", {}


def buscar_pagina_en_destilado_local(marcador):
    _, texto_completo, _ = cargar_boveda_moodle_del_repo()
    if not texto_completo or not marcador:
        return None
    pos = texto_completo.find(marcador)
    if pos == -1:
        return None
    inicio = max(0, pos - 40)
    fin = min(len(texto_completo), pos + 2400)
    return texto_completo[inicio:fin]


def buscar_tarjeta_por_id(cita_id):
    for nombre_ramo, datos in CUADRILLAS_LITERATURA_POR_RAMO.items():
        for t in datos["tarjetas"]:
            if t["id"] == cita_id:
                return nombre_ramo, datos["docente"], t
    return None, None, None


def formatear_cuadrilla_en_texto_plano(nombre_ramo):
    if nombre_ramo not in CUADRILLAS_LITERATURA_POR_RAMO:
        return ""
    info = CUADRILLAS_LITERATURA_POR_RAMO[nombre_ramo]
    lineas = [
        "-" * 90,
        f"CUADRILLA METODOLÓGICA Y RESPALDO EN LITERATURA OFICIAL: {nombre_ramo.upper()}",
        f"Docente Cátedra ULagos: {info['docente']}",
        "-" * 90,
    ]
    for t in info["tarjetas"]:
        lineas.append(f"[*] {t['titulo']}")
        lineas.append(f"    - Fórmula / Regla: {t['formula']}")
        lineas.append(f"    - Tip de Cátedra : {t['tip']}")
        lineas.append(f"    - Fuente Exacta  : {t['fuente']}")
        if t.get("links"):
            enlaces_str = " | ".join(f"{lbl}: {url}" for lbl, url in t["links"])
            lineas.append(f"    - Hipervínculos  : {enlaces_str}")
        lineas.append("")
    lineas.append("-" * 90 + "\n")
    return "\n".join(lineas)


# ==============================================================================
# 8. RENDERIZADOR DE CUADRILLAS CON HIPERVÍNCULOS Y VISOR PDF DE GOOGLE DRIVE
# ==============================================================================

def renderizar_cuadrillas_ramo(nombre_ramo):
    info = CUADRILLAS_LITERATURA_POR_RAMO[nombre_ramo]
    st.markdown(
        f"<div class='sec-header'>{nombre_ramo} — Docente: {info['docente']}</div>",
        unsafe_allow_html=True,
    )
    tarjetas = info["tarjetas"]
    for i in range(0, len(tarjetas), 2):
        cols = st.columns(2)
        for j in range(2):
            if i + j < len(tarjetas):
                t = tarjetas[i + j]
                with cols[j]:
                    links_html = [
                        f"<a class='lit-link-internal' href='?cita={t['id']}' target='_self'>"
                        f"Abrir PDF desde Google Drive en Pág. {t.get('pag_pdf', 1)} ({t.get('doc_pdf', 'PDF')})</a>"
                    ]
                    for lbl_link, url_link in t.get("links", []):
                        links_html.append(
                            f"<a class='lit-link' href='{url_link}' target='_blank' rel='noopener noreferrer'>"
                            f"{lbl_link} &#8599;</a>"
                        )
                    barra_enlaces = "<div class='link-bar'>" + "".join(links_html) + "</div>"

                    st.markdown(
                        f"""
                        <div class="tip-card">
                            <div class="tip-title">{t['titulo']}</div>
                            <div class="tip-body">{t['tip']}</div>
                            <div class="tip-source">Ubicación en la Literatura: {t['fuente']}</div>
                            {barra_enlaces}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    if t.get("formula"):
                        st.latex(t["formula"])

                    with st.expander(f"Ver transcripción de texto ({t['marcador_moodle']})", expanded=False):
                        st.code(t["extracto_literal"], language="text")


# ==============================================================================
# 9. INTERFAZ PRINCIPAL DEL HUB (SOLO SI NO ES INVOCADO COMO PUENTE REMOTO)
# ==============================================================================

if not ES_MODO_PUENTE_REMOTO:
    st.markdown(
        """
        <div class="top-banner">
            <h1>SUPER HUB ACADÉMICO Y CENTRAL DE MANDO ULAGOS 2026: GITHUB CMS + GOOGLE DRIVE API (5 TB)</h1>
            <p>Conectado a Google Cloud (motor-sii-python) y GitHub API para extraer todo tu portafolio y controlar remotamente About, README.md, requirements.txt y app.py desde un solo panel seguro.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cita_activa = st.query_params.get("cita", None)
    if cita_activa:
        ramo_c, doc_c, tarjeta_c = buscar_tarjeta_por_id(cita_activa)
        if tarjeta_c:
            st.markdown(
                f"""
                <div class="cita-box">
                    <div style="font-weight:700;font-size:15px;color:#854D0E;margin-bottom:4px;">
                        VISOR DE DOCUMENTO ORIGINAL VÍA GOOGLE DRIVE API — {ramo_c.upper()} ({doc_c})
                    </div>
                    <div style="font-weight:700;font-size:14px;color:#0F172A;margin-bottom:6px;">
                        {tarjeta_c['titulo']}
                    </div>
                    <div style="font-size:12.5px;color:#334155;margin-bottom:6px;">
                        <b>Referencia documental:</b> {tarjeta_c['fuente']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.latex(tarjeta_c["formula"])

            v_tab1, v_tab2 = st.tabs([
                f"1. Visor PDF Original desde Google Drive ({tarjeta_c.get('doc_pdf', 'Documento')} — Pág. {tarjeta_c.get('pag_pdf', 1)})",
                "2. Transcripción Literal de la Página en la Bóveda",
            ])
            with v_tab1:
                mostrar_visor_documento_citado(
                    tarjeta_c.get("doc_pdf", "Clase2.pdf"),
                    pagina_objetivo=tarjeta_c.get("pag_pdf", 1),
                )
            with v_tab2:
                st.code(tarjeta_c["extracto_literal"], language="text")
                frag_local = buscar_pagina_en_destilado_local(tarjeta_c.get("marcador_moodle", ""))
                if frag_local:
                    st.caption("Contexto extendido extraído en vivo desde el archivo maestro del repositorio:")
                    st.code(frag_local, language="text")

            if st.button("Cerrar Visor de Documento Citado"):
                st.query_params.clear()
                st.rerun()
            st.divider()

    with st.sidebar:
        st.markdown("### Acceso Central de Mando")
        usuario_gh = st.text_input("Usuario GitHub:", value=GITHUB_USER_DEFAULT)

        clave_admin = st.text_input(
            "Clave Admin (desbloquea repos privados y Pestaña 5):",
            value="",
            type="password",
            help="Valida tu identidad en servidor. El token de GitHub nunca se envía al navegador.",
        )

        token_gh = ""
        try:
            clave_real = str(st.secrets.get("ADMIN_PASSWORD", ""))
            token_secreto = str(st.secrets.get("GITHUB_TOKEN", ""))
        except Exception:
            clave_real = ""
            token_secreto = ""

        if clave_real and clave_admin and hmac.compare_digest(clave_admin, clave_real):
            token_gh = token_secreto
            if token_gh.strip():
                st.success("Modo Admin activo (token protegido en servidor).")
            else:
                st.warning("Clave correcta, pero falta definir GITHUB_TOKEN en Secrets.")
        elif clave_admin:
            st.error("Clave Admin incorrecta.")
        else:
            st.caption("Modo público (solo lectura).")

        incluir_lit_en_txt = st.checkbox(
            "Incluir Cuadrilla de Literatura e Hipervínculos en el .TXT",
            value=True,
        )

        st.divider()
        st.markdown("### Estado Google Cloud (5 TB)")
        st.caption("**Proyecto GCP:** `motor-sii-python`")
        st.code(SERVICE_ACCOUNT_EMAIL, language="text")
        if st.button("Refrescar Caches Drive / GitHub", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "1. Super Extractor GitHub",
        "2. Cuadrillas y Visor PDF (Drive API)",
        "3. Explorador Quirúrgico Google Drive (.ZIP)",
        "4. Bóveda Destilada en 1 Clic",
        "5. Super Central de Mando (Editor Remoto de Repos)",
    ])

    # --------------------------------------------------------------------------
    # PESTAÑA 1: SUPER EXTRACTOR GITHUB (MÓDULO EXTERNO extractor_github_avanzado.py)
    # --------------------------------------------------------------------------
    with tab1:
        try:
            from extractor_github_avanzado import renderizar_extractor_github

            renderizar_extractor_github(
                usuario_gh=usuario_gh,
                token_gh=token_gh,
                mapa_repos=MAPA_REPOS_A_RAMOS,
                incluir_lit_en_txt=incluir_lit_en_txt,
                fn_formatear_cuadrilla=formatear_cuadrilla_en_texto_plano,
                fn_cargar_boveda=cargar_boveda_moodle_del_repo,
            )
        except ImportError:
            st.error(
                "Falta subir el archivo `extractor_github_avanzado.py` en la raíz del repositorio "
                "`github-context-extractor` para activar el Super Extractor."
            )
        except SyntaxError as exc_syn1:
            st.error(
                f"Error de sintaxis en `extractor_github_avanzado.py` (línea {exc_syn1.lineno}): {exc_syn1.msg}."
            )

    # --------------------------------------------------------------------------
    # PESTAÑA 2: CUADRILLAS CON APERTURA QUIRÚRGICA DE PDF DESDE GOOGLE DRIVE API
    # --------------------------------------------------------------------------
    with tab2:
        st.markdown(
            "<div class='sec-header'>2. CUADRILLAS METODOLÓGICAS CON APERTURA DEL PDF ORIGINAL EN LA PÁGINA EXACTA</div>",
            unsafe_allow_html=True,
        )
        st.caption(
            "Haz clic en el botón verde de cualquier tarjeta: el motor extraerá vía HTTP Range únicamente los bytes "
            "de ese PDF desde adentro de tu 'Respaldo_ULagos_2026.zip' en Google Drive y dibujará la lámina exacta con PDF.js."
        )
        ramos_disponibles_lit = ["Mostrar Todos los Ramos"] + list(CUADRILLAS_LITERATURA_POR_RAMO.keys())
        filtro_ramo_lit = st.selectbox("Filtrar cuadrillas por asignatura:", options=ramos_disponibles_lit)

        if filtro_ramo_lit == "Mostrar Todos los Ramos":
            for nombre_r in CUADRILLAS_LITERATURA_POR_RAMO:
                renderizar_cuadrillas_ramo(nombre_r)
        else:
            renderizar_cuadrillas_ramo(filtro_ramo_lit)

    # --------------------------------------------------------------------------
    # PESTAÑA 3: EXPLORADOR QUIRÚRGICO DE GOOGLE DRIVE (.ZIP Y PDFS)
    # --------------------------------------------------------------------------
    with tab3:
        st.markdown(
            "<div class='sec-header'>3. EXPLORADOR QUIRÚRGICO DE GOOGLE DRIVE (INSPECCIÓN INTERNA DE .ZIP VÍA HTTP RANGE)</div>",
            unsafe_allow_html=True,
        )

        try:
            archivos_drv = listar_archivos_google_drive_service_account()
            st.success(
                f"Autenticación OAuth2 exitosa con `drive.googleapis.com` (Proyecto: `motor-sii-python`). "
                f"Elementos raíz compartidos detectados: **{len(archivos_drv)}**."
            )

            if archivos_drv:
                df_drv = pd.DataFrame([
                    {
                        "Nombre en Google Drive": a.get("name", ""),
                        "Tipo MIME": a.get("mimeType", ""),
                        "Tamaño (KB)": round(int(a.get("size", 0)) / 1024, 1) if a.get("size") else 0.0,
                        "ID de Google Drive": a.get("id", ""),
                        "Abrir en Drive": a.get("webViewLink", ""),
                    }
                    for a in archivos_drv
                ])
                st.dataframe(
                    df_drv,
                    column_config={"Abrir en Drive": st.column_config.LinkColumn("Enlace Drive")},
                    use_container_width=True,
                    hide_index=True,
                )

                zips_en_drive = [
                    a for a in archivos_drv
                    if a.get("name", "").lower().endswith(".zip") and int(a.get("size", 0)) > 0
                ]

                for z_arch in zips_en_drive:
                    z_id = z_arch["id"]
                    z_nom = z_arch["name"]
                    z_size = int(z_arch["size"])

                    st.markdown(
                        f"<div class='sec-header'>CONTENIDO INTERNO DE {z_nom} ({z_size / (1024*1024):,.1f} MB) — LEÍDO VÍA HTTP RANGE EN 0,2 SEGUNDOS</div>",
                        unsafe_allow_html=True,
                    )

                    entradas_internas = listar_indice_interno_zip_en_drive(z_id, z_size)
                    if entradas_internas:
                        carpetas_unicas = ["Todas las Asignaturas"] + sorted(
                            list({e["asignatura_carpeta"] for e in entradas_internas})
                        )
                        col_f1, col_f2 = st.columns([1.4, 2.6])
                        with col_f1:
                            filtro_carpeta = st.selectbox(
                                "Filtrar por Carpeta / Ramo dentro del .ZIP:",
                                options=carpetas_unicas,
                                key=f"f_carp_{z_id}",
                            )
                        entradas_filtradas = [
                            e for e in entradas_internas
                            if filtro_carpeta == "Todas las Asignaturas" or e["asignatura_carpeta"] == filtro_carpeta
                        ]
                        with col_f2:
                            st.info(
                                f"Se desglosaron **{len(entradas_filtradas)} archivos** dentro de `{z_nom}` "
                                f"(de un total de {len(entradas_internas)} documentos) leyendo solo los últimos 64 KB del archivo."
                            )

                        df_int = pd.DataFrame([
                            {
                                "Asignatura / Carpeta": e["asignatura_carpeta"],
                                "Documento": e["nombre_archivo"],
                                "Formato": e["extension"],
                                "Tamaño Real (KB)": e["kb_real"],
                                "Tamaño Comprimido (KB)": round(e["comp_size"] / 1024.0, 1),
                                "Offset Byte en Drive": e["lfh_offset"],
                            }
                            for e in entradas_filtradas
                        ])
                        st.dataframe(df_int, use_container_width=True, hide_index=True)

                        docs_visibles = [
                            e for e in entradas_filtradas
                            if e["extension"] in (".pdf", ".xlsx", ".xls", ".txt", ".docx")
                        ]
                        if docs_visibles:
                            st.markdown("#### Visor y Extractor Quirúrgico de Documentos Internos del .ZIP:")
                            c_v1, c_v2, c_v3 = st.columns([2.2, 0.9, 0.9])
                            with c_v1:
                                opciones_etiquetas = [
                                    f"{e['asignatura_carpeta']} / {e['nombre_archivo']} ({e['kb_real']} KB)"
                                    for e in docs_visibles
                                ]
                                idx_doc_sel = st.selectbox(
                                    "Elige cualquier PDF o Excel dentro de Respaldo_ULagos_2026.zip para abrirlo en vivo:",
                                    options=range(len(opciones_etiquetas)),
                                    format_func=lambda i: opciones_etiquetas[i],
                                    key=f"sel_int_{z_id}",
                                )
                            doc_obj = docs_visibles[idx_doc_sel]
                            with c_v2:
                                pag_ini_int = st.number_input(
                                    "Desde página (PDF):",
                                    min_value=1,
                                    max_value=1500,
                                    value=1,
                                    step=1,
                                    key=f"pi_int_{z_id}",
                                )
                            with c_v3:
                                pag_fin_int = st.number_input(
                                    "Hasta página (PDF):",
                                    min_value=1,
                                    max_value=1500,
                                    value=1,
                                    step=1,
                                    key=f"pf_int_{z_id}",
                                )

                            with st.spinner(f"Extrayendo solo '{doc_obj['nombre_archivo']}' ({doc_obj['kb_real']} KB) desde Google Drive..."):
                                raw_file_bytes = extraer_archivo_individual_de_zip_drive(
                                    z_id,
                                    doc_obj["lfh_offset"],
                                    doc_obj["comp_size"],
                                    doc_obj["comp_method"],
                                )

                            st.download_button(
                                label=f"DESCARGAR ARCHIVO INDIVIDUAL: {doc_obj['nombre_archivo']} ({doc_obj['kb_real']} KB)",
                                data=raw_file_bytes,
                                file_name=doc_obj["nombre_archivo"],
                                mime="application/octet-stream",
                                use_container_width=True,
                            )

                            if doc_obj["extension"] == ".pdf":
                                b64_cut, tot_p_drv, ri_d, rf_d = _recortar_paginas_pdf_en_base64(
                                    raw_file_bytes, pag_ini_int, pag_fin_int
                                )
                                if b64_cut:
                                    st.success(
                                        f"Mostrando página/lámina {ri_d} a {rf_d} (de {tot_p_drv} totales) de `{doc_obj['nombre_archivo']}`:"
                                    )
                                    renderizar_visor_pdf_canvas_js(b64_cut, doc_obj["nombre_archivo"], ri_d, rf_d)
                            elif doc_obj["extension"] in (".xlsx", ".xls"):
                                xls_obj = pd.ExcelFile(io.BytesIO(raw_file_bytes))
                                hoja_sel = st.selectbox("Hoja del archivo Excel:", options=xls_obj.sheet_names)
                                df_hoja = pd.read_excel(xls_obj, sheet_name=hoja_sel)
                                st.dataframe(df_hoja, use_container_width=True)
        except Exception as exc_drv:
            st.error(f"Error al consultar Google Drive API: {exc_drv}")

    # --------------------------------------------------------------------------
    # PESTAÑA 4: BÓVEDA MOODLE EN 1 CLIC Y BUSCADOR DE PÁGINAS
    # --------------------------------------------------------------------------
    with tab4:
        st.markdown(
            "<div class='sec-header'>4. BÓVEDA DE CÁTEDRA ALOJADA EN EL SERVIDOR Y BUSCADOR DE PÁGINAS</div>",
            unsafe_allow_html=True,
        )
        nombre_maestro, texto_maestro, dict_secciones = cargar_boveda_moodle_del_repo()

        if dict_secciones:
            st.write(f"Archivo maestro detectado en el repositorio: `{nombre_maestro}` ({len(dict_secciones)} asignaturas indexadas).")
            cols_bov = st.columns(min(3, len(dict_secciones)))
            for idx_s, (nom_sec, contenido_sec) in enumerate(dict_secciones.items()):
                slug_sec = re.sub(r"[^A-Za-z0-9]+", "_", nom_sec).strip("_").upper()
                kb_sec = len(contenido_sec.encode("utf-8")) / 1024.0
                with cols_bov[idx_s % len(cols_bov)]:
                    st.download_button(
                        label=f"DESCARGAR CÁTEDRA: {nom_sec} ({kb_sec:,.0f} KB)",
                        data=contenido_sec.encode("utf-8"),
                        file_name=f"CATEDRA_{slug_sec}_2026.txt",
                        mime="text/plain",
                        use_container_width=True,
                        key=f"btn_bov_{idx_s}",
                    )

            busqueda = st.text_input(
                "Buscar autor, fórmula o marcador de página en toda la Bóveda (ej. 'Fontaine', 'Hamada', 'Weber', 'Página 20'):"
            )
            if busqueda.strip():
                lineas_tot = texto_maestro.splitlines()
                bloques_encontrados = []
                for idx_l, lin in enumerate(lineas_tot):
                    if busqueda.lower() in lin.lower():
                        ini_b = max(0, idx_l - 2)
                        fin_b = min(len(lineas_tot), idx_l + 6)
                        bloques_encontrados.append("\n".join(lineas_tot[ini_b:fin_b]))
                        if len(bloques_encontrados) >= 15:
                            break
                st.write(f"Mostrando las primeras {len(bloques_encontrados)} coincidencias con contexto de página:")
                st.code("\n\n" + ("\n" + "=" * 60 + "\n").join(bloques_encontrados), language="text")
        else:
            st.info("No se encontró ningún archivo `.txt` ni `.zip` destilado en la raíz del repositorio.")

    # --------------------------------------------------------------------------
    # PESTAÑA 5: SUPER CENTRAL DE MANDO (MÓDULO EXTERNO central_mando_github.py)
    # --------------------------------------------------------------------------
    with tab5:
        try:
            from central_mando_github import renderizar_central_de_mando

            renderizar_central_de_mando(
                usuario_gh=usuario_gh,
                token_gh=token_gh,
                mapa_repos=MAPA_REPOS_A_RAMOS,
                cuadrillas_lit=CUADRILLAS_LITERATURA_POR_RAMO,
                fn_preview_puente=ejecutar_nodo_receptor_puente,
            )
        except ImportError:
            st.error(
                "Falta subir el archivo `central_mando_github.py` en la raíz del repositorio `github-context-extractor` "
                "para activar la Pestaña 5."
            )
        except SyntaxError as exc_syn:
            st.error(
                f"Error de sintaxis dentro de `central_mando_github.py` (línea {exc_syn.lineno}): {exc_syn.msg}. "
                "Vuelve a subir ese archivo completo."
            )
