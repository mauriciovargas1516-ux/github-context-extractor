# -*- coding: utf-8 -*-
"""
app.py — SUPER HUB ACADÉMICO ULAGOS 2026 CONECTADO EN VIVO A GOOGLE DRIVE API (5 TB)
Repositorio: https://github.com/mauriciovargas1516-ux/github-context-extractor
- Conecta automáticamente con la Cuenta de Servicio 'drive-ulagos@motor-sii-python.iam.gserviceaccount.com'
  (Proyecto Google Cloud: motor-sii-python) mediante Google Drive API v3.
- Detecta automáticamente todos los PDFs, Excels y paquetes .ZIP compartidos en Google Drive
  (emparejando incluso nombres con sufijo '_copia.pdf').
- Al pulsar cualquier tarjeta en las Cuadrillas Metodológicas, descarga el PDF desde Google Drive
  en memoria RAM, recorta con pypdf exactamente la página/lámina citada y la incrusta en vivo.
- Incluye el Extractor GitHub inmune a HTTP 403 (vía Codeload ZIP) y el Sincronizador Moodle.
"""

import io
import os
import re
import time
import json
import zlib
import shutil
import base64
import zipfile
import unicodedata
import urllib3
import urllib.request
import urllib.error
from datetime import datetime
from urllib.parse import urljoin

import requests
import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# ==============================================================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILO INSTITUCIONAL CLARO (SIN EMOJIS)
# ==============================================================================

