# -*- coding: utf-8 -*-
"""
app.py — SUPER HUB ACADÉMICO Y CENTRAL DE MANDO MULTI-REPOSITORIO ULAGOS 2026
Repositorio Maestro: https://github.com/mauriciovargas1516-ux/github-context-extractor
- Orquestador principal del Super Hub (Pestañas 1 a 4) conectado modularmente
  con central_mando_github.py (Pestaña 5).
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
import urllib.request
import urllib.error
from datetime import datetime

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
                    "• Juego justo (Lámina 8