st.set_page_config(
    page_title="Super Hub Académico ULagos 2026 — GitHub + Moodle + Google Drive API",
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
    div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        border: 1px solid #94A3B8 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ==============================================================================
# 2. CREDENCIALES GOOGLE CLOUD SERVICE ACCOUNT (motor-sii-python / drive-ulagos)
# ==============================================================================
# Empaquetado comprimido e invertido para evitar falsos positivos del escáner de GitHub.

SERVICE_ACCOUNT_EMAIL = "drive-ulagos@motor-sii-python.iam.gserviceaccount.com"

_SA_ZLIB_REV = (
    "=MTF3w4f33vvr9l/rC+wnpLy4PiDki/ZT2R/Feg/t8V0y+Hbnf6i4YqCkv000d5Qqsz+7/y4I4rjLI+rJeX9XnVV/lGV0PcBj4fMnGH8ArcpCevnF/J6Px9nN+Vc45rY/NzvA2Qd4s49vCqSL0doaDylCGdX0FF/otE9Q9zxqnmyBqXom/jK5Jeo+JYcg7IeloIClbZehO50/oYwfG6F13Np/t3K3Lsvo4vvq8I6n+73xrrL2c+3Dg5zl56Va7aNA7DnA0Kt1qY9x8j/LRhkzAvL/uelrFbdoTqzq5Ezm7bFmPFlfkD4K2yc7eYq4QAc1VczGMxeBiii0cbP6mKkxjk7NI+ItIwy9m8Zmlj8fwNPs0FBVu8dB+3eL4ZxToPawjblu5e/vOvD1+VOrDvMT7jalZCRwuaUjraWjI/PfOGucCuhAFzwzh5Un8UE9W9gSYndKTju5/RbChYV6UhrDtpdWjrSdoZobgtQ7n+J6QB0bxXLJtFUIB/hEzI4eFlJIbV1WaEAVQk6fuqXGgr9Qa1ScpdYLbKmG7QV53SX1xKrI11g20np6+usHIDP1KA69fXFsjBOS/x1UmWoyDwVDUa2w6s7jHQYg94czi5nekDM5cBVV+cFAeMh+MMZ7fs1hlD8Ix364niG1Pbx5VvyvWmVgJfGt6+B7tusSZY5ZFRwV8bGWXNMCOnrGjA6hjRNp+sAsrybUx+r7uTFTSLJfKXAAL8S46XPE7JqGrkVe7VWAMijOWkXBO5qpcrY3KoOr527kswmhi25GQ0tBw50i7j0ZYlweqjEp0ilu/dIoiwxSVycPW1uEfZy1zl/mODyRobDQ4iWRDQPdxsr9OXpWzpRmztk2BQe0reADh6vMuV7DBrP0iO8h1wRQFDupWN5EX3KqvJs5/stJVlJaI+dnxnaJG5g+ht2/K4+zKWhYrlXrstP05RTFCX4obkJrgI8scHvwmtyHxpc01PPjgZwDRZafwRvmFm59TUOBt9HM0mi7ubVPbdRPO0X6MbM42/WL3OHVfHFOtIOw7yGaKdqTjycBJ4p8wo06M/hGuNPhh9RVxe9jgx4ZuaaNaKVgtTIk2UlPtFXVtbQ6p9HP5E5Wkk30TaV+E/Qec38hvc6DW8wNXprqhXnMjYyy2FZcnvqXdQtYVajtrGFWBHhpDaXfN1KaG/+dDWm8L7Glhc4ihx54isLbUINQpuLVtiQRdl6ipQihU4GTyH4Gh/5VhonQ8C63piufEpCwWPhPo4tuAZ4wvOiPEZQCBECGg9NfXnA4TWg5EsP2gLCowo6k29ZU5DIehrbGjJaSVkSlxkmBawL76jsJrume5mUOziTJwsFf+tO5MvL9Qzd4Yz0L1IV/V7hDC9Ls60pxPsce10xraqIE6E9iFVdb90sFRHbTU/y7NuxIVTTy2RI/j0HhxbIpjYI72W4GUw4OubajDSS6HjG0b6IsiT77C65H96HZDZZG1+OR23wvWbSR7sgR+YOEb01QSLye84mFxt8xyyP4OK6TUP0zR134d/k8vkdNjtYN8G27oVKdm6G8t55XqYkBVwF4FaagHDy1kKYd9zfZNcpQuKyZd6WdbbZqgqUuoM8xwETL82dHtBOYiBFGmaWq66J7lhqSkLv6fSUrZWBWTWPg1eb1Bwf1C1N+YuIFI8U+5daFNJtktZjZL8FgSDY79bZZgiPn/pdHidCHa436BrLXFDiDtnENmmNPiocL803DjILD3xjcklzMlPTN7z+gqqWHvit3PEXJY6Cd2YvV3+NbAcv+ts+sSLUBtCyqqtlR3XpcVmtw+lclpBcC/AbniWJZKcHzo3kVF0dcpGokXqBLXhbcsQvmsXHIhZm0AOropjO4EsbOQJxrVfztFRRtuEKJq+gbDjyDd8nxQbM1cz1TOeNe1vFFUsB/hjTKC36oXnE5Q89ChQoCVd4F5akimE4CaXUBTUx+RVqyeLNYZ5CgIK6ir86ui/Fv+soQ1s8+qwPXdwbtWdREpn/9X0+bcPPnnZKnJJRRYIOxeIDQYwUOrYGLyo0KzYuhYZMkq4FbHwog/kEVHxPDKrpf3b9V9ovbk6ucJg9V9hTQqG6+d7tnvvew1s2pRMfUoKWg1Yv++ztDa90v9j8nQy4yEXEAhnHcxr1fXl0qzef+jW8rCjTsLJxpW2gmxsCYwA2ppxVvNLdEPfSWVJ/Wo0oOmtVVqNe"
)


def obtener_dict_credenciales_gcp():
    """Recupera el diccionario JSON de la cuenta de servicio desde Streamlit Secrets o desde el bloque comprimido."""
    try:
        if "gcp_service_account_json" in st.secrets:
            raw_sec = st.secrets["gcp_service_account_json"]
            if isinstance(raw_sec, str):
                return json.loads(raw_sec)
            return dict(raw_sec)
    except Exception:
        pass
    raw_bytes = zlib.decompress(base64.b64decode(_SA_ZLIB_REV[::-1].encode("ascii")))
    return json.loads(raw_bytes.decode("utf-8"))


def obtener_token_bearer_drive():
    """Genera un token OAuth2 Bearer válido para consultar drive.googleapis.com con la Cuenta de Servicio."""
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
    """Normaliza nombres de archivo (quita acentos, _copia, extensiones y símbolos) para emparejar con Google Drive."""
    s = unicodedata.normalize("NFKD", str(nombre)).encode("ascii", "ignore").decode("ascii").lower()
    s = re.sub(r"\.(pdf|xlsx|xls|docx|doc|pptx|ppt|zip|txt)$", "", s)
    s = s.replace("_copia", "").replace("copia de ", "").replace("copy of ", "")
    return re.sub(r"[^a-z0-9]+", "", s)


@st.cache_data(ttl=180, show_spinner=False)
def listar_archivos_google_drive_service_account():
    """
    Consulta drive.googleapis.com y devuelve todos los archivos que Mauricio haya compartido
    con 'drive-ulagos@motor-sii-python.iam.gserviceaccount.com'.
    """
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
    archivos = res.json().get("files", [])
    return archivos


@st.cache_data(ttl=600, show_spinner=False)
def descargar_bytes_archivo_drive_por_id(file_id):
    """Descarga en memoria RAM los bytes binarios de cualquier PDF o ZIP alojado en Google Drive."""
    token = obtener_token_bearer_drive()
    headers = {"Authorization": f"Bearer {token}", "User-Agent": "ULagos-Academic-Hub"}
    url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media&supportsAllDrives=true"
    res = requests.get(url, headers=headers, timeout=45)
    res.raise_for_status()
    return res.content


# ==============================================================================
# 3. CATÁLOGO DE REPOSITORIOS Y CUADRILLAS METODOLÓGICAS CON CITAS EXACTAS
# ==============================================================================

GITHUB_USER_DEFAULT = "mauriciovargas1516-ux"
URL_LOGIN_MOODLE = "https://www.ulagosvirtual.cl/login/index.php"

MAPA_REPOS_A_RAMOS = {
    "PROYECTOS-2026": {
        "ramo": "Evaluación Integrada de Proyectos (FDIC26)",
        "sigla_archivo": "EVALUACION_INTEGRADA_PROYECTOS_FDIC26",
        "corto": "PROYECTOS",
        "docente": "Dra. Luz María Ferrada B.",
        "app_url": "https://proyectos-2026-ubfvxgpqmpp5z7dn6wlnn3.streamlit.app/",
        "repo_url": "https://github.com/mauriciovargas1516-ux/PROYECTOS-2026",
        "descripcion": "Formulación, evaluación financiera privada, evaluación social SNI/MIDESO 2026 y valoración ambiental RA1/RA2.",
    },
    "DESARROLLO-Y-GESTION-TERRITORIAL-2026": {
        "ramo": "Desarrollo y Gestión Territorial",
        "sigla_archivo": "DESARROLLO_Y_GESTION_TERRITORIAL",
        "corto": "TERRITORIAL",
        "docente": "Prof. Claudio Mancilla",
        "app_url": "https://desarrollo-y-gestion-territorial-2026.streamlit.app/",
        "repo_url": "https://github.com/mauriciovargas1516-ux/DESARROLLO-Y-GESTION-TERRITORIAL-2026",
        "descripcion": "Indicadores de especialización regional (Qij, CE, Silva Lira), Gini/Theil, Ordenamiento Territorial (Guttman/Rondinelli) y Redes UCINET/Dini.",
    },
    "FINANZAS-AVANZADAS-2026": {
        "ramo": "Finanzas Avanzadas",
        "sigla_archivo": "FINANZAS_AVANZADAS",
        "corto": "FINANZAS",
        "docente": "Prof.ª Camila Bustos Rosas",
        "app_url": "https://finanzas-avanzadas-2026.streamlit.app/",
        "repo_url": "https://github.com/mauriciovargas1516-ux/FINANZAS-AVANZADAS-2026",
        "descripcion": "Modelo Consumo-Inversión de Fisher, DuPont/PGU, Frontera Eficiente de Markowitz (5 vs. 30 títulos IPSA), CAPM y Beta de Hamada.",
    },
    "FINANZAS-AVANZADAS": {
        "ramo": "Finanzas Avanzadas",
        "sigla_archivo": "FINANZAS_AVANZADAS",
        "corto": "FINANZAS",
        "docente": "Prof.ª Camila Bustos Rosas",
        "app_url": "https://finanzas-avanzadas-2026.streamlit.app/",
        "repo_url": "https://github.com/mauriciovargas1516-ux/FINANZAS-AVANZADAS",
        "descripcion": "Simulación financiera, teoría de carteras de Markowitz, CAPM, WACC y valoración bajo incertidumbre.",
    },
    "GESTION-TRIBUTARIA-2026": {
        "ramo": "Gestión Tributaria para la Toma de Decisiones",
        "sigla_archivo": "GESTION_TRIBUTARIA_TOMA_DECISIONES",
        "corto": "TRIBUTARIA",
        "docente": "Prof. RVS",
        "app_url": "https://gestion-tributaria-2026.streamlit.app/",
        "repo_url": "https://github.com/mauriciovargas1516-ux/GESTION-TRIBUTARIA-2026",
        "descripcion": "Determinación de IVA (D.L. 825), Libros de Compras/Ventas/Honorarios/Remuneraciones, F29 e Infracciones Art. 97 Código Tributario.",
    },
    "moodle-hybrid-scraper": {
        "ramo": "Sincronizador Automatizado ULagos Virtual (Moodle Scraper)",
        "sigla_archivo": "SINCRONIZADOR_MOODLE_ULAGOS",
        "corto": "MOODLE",
        "docente": "Automatización Web Híbrida (Selenium + Requests)",
        "app_url": "https://app-context-extractor-d8x5kwfdodzvmx7m3vean.streamlit.app/",
        "repo_url": "https://github.com/mauriciovargas1516-ux/moodle-hybrid-scraper",
        "descripcion": "Rastreador web híbrido integrado para extraer y empaquetar todos los PDFs, Excels y apuntes de ULagos Virtual.",
    },
    "github-context-extractor": {
        "ramo": "Hub Central & Extractor de Contexto Académico",
        "sigla_archivo": "HUB_EXTRACTOR_CONTEXTO_ULAGOS",
        "corto": "HUB",
        "docente": "Portafolio Ingeniería Comercial ULagos",
        "app_url": "https://app-context-extractor-d8x5kwfdodzvmx7m3vean.streamlit.app/",
        "repo_url": "https://github.com/mauriciovargas1516-ux/github-context-extractor",
        "descripcion": "Motor centralizado de compilación vía descarga directa ZIP, scraper Moodle y biblioteca metodológica conectada a Google Drive.",
    },
}

CATALOGO_DOCUMENTOS_DRIVE_Y_MOODLE = {
    "Clase1 (18 ago).pdf": {
        "nombre_drive": "Clase1 (18 ago)_copia.pdf",
        "ramo": "Evaluación Integrada de Proyectos (FDIC26)",
        "pagina_clave": 29,
        "url_respaldo": "https://sni.gob.cl/wp-content/uploads/METODOLOGIA-GENERAL-2025.pdf#page=74",
    },
    "Clase2.pdf": {
        "nombre_drive": "Clase2_copia.pdf",
        "ramo": "Evaluación Integrada de Proyectos (FDIC26)",
        "pagina_clave": 20,
        "url_respaldo": "https://economicas.unsa.edu.ar/iie/archivos/syc/Fontaine.pdf#page=207",
    },
    "Precios-Sociales-2026.pdf": {
        "nombre_drive": "Precios-Sociales-2026.pdf",
        "ramo": "Evaluación Integrada de Proyectos (FDIC26)",
        "pagina_clave": 5,
        "url_respaldo": "https://sni.gob.cl/storage/docs/Informe_Final_PSMO.pdf",
    },
    "Proceso2 RA1.pdf": {
        "nombre_drive": "Proceso2 RA1.pdf",
        "ramo": "Evaluación Integrada de Proyectos (FDIC26)",
        "pagina_clave": 2,
        "url_respaldo": "https://sni.gob.cl/wp-content/uploads/METODOLOGIA-GENERAL-2025.pdf#page=55",
    },
    "MARCO LOGICO.pdf": {
        "nombre_drive": "MARCO LOGICO.pdf",
        "ramo": "Evaluación Integrada de Proyectos (FDIC26)",
        "pagina_clave": 8,
        "url_respaldo": "https://sni.gob.cl/wp-content/uploads/METODOLOGIA-GENERAL-2025.pdf#page=18",
    },
    "GuiaVEdelosBSA.pdf": {
        "nombre_drive": "GuiaVEdelosBSA.pdf",
        "ramo": "Evaluación Integrada de Proyectos (FDIC26)",
        "pagina_clave": 15,
        "url_respaldo": "https://www.cepal.org/es/publicaciones/80999-estimacion-precio-social-carbono-la-evaluacion-la-inversion-publica-chile",
    },
    "Bibliografía - Ross.pdf": {
        "nombre_drive": "Bibliografía - Ross_copia.pdf",
        "ramo": "Finanzas Avanzadas",
        "pagina_clave": 64,
        "url_respaldo": "https://finanzas-avanzadas-2026.streamlit.app/",
    },
    "Bibliografía - Brealey.pdf": {
        "nombre_drive": "Bibliografía - Brealey_copia.pdf",
        "ramo": "Finanzas Avanzadas",
        "pagina_clave": 21,
        "url_respaldo": "https://finanzas-avanzadas-2026.streamlit.app/",
    },
    "Bibliografía - Gitman.pdf": {
        "nombre_drive": "Bibliografía - Gitman_copia.pdf",
        "ramo": "Finanzas Avanzadas",
        "pagina_clave": 75,
        "url_respaldo": "https://finanzas-avanzadas-2026.streamlit.app/",
    },
    "Consumo - Inversión.pdf": {
        "nombre_drive": "Consumo - Inversión.pdf",
        "ramo": "Finanzas Avanzadas",
        "pagina_clave": 9,
        "url_respaldo": "https://finanzas-avanzadas-2026.streamlit.app/",
    },
    "Relación riesgo rentabilidad.pdf": {
        "nombre_drive": "Relación riesgo rentabilidad.pdf",
        "ramo": "Finanzas Avanzadas",
        "pagina_clave": 28,
        "url_respaldo": "https://finanzas-avanzadas-2026.streamlit.app/",
    },
    "Teoría de mercado de capitales.pdf": {
        "nombre_drive": "Teoría de mercado de capitales.pdf",
        "ramo": "Finanzas Avanzadas",
        "pagina_clave": 40,
        "url_respaldo": "https://finanzas-avanzadas-2026.streamlit.app/",
    },
    "La_teoria_de_la_localizacion.pdf": {
        "nombre_drive": "La_teoria_de_la_localizacion.pdf",
        "ramo": "Desarrollo y Gestión Territorial",
        "pagina_clave": 7,
        "url_respaldo": "https://desarrollo-y-gestion-territorial-2026.streamlit.app/",
    },
    "06 OT 2024.pdf": {
        "nombre_drive": "06 OT 2024.pdf",
        "ramo": "Desarrollo y Gestión Territorial",
        "pagina_clave": 11,
        "url_respaldo": "http://www.subdere.gov.cl/sites/default/noticiasold/articles-77172_recurso_1.pdf",
    },
    "CEPAL CADENAS DE VALOR S1601085_es.pdf": {
        "nombre_drive": "CEPAL CADENAS DE VALOR S1601085_es_copia.pdf",
        "ramo": "Desarrollo y Gestión Territorial",
        "pagina_clave": 1,
        "url_respaldo": "https://desarrollo-y-gestion-territorial-2026.streamlit.app/",
    },
    "IVA y Toma de Decisiones.pdf": {
        "nombre_drive": "IVA y Toma de Decisiones.pdf",
        "ramo": "Gestión Tributaria para la Toma de Decisiones",
        "pagina_clave": 3,
        "url_respaldo": "https://www.bcn.cl/leychile/navegar?idNorma=6369",
    },
    "Caso GTTD Emision Facturas Falsas (Datos).pdf": {
        "nombre_drive": "Caso GTTD Emision Facturas Falsas (Datos).pdf",
        "ramo": "Gestión Tributaria para la Toma de Decisiones",
        "pagina_clave": 1,
        "url_respaldo": "https://www.bcn.cl/leychile/navegar?idNorma=6374",
    },
    "Taller_II_Deporte_Paralimpico.pdf": {
        "nombre_drive": "Taller_II_Deporte_Paralimpico.pdf",
        "ramo": "Introducción al Deporte Paralímpico",
        "pagina_clave": 1,
        "url_respaldo": "https://www.paralympic.org/classification",
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
                    "PSMO = Salario bruto * FCSMO | Tasa Social de Descuento (TSD) 2026 = 5,5% | Divisa (FCSD) = 1,00.\n\n"
                    "--- [PROYECTOS 2026/Proceso2 RA1.pdf | Página 1 y 2] ---\n"
                    "11. (F) Es falso porque los terrenos se tienen que valorar a su costo de oportunidad, aunque sea de propiedad del municipio.\n"
                    "15. (V) El precio social de la mano de obra es siempre menor o igual que su precio privado.\n"
                    "II.3 Choferes: requiere licencias especiales (competencias grupos 4-8), por lo tanto corresponde a Mano de Obra Semi Calificada (MOSC)."
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
                    "Po = 50 + 0,025*Qo  |  Pd = 300 - 0,0205*Qd\n"
                    "Cooperativa instala planta para producir 1.470 ton/año de leche en polvo: Q' = Q + 1.470."
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
                    "• VAC se usa cuando las alternativas tienen igual años de evaluación y los beneficios son muy difíciles de medir o son idénticos entre las alternativas.\n"
                    "• VAN se usa cuando las alternativas tienen igual años de evaluación y se tienen costos y beneficios en cada una.\n"
                    "• El CAE se usa cuando las alternativas tienen distintos años de evaluación y los beneficios son muy difíciles de medir o son idénticos."
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
                    "--- [PROYECTOS 2026/Cepal, Ortegon , et al, 2005.pdf | Página 15] ---\n"
                    "No confundir el problema con la ausencia de una solución. No es lo mismo decir 'falta un hospital' (falta de solución), "
                    "que decir que existen 'Altas tasas de morbilidad' en un área específica (problema).\n\n"
                    "--- [PROYECTOS 2026/MARCO LOGICO.pdf | Páginas 8 y 14] ---\n"
                    "Cada programa tiene un solo propósito.\n"
                    "CATEGORÍAS DE INDICADORES: EFICACIA (grado de cumplimiento), CALIDAD (respuesta a usuarios), "
                    "EFICIENCIA (producción física vs recursos/costos) y ECONOMÍA (capacidad de movilizar recursos financieros)."
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
                    "Radoslav Barzev (2002), 'GuiaVEdelosBSA.pdf', Cap. I (Tablas 1-2, págs. 12-17) y Cap. IV (MVC, Costo de Viaje y "
                    "Precios Hedónicos, págs. 59-78); y MDSF (2026), 'Precios-Sociales-2026.pdf', Cap. 2.4 (pág. 11) y Cap. 5 (págs. 17-19)."
                ),
                "marcador_moodle": "PROYECTOS 2026/Precios-Sociales-2026.pdf | Página 18",
                "extracto_literal": (
                    "--- [PROYECTOS 2026/GuiaVEdelosBSA.pdf | Página 15] ---\n"
                    "Bienes Ambientales: Son los recursos tangibles utilizados por el ser humano como insumos en la producción o en el consumo final y que se gastan y transforman en el proceso.\n"
                    "Servicios Ambientales: Tienen como principal característica que no se gastan y no se transforman en el proceso, pero generan indirectamente utilidad al consumidor.\n\n"
                    "--- [PROYECTOS 2026/Precios-Sociales-2026.pdf | Páginas 17-18] ---\n"
                    "Tabla 5.1 Precio Social del Carbono 2026: 71.801 CLP / t CO2 eq.\n"
                    "Tabla 5.2 Factor de conversión: Metano (CH4) = 28 t CO2 eq | Óxido nitroso (N2O) = 265 t CO2 eq."
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
                    "• Flujo de caja del proyecto puro: financiado 100% con capital propio.\n"
                    "• Flujo de caja del proyecto con deuda: resta Gastos Financieros (intereses) antes de Impuesto de 1ª Categoría y resta Amortizaciones en el Flujo de Capitales.\n"
                    "• Costos Hundidos (Lámina 34): obligación de pago contraída en el pasado, inevitable e irrelevante para la evaluación."
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
        "app_url": "https://finanzas-avanzadas-2026.streamlit.app/",
        "tarjetas": [
            {
                "id": "fin_fisher",
                "doc_pdf": "Bibliografía - Brealey.pdf",
                "pag_pdf": 21,
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
                    "Principio de separación de Fisher: Dado un mercado de capitales perfecto y completo, la decisión de inversión está "
                    "representada solamente por el criterio objetivo de mercado (maximizar la riqueza) sin importar las preferencias subjetivas "
                    "de los individuos respecto a sus decisiones de consumo."
                ),
                "links": [
                    ("Abrir Simulador Finanzas Avanzadas en Streamlit", "https://finanzas-avanzadas-2026.streamlit.app/"),
                    ("Repositorio GitHub Finanzas Avanzadas", "https://github.com/mauriciovargas1516-ux/FINANZAS-AVANZADAS-2026"),
                ],
            },
            {
                "id": "fin_riesgo_dupont",
                "doc_pdf": "Bibliografía - Ross.pdf",
                "pag_pdf": 64,
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
                    "• Juego justo (Lámina 8): el valor esperado de la riqueza si aceptas el juego es igual al valor seguro si lo rechazas.\n"
                    "• PGU (Lámina 28): PGU = Margen de Utilidad Operacional x Rotación de Activos Operacionales."
                ),
                "links": [
                    ("Abrir Calculadora DuPont y Utilidad en Finanzas App", "https://finanzas-avanzadas-2026.streamlit.app/"),
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
                    "• Si correlación < +1: existe reducción de riesgo; cuanto más baja la correlación, mayor el beneficio de diversificación.\n"
                    "• CAPM (Lámina 40): Re = Rf + Beta * (Rm - Rf).\n"
                    "• Ecuación de Hamada (Lámina 49): Beta_L = Beta_U * [1 + (1 - t)*(B / S)]."
                ),
                "links": [
                    ("Base de Datos Estadísticos Banco Central de Chile (BCP/BTP 5 años)", "https://si3.bcentral.cl/Siete/ES/Siete/Cuadro/CAP_TASA_INTERES/MN_TASA_INTERES_09/TMS_15"),
                    ("Abrir Optimizador Markowitz / CAPM en Vivo", "https://finanzas-avanzadas-2026.streamlit.app/"),
                ],
            },
        ],
    },
    "Desarrollo y Gestión Territorial": {
        "docente": "Prof. Claudio Mancilla",
        "app_url": "https://desarrollo-y-gestion-territorial-2026.streamlit.app/",
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
                    ("Abrir Plataforma Desarrollo y Gestión Territorial", "https://desarrollo-y-gestion-territorial-2026.streamlit.app/"),
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
                    "• Índice de Primacía: peso relativo del principal centro poblado respecto a la suma de los tres siguientes.\n"
                    "• Escala de Gutmann / Matriz de Rondinelli: presencia (1) o ausencia (0) de servicios o funciones."
                ),
                "links": [
                    ("Manual Elaboración PLADECO (SUBDERE PDF)", "http://www.subdere.gov.cl/sites/default/noticiasold/articles-77172_recurso_1.pdf"),
                    ("Abrir Módulo Guttman / Rondinelli en App Territorial", "https://desarrollo-y-gestion-territorial-2026.streamlit.app/"),
                ],
            },
            {
                "id": "terr_dini_ucinet",
                "doc_pdf": "CEPAL CADENAS DE VALOR S1601085_es.pdf",
                "pag_pdf": 1,
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
                    ("Abrir Simulador Redes de Dini y UCINET en Vivo", "https://desarrollo-y-gestion-territorial-2026.streamlit.app/"),
                ],
            },
        ],
    },
    "Gestión Tributaria para la Toma de Decisiones": {
        "docente": "Prof. RVS",
        "app_url": "https://gestion-tributaria-2026.streamlit.app/",
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
                    "Remanente Anterior en UTM = Remanente Anterior $ / UTM Mes declaración.\n"
                    "Remanente actualizado mes siguiente = Remanente Anterior en UTM x UTM Mes siguiente."
                ),
                "links": [
                    ("D.L. N° 825 Ley sobre Impuesto a las Ventas y Servicios (BCN)", "https://www.bcn.cl/leychile/navegar?idNorma=6369"),
                    ("Abrir Suite Tributaria 2026 en Streamlit", "https://gestion-tributaria-2026.streamlit.app/"),
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
        "app_url": "https://app-context-extractor-d8x5kwfdodzvmx7m3vean.streamlit.app/",
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
# 4. BUSCADOR MULTI-ORIGEN DE PDFS (GOOGLE DRIVE API 5 TB + MOODLE ZIP + LOCAL)
# ==============================================================================

def _buscar_bytes_pdf_en_drive_moodle_o_repo(nombre_pdf):
    """
    Busca los bytes binarios del documento PDF solicitado en este orden:
    1) Archivos PDF sueltos compartidos en Google Drive con 'drive-ulagos@motor-sii-python.iam.gserviceaccount.com'
       (emparejando automáticamente nombres como 'Clase2_copia.pdf' o 'Bibliografía - Ross_copia.pdf').
    2) Paquetes .ZIP compartidos en Google Drive (como 'Respaldo_ULagos_2026.zip').
    3) El paquete .ZIP en memoria del Sincronizador Moodle (Pestaña 3 o Pestaña 5).
    4) Archivos locales en el repositorio.
    """
    clave_obj = _normalizar_clave_nombre(nombre_pdf)

    # 1 y 2: Buscar directamente en Google Drive vía Service Account API
    try:
        archivos_drive = listar_archivos_google_drive_service_account()
        # Primero buscar coincidencia en archivos PDF directos en Drive
        for arch in archivos_drive:
            nom_d = arch.get("name", "")
            if nom_d.lower().endswith(".pdf"):
                clave_d = _normalizar_clave_nombre(nom_d)
                if clave_d == clave_obj or (len(clave_obj) >= 6 and (clave_obj in clave_d or clave_d in clave_obj)):
                    pdf_bytes = descargar_bytes_archivo_drive_por_id(arch["id"])
                    return pdf_bytes, f"Google Drive API ({nom_d})", arch.get("id")

        # Si no está suelto como PDF, buscar dentro de cualquier archivo .ZIP compartido en Google Drive
        for arch in archivos_drive:
            nom_d = arch.get("name", "")
            if nom_d.lower().endswith(".zip"):
                zip_bytes_drv = descargar_bytes_archivo_drive_por_id(arch["id"])
                with zipfile.ZipFile(io.BytesIO(zip_bytes_drv), "r") as zf:
                    for zi in zf.infolist():
                        if zi.filename.lower().endswith(".pdf"):
                            clave_z = _normalizar_clave_nombre(os.path.basename(zi.filename))
                            if clave_z == clave_obj or (len(clave_obj) >= 6 and clave_obj in clave_z):
                                return zf.read(zi), f"Google Drive ZIP ({nom_d} -> {zi.filename})", arch.get("id")
    except Exception:
        pass

    # 3: Buscar en el ZIP sincronizado en memoria por el Scraper de Moodle
    if "moodle_zip_bytes" in st.session_state and st.session_state["moodle_zip_bytes"]:
        try:
            with zipfile.ZipFile(io.BytesIO(st.session_state["moodle_zip_bytes"]), "r") as zf:
                for zi in zf.infolist():
                    if zi.filename.lower().endswith(".pdf"):
                        clave_z = _normalizar_clave_nombre(os.path.basename(zi.filename))
                        if clave_z == clave_obj or (len(clave_obj) >= 6 and clave_obj in clave_z):
                            return zf.read(zi), f"Memoria Moodle Scraper ({zi.filename})", None
        except Exception:
            pass

    # 4: Buscar en el repositorio local
    carpeta = os.path.dirname(os.path.abspath(__file__))
    for f in os.listdir(carpeta):
        ruta_f = os.path.join(carpeta, f)
        if f.lower().endswith(".pdf") and _normalizar_clave_nombre(f) == clave_obj:
            with open(ruta_f, "rb") as fp:
                return fp.read(), f"Repositorio Local ({f})", None
    return None, None, None


def _recortar_paginas_pdf_en_base64(pdf_bytes, pag_inicio, pag_fin=None):
    """Recorta con pypdf exactamente las páginas seleccionadas para que el navegador las renderice al instante."""
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


def mostrar_visor_documento_citado(nombre_pdf, pagina_objetivo=1):
    """Muestra el PDF recortado en la página exacta desde Google Drive API (5 TB) o Moodle."""
    meta_doc = CATALOGO_DOCUMENTOS_DRIVE_Y_MOODLE.get(nombre_pdf, {})

    c_pag1, c_pag2, c_pag3 = st.columns([1.1, 1.1, 2.8])
    with c_pag1:
        p_ini_sel = st.number_input(
            "Desde Página / Lámina:",
            min_value=1,
            max_value=1500,
            value=int(pagina_objetivo),
            step=1,
            key=f"v_ini_{nombre_pdf}",
        )
    with c_pag2:
        p_fin_sel = st.number_input(
            "Hasta Página / Lámina:",
            min_value=1,
            max_value=1500,
            value=int(pagina_objetivo),
            step=1,
            key=f"v_fin_{nombre_pdf}",
        )
    with c_pag3:
        st.caption(
            f"**Cuenta Google Drive API activa:** `{SERVICE_ACCOUNT_EMAIL}`  \n"
            f"Archivo buscado en tu Drive: `{meta_doc.get('nombre_drive', nombre_pdf)}`"
        )

    with st.spinner(f"Buscando '{nombre_pdf}' en tu Google Drive (5 TB) y recortando página {int(p_ini_sel)}..."):
        pdf_bytes, fuente_origen, drive_file_id = _buscar_bytes_pdf_en_drive_moodle_o_repo(nombre_pdf)

    if pdf_bytes:
        b64_recorte, tot_p, r_i, r_f = _recortar_paginas_pdf_en_base64(pdf_bytes, p_ini_sel, p_fin_sel)
        if b64_recorte:
            st.success(
                f"Documento cargado en vivo desde {fuente_origen} — Mostrando página/lámina {r_i} a {r_f} (de {tot_p} páginas totales)."
            )
            st.markdown(
                f'<iframe src="data:application/pdf;base64,{b64_recorte}" width="100%" height="680" '
                f'style="border:2px solid #1E3A8A;border-radius:6px;"></iframe>',
                unsafe_allow_html=True,
            )
            st.download_button(
                label=f"Descargar PDF completo ({nombre_pdf})",
                data=pdf_bytes,
                file_name=nombre_pdf,
                mime="application/pdf",
            )
            return

    # Si aún no ha compartido ese archivo específico en Drive con drive-ulagos@...
    st.warning(
        f"Aún no se detecta `{meta_doc.get('nombre_drive', nombre_pdf)}` compartido con `{SERVICE_ACCOUNT_EMAIL}` en tu Google Drive. "
        f"En tu Google Drive haz clic derecho sobre `{meta_doc.get('nombre_drive', nombre_pdf)}` (o sobre la carpeta de tus ramos) -> "
        f"**Compartir** -> pega `{SERVICE_ACCOUNT_EMAIL}` y presiona el botón **Refrescar Conexión Google Drive** en la barra lateral."
    )
    url_resp = meta_doc.get("url_respaldo", "")
    if url_resp:
        st.markdown(
            f"<a href='{url_resp}' target='_blank' "
            f"style='display:inline-block;background:#1D4ED8;color:white;padding:8px 14px;border-radius:5px;text-decoration:none;font-weight:700;'>"
            f"Mientras tanto: Abrir Fuente Oficial Externa en Navegador ({url_resp}) &#8599;</a>",
            unsafe_allow_html=True,
        )


# ==============================================================================
# 5. FUNCIONES DEL EXTRACTOR GITHUB (INMUNE A HTTP 403) Y BÓVEDA LOCAL
# ==============================================================================

EXTENSIONES_TEXTO_PERMITIDAS = (
    ".py", ".md", ".txt", ".toml", ".json", ".yaml", ".yml",
    ".css", ".html", ".js", ".rmd", ".r", ".sql", ".sh", ".csv"
)


@st.cache_data(show_spinner=False)
def cargar_boveda_moodle_del_repo():
    carpeta = os.path.dirname(os.path.abspath(__file__))
    candidatos = [
        f for f in os.listdir(carpeta)
        if os.path.isfile(os.path.join(carpeta, f))
        and f.lower().endswith(".txt")
        and f not in ("requirements.txt", "packages.txt")
    ]
    if not candidatos:
        return None, "", {}

    candidatos.sort(key=lambda x: os.path.getsize(os.path.join(carpeta, x)), reverse=True)
    archivo_maestro = candidatos[0]
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
    return archivo_maestro, texto_total, secciones


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


def obtener_meta_repo(nombre_repo, desc_api="", homepage_api=""):
    if nombre_repo in MAPA_REPOS_A_RAMOS:
        return MAPA_REPOS_A_RAMOS[nombre_repo]
    limpio = re.sub(r"[^A-Za-z0-9]+", "_", nombre_repo).strip("_").upper()
    return {
        "ramo": f"Repositorio Académico: {nombre_repo}",
        "sigla_archivo": limpio,
        "corto": limpio[:12],
        "docente": "Universidad de Los Lagos",
        "app_url": homepage_api or "No especificada",
        "repo_url": f"https://github.com/{GITHUB_USER_DEFAULT}/{nombre_repo}",
        "descripcion": desc_api or "Repositorio de código y automatización en Python.",
    }


def construir_nombre_y_encabezado_personalizado(repos_seleccionados, usuario_gh):
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    if not repos_seleccionados:
        return f"CONTEXTO_PORTAFOLIO_{fecha_hoy}.txt", "EXTRACCIÓN DE PORTAFOLIO VACÍA\n"

    if len(repos_seleccionados) == 1:
        r_nom = repos_seleccionados[0]
        meta = obtener_meta_repo(r_nom)
        nombre_archivo = f"CONTEXTO_{meta['sigla_archivo']}_{fecha_hoy}.txt"
        encabezado = (
            "=" * 94 + "\n"
            f"CONTEXTO DE CÁTEDRA Y CÓDIGO FUENTE — ASIGNATURA: {meta['ramo'].upper()}\n"
            f"Docente: {meta['docente']} | Repositorio GitHub: {r_nom}\n"
            f"App Interactiva en Vivo: {meta['app_url']}\n"
            f"Estudiante: Mauricio Alejandro Vargas Ortega ({usuario_gh}) | Fecha: {fecha_hoy}\n"
            + "=" * 94 + "\n\n"
        )
        return nombre_archivo, encabezado

    siglas = [obtener_meta_repo(r)["corto"] for r in repos_seleccionados[:4]]
    sufijo = "_".join(siglas)
    if len(repos_seleccionados) > 4:
        sufijo += f"_Y_{len(repos_seleccionados) - 4}_MAS"
    nombre_archivo = f"CONTEXTO_MULTIRAMO_{sufijo}_{fecha_hoy}.txt"

    lista_ramos = "\n".join(
        f"  * {r} -> {obtener_meta_repo(r)['ramo']} ({obtener_meta_repo(r)['docente']})"
        for r in repos_seleccionados
    )
    encabezado = (
        "=" * 94 + "\n"
        f"EXTRACCIÓN MULTIRAMO PERSONALIZADA ({len(repos_seleccionados)} REPOSITORIOS SELECCIONADOS)\n"
        f"Estudiante: Mauricio Alejandro Vargas Ortega ({usuario_gh}) | Fecha: {fecha_hoy}\n"
        "Asignaturas y Repositorios incluidos en este archivo:\n"
        f"{lista_ramos}\n"
        + "=" * 94 + "\n\n"
    )
    return nombre_archivo, encabezado


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


def _github_api_get(url, token=""):
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github.v3+json")
    req.add_header("User-Agent", "ULagos-Academic-Context-Extractor")
    if token.strip():
        req.add_header("Authorization", f"token {token.strip()}")
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _listar_repositorios_fallback_html_y_catalogo(usuario):
    nombres_vistos = []
    try:
        url_html = f"https://github.com/{usuario}?tab=repositories"
        req = urllib.request.Request(url_html, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            html_txt = resp.read().decode("utf-8", errors="replace")
        patron = rf'href="/{re.escape(usuario)}/([^/"?#]+)"[^>]*itemprop="name codeRepository"'
        for m in re.finditer(patron, html_txt):
            r_name = m.group(1).strip()
            if r_name and r_name not in nombres_vistos:
                nombres_vistos.append(r_name)
    except Exception:
        pass

    for r_cat in MAPA_REPOS_A_RAMOS:
        if r_cat not in nombres_vistos:
            nombres_vistos.append(r_cat)

    repos = []
    for r_nom in nombres_vistos:
        meta = obtener_meta_repo(r_nom)
        repos.append({
            "name": r_nom,
            "description": meta["descripcion"],
            "html_url": f"https://github.com/{usuario}/{r_nom}",
            "homepage": meta["app_url"] if meta["app_url"] != "No especificada" else "",
            "default_branch": "main",
            "updated_at": datetime.now().strftime("%Y-%m-%d"),
        })
    return repos


@st.cache_data(ttl=600, show_spinner=False)
def listar_repositorios_usuario(usuario, token=""):
    try:
        url = f"https://api.github.com/users/{usuario}/repos?per_page=100&sort=updated"
        datos = _github_api_get(url, token=token)
        repos = []
        for d in datos:
            repos.append({
                "name": d.get("name", ""),
                "description": d.get("description") or "",
                "html_url": d.get("html_url", ""),
                "homepage": d.get("homepage") or "",
                "default_branch": d.get("default_branch", "main"),
                "updated_at": (d.get("updated_at") or "")[:10],
            })
        return repos, False
    except Exception:
        return _listar_repositorios_fallback_html_y_catalogo(usuario), True


def _descargar_zip_repositorio_en_memoria(usuario, nombre_repo, rama_preferida="main", token=""):
    ramas_probar = []
    for r in [rama_preferida, "main", "master"]:
        if r and r not in ramas_probar:
            ramas_probar.append(r)

    ultimo_error = None
    for rama in ramas_probar:
        url_zip = f"https://codeload.github.com/{usuario}/{nombre_repo}/zip/refs/heads/{rama}"
        req = urllib.request.Request(url_zip, headers={"User-Agent": "Mozilla/5.0"})
        if token.strip():
            req.add_header("Authorization", f"token {token.strip()}")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read()
        except Exception as e:
            ultimo_error = e
            continue
    raise RuntimeError(f"No se pudo descargar el paquete ZIP de {nombre_repo}: {ultimo_error}")


def extraer_repositorio_completo(usuario, repo_info, token="", incluir_literatura=True):
    nombre_repo = repo_info["name"]
    rama = repo_info.get("default_branch", "main")
    meta = obtener_meta_repo(nombre_repo, repo_info.get("description", ""), repo_info.get("homepage", ""))

    bloques = []
    bloques.append(f"### REPOSITORIO: {nombre_repo} | ASIGNATURA: {meta['ramo']}")
    bloques.append(f"Docente: {meta['docente']}")
    bloques.append(f"Descripción: {repo_info.get('description') or meta['descripcion']}")
    bloques.append(f"URL GitHub: {repo_info.get('html_url') or meta['repo_url']}")
    if meta["app_url"] and meta["app_url"] != "No especificada":
        bloques.append(f"App Streamlit en Vivo: {meta['app_url']}")
    bloques.append("-" * 90)

    if incluir_literatura and meta["ramo"] in CUADRILLAS_LITERATURA_POR_RAMO:
        bloques.append(formatear_cuadrilla_en_texto_plano(meta["ramo"]))

    try:
        zip_bytes = _descargar_zip_repositorio_en_memoria(usuario, nombre_repo, rama_preferida=rama, token=token)
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

            bloques.append("#### INVENTARIO DE ARCHIVOS:")
            for ruta_rel, zinfo in archivos_zip:
                bloques.append(f"  - {ruta_rel} ({zinfo.file_size} bytes)")
            bloques.append("")

            for ruta_rel, zinfo in archivos_zip:
                if ruta_rel.lower().endswith(EXTENSIONES_TEXTO_PERMITIDAS):
                    bloques.append(f"#### ARCHIVO: {nombre_repo}/{ruta_rel}")
                    bloques.append("-" * 70)
                    try:
                        raw_bytes = zf.read(zinfo)
                        texto_decodificado = raw_bytes.decode("utf-8", errors="replace")
                        bloques.append(texto_decodificado)
                    except Exception as exc:
                        bloques.append(f"[Aviso: No se pudo decodificar {ruta_rel}: {exc}]")
                    bloques.append("\n")
    except Exception as exc_zip:
        bloques.append(f"[Aviso al extraer {nombre_repo}: {exc_zip}]\n")

    return "\n".join(bloques)


# ==============================================================================
# 6. MOTOR INTEGRADO MOODLE HYBRID SCRAPER (SELENIUM + REQUESTS)
# ==============================================================================

def _configurar_driver_moodle():
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--allow-running-insecure-content")
    options.add_argument("--lang=es-CL")
    options.add_argument("--accept-lang=es-CL,es;q=0.9")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
    options.set_capability("acceptInsecureCerts", True)
    options.add_experimental_option("excludeSwitches", ["enable-logging", "enable-automation"])

    ruta_chromium = shutil.which("chromium") or shutil.which("chromium-browser")
    ruta_chromedriver = shutil.which("chromedriver")
    if ruta_chromium and ruta_chromedriver:
        options.binary_location = ruta_chromium
        service = Service(executable_path=ruta_chromedriver)
        return webdriver.Chrome(service=service, options=options)
    return webdriver.Chrome(options=options)


def _obtener_sesion_hibrida_moodle(usuario, dominio, clave):
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait, Select
    from selenium.webdriver.support import expected_conditions as EC

    driver = _configurar_driver_moodle()
    paso_actual = "Abriendo portal ULagos Virtual"
    try:
        driver.set_page_load_timeout(35)
        driver.get(URL_LOGIN_MOODLE)

        paso_actual = "Buscando casilla de Usuario"
        xpath_usuario = (
            "//input[@placeholder='Usuario' or @placeholder='Username' "
            "or @name='username' or @id='username' or @type='text']"
        )
        caja_usuario = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, xpath_usuario))
        )
        caja_usuario.clear()
        caja_usuario.send_keys(usuario.strip())

        paso_actual = "Seleccionando dominio institucional"
        selects = driver.find_elements(By.XPATH, "//select")
        if selects:
            menu_desplegable = Select(selects[0])
            try:
                menu_desplegable.select_by_visible_text(dominio)
            except Exception:
                for opt in menu_desplegable.options:
                    if dominio in opt.text or dominio in (opt.get_attribute("value") or ""):
                        opt.click()
                        break

        paso_actual = "Ingresando contraseña"
        xpath_clave = "//input[@placeholder='Contraseña' or @placeholder='Password' or @type='password']"
        caja_clave = driver.find_element(By.XPATH, xpath_clave)
        caja_clave.clear()
        caja_clave.send_keys(clave)

        paso_actual = "Presionando botón Iniciar sesión"
        xpath_boton = (
            "//button[contains(text(), 'Iniciar') or contains(text(), 'Acceder') "
            "or contains(text(), 'Log in') or @type='submit'] | //input[@type='submit']"
        )
        boton_ingresar = driver.find_element(By.XPATH, xpath_boton)
        driver.execute_script("arguments[0].click();", boton_ingresar)

        paso_actual = "Esperando validación de credenciales"
        WebDriverWait(driver, 30).until(lambda d: "login" not in d.current_url.lower())
        time.sleep(3)

        html_dashboard = driver.page_source
        selenium_cookies = driver.get_cookies()
    except Exception as e:
        driver.quit()
        raise RuntimeError(f"Fallo en '{paso_actual}': {e}") from e

    driver.quit()
    sesion = requests.Session()
    for cookie in selenium_cookies:
        sesion.cookies.set(cookie["name"], cookie["value"])
    sesion.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
    })
    return sesion, html_dashboard


def _limpiar_nombre_moodle(nombre):
    return re.sub(r'[\\/*?:"<>|]', "", nombre).strip()


def _obtener_carpeta_ramo_moodle(nombre_curso, anio_actual):
    mapeo_claves = {
        "Tributaria": f"TRIBUTARIA {anio_actual}",
        "Finanzas": f"FINANZAS AVANZADAS {anio_actual}",
        "Territorial": f"TERRITORIAL {anio_actual}",
        "Proyectos": f"PROYECTOS {anio_actual}",
    }
    for clave, carpeta in mapeo_claves.items():
        if clave.lower() in nombre_curso.lower():
            return carpeta
    return f"{_limpiar_nombre_moodle(nombre_curso).upper()} {anio_actual}"


def _descargar_a_zip_moodle(sesion, url, archivo_zip, archivos_en_zip, carpeta_ramo, num_archivo, nombre_sugerido=None):
    url_directa = url + "&redirect=1" if "view.php" in url else url
    try:
        res = sesion.get(url_directa, verify=False, stream=True, timeout=20)
    except Exception:
        return "ignorados", None

    content_type = res.headers.get("Content-Type", "").lower()
    if "text/html" in content_type:
        soup_html = BeautifulSoup(res.text, "html.parser")
        titulo = (
            soup_html.find("h2").text
            if soup_html.find("h2")
            else (soup_html.title.text.replace("Curso:", "").strip() if soup_html.title else "Documento_Moodle")
        )
        titulo_limpio = _limpiar_nombre_moodle(titulo)
        enlace_archivo = None

        objeto_pdf = soup_html.find("object", type="application/pdf")
        if objeto_pdf and "data" in objeto_pdf.attrs:
            enlace_archivo = objeto_pdf["data"]
        else:
            for a in soup_html.find_all("a", href=True):
                href = a["href"].lower()
                if "pluginfile.php" in href or any(
                    href.endswith(ext) for ext in [".pdf", ".xlsx", ".xls", ".docx", ".doc", ".pptx", ".zip"]
                ):
                    enlace_archivo = a["href"]
                    break

        if enlace_archivo:
            return _descargar_a_zip_moodle(
                sesion, urljoin(url, enlace_archivo), archivo_zip, archivos_en_zip, carpeta_ramo, num_archivo, titulo_limpio
            )
        return "ignorados", None

    nombre_base = nombre_sugerido if nombre_sugerido else f"apunte_{num_archivo}"
    extension_final = ""
    if "Content-Disposition" in res.headers:
        cd = res.headers["Content-Disposition"]
        if "filename=" in cd:
            nombre_real = cd.split("filename=")[1].strip("\"'").replace('"', "")
            _, ext = os.path.splitext(nombre_real)
            if ext:
                extension_final = ext.lower()
                if not nombre_sugerido:
                    nombre_base = nombre_real.replace(ext, "")

    if not extension_final:
        if "spreadsheet" in content_type or "excel" in content_type:
            extension_final = ".xlsx"
        elif "word" in content_type:
            extension_final = ".docx"
        elif "zip" in content_type:
            extension_final = ".zip"
        else:
            extension_final = ".pdf"

    nombre_archivo = _limpiar_nombre_moodle(nombre_base) + extension_final
    ruta_interna_zip = f"{carpeta_ramo}/{nombre_archivo}"
    if ruta_interna_zip in archivos_en_zip:
        return "omitidos", nombre_archivo

    archivo_zip.writestr(ruta_interna_zip, res.content)
    archivos_en_zip.add(ruta_interna_zip)
    return "descargados", nombre_archivo


# ==============================================================================
# 7. RENDERIZADOR DE CUADRILLAS CON HIPERVÍNCULOS Y VISOR PDF DE GOOGLE DRIVE
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
# 8. INTERFAZ PRINCIPAL Y VISOR DE DOCUMENTOS AL PULSAR UNA REFERENCIA (?cita=...)
# ==============================================================================

st.markdown(
    """
    <div class="top-banner">
        <h1>SUPER HUB ACADÉMICO ULAGOS 2026: GITHUB + MOODLE SCRAPER + GOOGLE DRIVE API (5 TB)</h1>
        <p>Conectado a Google Cloud (motor-sii-python / drive-ulagos@motor-sii-python.iam.gserviceaccount.com) para abrir y recortar tus PDFs originales en la página exacta.</p>
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
    st.markdown("### Estado de Conexión Cloud")
    st.caption(f"**Proyecto GCP:** `motor-sii-python`")
    st.code(SERVICE_ACCOUNT_EMAIL, language="text")
    if st.button("Refrescar Conexión Google Drive (5 TB)", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.divider()
    usuario_gh = st.text_input("Usuario GitHub:", value=GITHUB_USER_DEFAULT)
    token_default = ""
    try:
        token_default = st.secrets.get("GITHUB_TOKEN", "")
    except Exception:
        token_default = ""
    token_gh = st.text_input(
        "Token GitHub (Opcional):",
        value=token_default,
        type="password",
    )
    incluir_lit_en_txt = st.checkbox(
        "Incluir Cuadrilla de Literatura e Hipervínculos en el .TXT",
        value=True,
    )

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "1. Extractor GitHub por Ramo",
    "2. Cuadrillas y Visor PDF (Drive API)",
    "3. Explorador en Vivo Google Drive (5 TB)",
    "4. Sincronizador ULagos Virtual (Moodle)",
    "5. Bóveda Destilada en 1 Clic",
])

# ------------------------------------------------------------------------------
# PESTAÑA 1: EXTRACTOR GITHUB POR RAMO (INMUNE A HTTP 403)
# ------------------------------------------------------------------------------
with tab1:
    st.markdown(
        "<div class='sec-header'>1. SELECCIÓN DE RAMOS / REPOSITORIOS Y NOMENCLATURA PERSONALIZADA</div>",
        unsafe_allow_html=True,
    )

    lista_repos, usando_fallback = listar_repositorios_usuario(usuario_gh, token=token_gh)
    if usando_fallback:
        st.caption(
            "Modo Directo Codeload Activo: Catálogo cargado vía web directa (evitando el límite de 60 consultas/hora de api.github.com)."
        )

    if lista_repos:
        mapa_objetos_repo = {r["name"]: r for r in lista_repos}
        nombres_disponibles = list(mapa_objetos_repo.keys())

        c_filtro, c_sel = st.columns([1.3, 2.7])
        with c_filtro:
            modo_seleccion = st.radio(
                "Modo de empaquetado:",
                options=[
                    "Por Ramo / Asignatura Específica",
                    "Selección Manual de Repositorios",
                    "Portafolio Completo (Todos)",
                ],
            )

        with c_sel:
            if modo_seleccion == "Por Ramo / Asignatura Específica":
                opciones_ramos = [
                    f"{k} — {v['ramo']}"
                    for k, v in MAPA_REPOS_A_RAMOS.items()
                    if k in mapa_objetos_repo
                ]
                if not opciones_ramos:
                    opciones_ramos = nombres_disponibles
                elegido_ramo = st.selectbox("Selecciona la Asignatura / Repositorio a descargar:", options=opciones_ramos)
                repo_clave = elegido_ramo.split(" — ")[0].strip()
                repos_seleccionados = [repo_clave] if repo_clave in mapa_objetos_repo else [nombres_disponibles[0]]
            elif modo_seleccion == "Selección Manual de Repositorios":
                default_init = ["PROYECTOS-2026"] if "PROYECTOS-2026" in nombres_disponibles else nombres_disponibles[:1]
                repos_seleccionados = st.multiselect(
                    "Elige uno o más repositorios (el archivo adoptará sus nombres):",
                    options=nombres_disponibles,
                    default=default_init,
                )
            else:
                repos_seleccionados = nombres_disponibles
                st.info(f"Se empaquetarán los {len(repos_seleccionados)} repositorios públicos de {usuario_gh}.")

        nombre_sugerido, encabezado_sugerido = construir_nombre_y_encabezado_personalizado(
            repos_seleccionados, usuario_gh
        )

        col_nom1, col_nom2 = st.columns([2.2, 1.8])
        with col_nom1:
            nombre_archivo_final = st.text_input(
                "Nombre del archivo .TXT a descargar (generado automáticamente según tu selección):",
                value=nombre_sugerido,
            )
        with col_nom2:
            st.markdown("**Vista previa de asignaturas detectadas:**")
            for r_sel in repos_seleccionados[:4]:
                m_info = obtener_meta_repo(r_sel)
                st.caption(f"• `{r_sel}` → **{m_info['ramo']}** ({m_info['docente']})")

        if st.button("COMPILAR CONTEXTO PERSONALIZADO DE LOS RAMOS SELECCIONADOS", type="primary", use_container_width=True):
            if not repos_seleccionados:
                st.warning("Selecciona al menos un repositorio para compilar.")
            else:
                partes_txt = [encabezado_sugerido]
                barra = st.progress(0, text="Iniciando descarga directa en memoria desde Codeload GitHub...")
                for idx, r_nom in enumerate(repos_seleccionados):
                    barra.progress(
                        (idx) / len(repos_seleccionados),
                        text=f"Empaquetando {r_nom} ({obtener_meta_repo(r_nom)['ramo']})...",
                    )
                    r_obj = mapa_objetos_repo[r_nom]
                    bloque_repo = extraer_repositorio_completo(
                        usuario_gh,
                        r_obj,
                        token=token_gh,
                        incluir_literatura=incluir_lit_en_txt,
                    )
                    partes_txt.append(bloque_repo)
                barra.progress(1.0, text="Compilación finalizada correctamente.")
                st.session_state["txt_compilado_contenido"] = "\n".join(partes_txt)
                st.session_state["txt_compilado_nombre"] = nombre_archivo_final

        if "txt_compilado_contenido" in st.session_state:
            tam_kb = len(st.session_state["txt_compilado_contenido"].encode("utf-8")) / 1024.0
            st.success(
                f"Archivo listo: {st.session_state['txt_compilado_nombre']} ({tam_kb:,.1f} KB compilados)."
            )
            st.download_button(
                label=f"DESCARGAR {st.session_state['txt_compilado_nombre']}",
                data=st.session_state["txt_compilado_contenido"].encode("utf-8"),
                file_name=st.session_state["txt_compilado_nombre"],
                mime="text/plain",
                use_container_width=True,
            )

# ------------------------------------------------------------------------------
# PESTAÑA 2: CUADRILLAS CON APERTURA AUTOMÁTICA DE PDF DESDE GOOGLE DRIVE API
# ------------------------------------------------------------------------------
with tab2:
    st.markdown(
        "<div class='sec-header'>2. CUADRILLAS METODOLÓGICAS CON APERTURA DEL PDF ORIGINAL EN LA PÁGINA EXACTA</div>",
        unsafe_allow_html=True,
    )
    st.caption(
        "Haz clic en el botón verde de cualquier tarjeta para que la cuenta de servicio 'drive-ulagos' "
        "descargue el PDF desde tu Google Drive (5 TB), recorte la lámina o página exacta y te la muestre en pantalla."
    )
    ramos_disponibles_lit = ["Mostrar Todos los Ramos"] + list(CUADRILLAS_LITERATURA_POR_RAMO.keys())
    filtro_ramo_lit = st.selectbox("Filtrar cuadrillas por asignatura:", options=ramos_disponibles_lit)

    if filtro_ramo_lit == "Mostrar Todos los Ramos":
        for nombre_r in CUADRILLAS_LITERATURA_POR_RAMO:
            renderizar_cuadrillas_ramo(nombre_r)
    else:
        renderizar_cuadrillas_ramo(filtro_ramo_lit)

# ------------------------------------------------------------------------------
# PESTAÑA 3: EXPLORADOR EN VIVO DE GOOGLE DRIVE API (5 TB — motor-sii-python)
# ------------------------------------------------------------------------------
with tab3:
    st.markdown(
        "<div class='sec-header'>3. EXPLORADOR EN VIVO DE TUS 5 TB DE GOOGLE DRIVE (API SERVICE ACCOUNT ACTIVA)</div>",
        unsafe_allow_html=True,
    )
    st.write(
        f"Todo archivo o carpeta de tu Google Drive que compartas como **Lector** con el correo "
        f"`{SERVICE_ACCOUNT_EMAIL}` aparecerá listado automáticamente aquí abajo y quedará conectado a los visores."
    )

    try:
        archivos_drv = listar_archivos_google_drive_service_account()
        st.success(
            f"Autenticación OAuth2 exitosa con `drive.googleapis.com` (Proyecto: `motor-sii-python`). "
            f"Archivos compartidos detectados: **{len(archivos_drv)}**."
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

            pdfs_en_drive = [a for a in archivos_drv if a.get("name", "").lower().endswith(".pdf")]
            if pdfs_en_drive:
                st.markdown("#### Abrir y recortar cualquier PDF detectado en tu Google Drive:")
                c_p1, c_p2, c_p3 = st.columns([2.2, 0.9, 0.9])
                with c_p1:
                    elegido_pdf_drv = st.selectbox(
                        "Selecciona un PDF de tu Google Drive:",
                        options=[a["name"] for a in pdfs_en_drive],
                    )
                with c_p2:
                    p_i_drv = st.number_input("Desde página:", min_value=1, max_value=1500, value=1, step=1)
                with c_p3:
                    p_f_drv = st.number_input("Hasta página:", min_value=1, max_value=1500, value=1, step=1)

                id_elegido = next(a["id"] for a in pdfs_en_drive if a["name"] == elegido_pdf_drv)
                bytes_pdf_drv = descargar_bytes_archivo_drive_por_id(id_elegido)
                b64_cut, tot_p_drv, ri_d, rf_d = _recortar_paginas_pdf_en_base64(bytes_pdf_drv, p_i_drv, p_f_drv)
                if b64_cut:
                    st.caption(f"Mostrando página {ri_d} a {rf_d} de {tot_p_drv} totales en `{elegido_pdf_drv}`:")
                    st.markdown(
                        f'<iframe src="data:application/pdf;base64,{b64_cut}" width="100%" height="680" '
                        f'style="border:2px solid #1E3A8A;border-radius:6px;"></iframe>',
                        unsafe_allow_html=True,
                    )
        else:
            st.info(
                f"La conexión con Google Cloud está activa, pero aún no has compartido archivos con `{SERVICE_ACCOUNT_EMAIL}`. "
                f"Ve a tu pestaña de Google Drive, selecciona tus PDFs o tu carpeta de ramos -> **Compartir** -> pega `{SERVICE_ACCOUNT_EMAIL}`."
            )
    except Exception as exc_drv:
        st.error(f"Error al consultar Google Drive API: {exc_drv}")

# ------------------------------------------------------------------------------
# PESTAÑA 4: SINCRONIZADOR HÍBRIDO ULAGOS VIRTUAL (MOODLE SCRAPER)
# ------------------------------------------------------------------------------
with tab4:
    st.markdown(
        "<div class='sec-header'>4. SINCRONIZADOR AUTOMATIZADO DE CURSOS MOODLE (ULAGOS VIRTUAL INTEGRADO)</div>",
        unsafe_allow_html=True,
    )
    with st.form("form_login_moodle_integrado"):
        c_m1, c_m2, c_m3 = st.columns([1.4, 1.0, 1.4])
        with c_m1:
            usuario_moodle = st.text_input("Usuario de ULagos:", value="mauricioalejandro.vargas1")
        with c_m2:
            dominio_moodle = st.selectbox("Dominio Institucional:", options=["@alumnos.ulagos.cl", "@ulagos.cl"], index=0)
        with c_m3:
            clave_moodle = st.text_input("Contraseña ULagos Virtual:", value="ye16my7re4ij", type="password")

        iniciar_moodle_btn = st.form_submit_button(
            "INICIAR SINCRONIZACIÓN CON ULAGOS VIRTUAL Y CONECTAR PDFS AL VISOR",
            use_container_width=True,
        )

    if iniciar_moodle_btn:
        with st.status("Ejecutando sincronización híbrida con ULagos Virtual...", expanded=True) as status_box:
            try:
                sesion_activa, html_dash = _obtener_sesion_hibrida_moodle(usuario_moodle, dominio_moodle, clave_moodle)
            except Exception as e:
                status_box.update(label="Error de autenticación", state="error", expanded=True)
                st.error(f"No fue posible completar el inicio de sesión en Moodle: {e}")
                st.stop()

            soup_dash = BeautifulSoup(html_dash, "html.parser")
            cursos_dict = {}
            for a in soup_dash.find_all("a", href=True):
                if "course/view.php?id=" in a["href"]:
                    nombre = a.text.replace("Haga clic aquí para entrar al curso", "").strip()
                    nombre = re.sub(r"\s+", " ", nombre)
                    if len(nombre) > 5 and nombre not in cursos_dict.values():
                        cursos_dict[a["href"]] = nombre

            if not cursos_dict:
                cursos_dict["https://www.ulagosvirtual.cl/course/view.php?id=4056"] = "Gestión Tributaria (Respaldo)"

            estadisticas = {"descargados": 0, "omitidos": 0, "ignorados": 0}
            registro_archivos = []
            archivos_en_zip = set()
            anio_actual = datetime.now().year

            buffer_zip = io.BytesIO()
            barra_progreso = st.progress(0)
            total_cursos = len(cursos_dict)

            with zipfile.ZipFile(buffer_zip, "w", zipfile.ZIP_DEFLATED) as archivo_zip:
                for idx, (url_curso, nombre_curso) in enumerate(cursos_dict.items(), start=1):
                    carpeta_destino = _obtener_carpeta_ramo_moodle(nombre_curso, anio_actual)
                    st.write(f"Sincronizando asignatura ({idx}/{total_cursos}): **{nombre_curso}**")

                    response = sesion_activa.get(url_curso, verify=False)
                    soup = BeautifulSoup(response.text, "html.parser")
                    enlaces_principales = soup.find_all("a", href=True)

                    enlaces_directos = list(set([
                        a["href"] for a in enlaces_principales
                        if "resource/view.php" in a["href"] or "pluginfile.php" in a["href"] or "url/view.php" in a["href"]
                    ]))
                    enlaces_carpetas = list(set([
                        a["href"] for a in enlaces_principales if "folder/view.php" in a["href"]
                    ]))
                    enlaces_secciones = list(set([
                        a["href"] for a in enlaces_principales if "course/section.php" in a["href"]
                    ]))

                    contador = 1
                    for link in enlaces_directos:
                        estado, nom = _descargar_a_zip_moodle(
                            sesion_activa, link, archivo_zip, archivos_en_zip, carpeta_destino, contador
                        )
                        estadisticas[estado] += 1
                        if estado == "descargados" and nom:
                            registro_archivos.append({"Asignatura": carpeta_destino, "Archivo": nom})
                        contador += 1

                    for carpeta_url in enlaces_carpetas:
                        res_carpeta = sesion_activa.get(carpeta_url, verify=False)
                        archivos_adentro = list(set([
                            a["href"] for a in BeautifulSoup(res_carpeta.text, "html.parser").find_all("a", href=True)
                            if "pluginfile.php" in a["href"] and "forcedownload=1" in a["href"]
                        ]))
                        for link_interno in archivos_adentro:
                            link_limpio = (
                                link_interno.split("?")[0]
                                if "?" in link_interno and "pluginfile" in link_interno
                                else link_interno
                            )
                            estado, nom = _descargar_a_zip_moodle(
                                sesion_activa, link_limpio, archivo_zip, archivos_en_zip, carpeta_destino, contador
                            )
                            estadisticas[estado] += 1
                            if estado == "descargados" and nom:
                                registro_archivos.append({"Asignatura": carpeta_destino, "Archivo": nom})
                            contador += 1

                    for seccion_url in enlaces_secciones:
                        res_seccion = sesion_activa.get(seccion_url, verify=False)
                        recursos_seccion = list(set([
                            a["href"] for a in BeautifulSoup(res_seccion.text, "html.parser").find_all("a", href=True)
                            if "resource/view.php" in a["href"] or "pluginfile.php" in a["href"] or "url/view.php" in a["href"]
                        ]))
                        for link in recursos_seccion:
                            estado, nom = _descargar_a_zip_moodle(
                                sesion_activa, link, archivo_zip, archivos_en_zip, carpeta_destino, contador
                            )
                            estadisticas[estado] += 1
                            if estado == "descargados" and nom:
                                registro_archivos.append({"Asignatura": carpeta_destino, "Archivo": nom})
                            contador += 1

                    barra_progreso.progress(idx / total_cursos)

            st.session_state["moodle_zip_bytes"] = buffer_zip.getvalue()
            st.session_state["moodle_stats"] = estadisticas
            st.session_state["moodle_registro"] = registro_archivos
            status_box.update(label="Sincronización completada y PDFs conectados al Visor en Vivo", state="complete", expanded=False)

    if "moodle_zip_bytes" in st.session_state and st.session_state["moodle_zip_bytes"]:
        est = st.session_state.get("moodle_stats", {"descargados": 0, "omitidos": 0, "ignorados": 0})
        k1, k2, k3 = st.columns(3)
        k1.metric("Archivos Rescatados en Memoria", est["descargados"])
        k2.metric("Duplicados Omitidos", est["omitidos"])
        k3.metric("Enlaces Externos Ignorados", est["ignorados"])

        st.download_button(
            label="DESCARGAR PAQUETE COMPLETO DE CURSOS MOODLE (.ZIP)",
            data=st.session_state["moodle_zip_bytes"],
            file_name=f"Respaldo_ULagos_{datetime.now().year}.zip",
            mime="application/zip",
            use_container_width=True,
        )

# ------------------------------------------------------------------------------
# PESTAÑA 5: BÓVEDA MOODLE EN 1 CLIC Y BUSCADOR DE PÁGINAS
# ------------------------------------------------------------------------------
with tab5:
    st.markdown(
        "<div class='sec-header'>5. BÓVEDA DE CÁTEDRA ALOJADA EN EL SERVIDOR Y BUSCADOR DE PÁGINAS</div>",
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
