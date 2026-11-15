# -*- coding: utf-8 -*-
"""
app.py — HUB CENTRAL DE APLICACIONES Y EXTRACTOR DE CONTEXTO POR RAMO (ULAGOS 2026)
Repositorio: https://github.com/mauriciovargas1516-ux/github-context-extractor
- BLINDAJE ANTI-RATE-LIMIT (HTTP 403):
  1) Extrae todos los archivos de cada repositorio descargando el paquete .ZIP en memoria RAM
     directamente desde codeload.github.com (0 llamadas por archivo a api.github.com, sin límite de 60/hora).
  2) Si api.github.com devuelve HTTP 403 al listar repositorios, activa automáticamente el
     lector HTML de respaldo y el catálogo interno sin interrumpir la aplicación.
- Nomenclatura dinámica por asignatura o combinación de repositorios seleccionados.
- Cuadrillas Metodológicas con HIPERVÍNCULOS DIRECTOS a la literatura oficial (#page=N y ?cita=ID).
"""

import io
import os
import re
import json
import zipfile
import urllib.request
import urllib.error
from datetime import datetime
import streamlit as st
import pandas as pd


# ==============================================================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILO INSTITUCIONAL CLARO (SIN EMOJIS)
# ==============================================================================

st.set_page_config(
    page_title="Hub Académico y Extractor de Contexto ULagos 2026",
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
        padding-top: 1.4rem !important;
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
# 2. CATÁLOGO DE RAMOS, HIPERVÍNCULOS (#page=N) Y EXTRACTOS LITERALES DE CÁTEDRA
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
    "github-context-extractor": {
        "ramo": "Hub Central & Extractor de Contexto Académico",
        "sigla_archivo": "HUB_EXTRACTOR_CONTEXTO_ULAGOS",
        "corto": "HUB",
        "docente": "Portafolio Ingeniería Comercial ULagos",
        "app_url": "https://app-context-extractor-d8x5kwfdodzvmx7m3vean.streamlit.app/",
        "repo_url": "https://github.com/mauriciovargas1516-ux/github-context-extractor",
        "descripcion": "Motor centralizado de compilación vía descarga directa ZIP y biblioteca metodológica con citas de cátedra.",
    },
}


CUADRILLAS_LITERATURA_POR_RAMO = {
    "Evaluación Integrada de Proyectos (FDIC26)": {
        "docente": "Dra. Luz María Ferrada B.",
        "app_url": "https://proyectos-2026-ubfvxgpqmpp5z7dn6wlnn3.streamlit.app/",
        "tarjetas": [
            {
                "id": "proy_sni_2026",
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
                    "de los individuos respecto a sus decisiones de consumo.\n"
                    "1. Elegir el óptimo de producción/inversión hasta que la tasa marginal de rentabilidad del último proyecto se iguale a la tasa de interés de mercado (decisión objetiva y delegable).\n"
                    "2. Elegir el patrón óptimo de consumo prestando o pidiendo prestado a lo largo de la línea del mercado de capitales hasta que TMS(C0, C1) se iguale con (1 + rf) (decisión indelegable)."
                ),
                "links": [
                    ("Abrir Simulador Finanzas Avanzadas en Streamlit", "https://finanzas-avanzadas-2026.streamlit.app/"),
                    ("Repositorio GitHub Finanzas Avanzadas", "https://github.com/mauriciovargas1516-ux/FINANZAS-AVANZADAS-2026"),
                ],
            },
            {
                "id": "fin_riesgo_dupont",
                "titulo": "2. Actitudes frente al Riesgo, Juego Justo y Poder Generador de Utilidades (PGU / DuPont)",
                "formula": r"PGU = \underbrace{\left(\frac{\text{Resultado Operacional}}{\text{Ventas}}\right)}_{\text{Margen Operacional}} \times \underbrace{\left(\frac{\text{Ventas}}{\text{Activos Operacionales}}\right)}_{\text{Rotación de Activos}}",
                "tip": (
                    "Un juego es 'justo' cuando el valor esperado de la riqueza si aceptas es igual al valor seguro si rechazas. "
                    "El individuo averso al riesgo tiene utilidad marginal decreciente y prefiere renta segura antes que incierta de igual valor esperado. "
                    "En la empresa, el PGU mide la rentabilidad contable de los activos operacionales combinando margen y rotación."
                ),
                "fuente": (
                    "Camila Bustos Rosas (2026), 'Relación riesgo rentabilidad.pdf', láminas 7-21 (Incertidumbre y Utilidad) "
                    "y láminas 26-35 (PGU, DuPont y Riesgo Operacional vs. Financiero); y Ross et al. (2010), Cap. 3, pág. 64."
                ),
                "marcador_moodle": "FINANZAS AVANZADAS 2026/Relaci",
                "extracto_literal": (
                    "--- [FINANZAS AVANZADAS 2026/Relación riesgo rentabilidad.pdf | Páginas 8, 14, 21 y 28] ---\n"
                    "• Juego justo (Lámina 8): el valor esperado de la riqueza si aceptas el juego es igual al valor seguro si lo rechazas.\n"
                    "• Individuos renuentes al riesgo (Lámina 14): utilidad marginal de la renta desciende cuando la renta aumenta; prefieren renta segura.\n"
                    "• Límite del valor de la información (Lámina 21): El valor de la información no puede superar el costo de tomar una mala decisión sin ella.\n"
                    "• PGU (Lámina 28): PGU = Margen de Utilidad Operacional x Rotación de Activos Operacionales."
                ),
                "links": [
                    ("Abrir Calculadora DuPont y Utilidad en Finanzas App", "https://finanzas-avanzadas-2026.streamlit.app/"),
                ],
            },
            {
                "id": "fin_markowitz_capm",
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
                    "• Ecuación de Hamada (Lámina 49): Beta_L = Beta_U * [1 + (1 - t)*(B / S)].\n\n"
                    "--- [FINANZAS AVANZADAS 2026/Taller Frontera Eficiente Ing Comercial.xlsx] ---\n"
                    "Dupla 13 (Raquel Becerra, Mauricio Vargas, Catalina Marigual): Cartera 13 (Parque Arauco - Andina-B - Cenco Malls - Banco de Chile - Vapores) y Cartera 20 / Cartera 6."
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
                "titulo": "1. Teoría de la Localización: Von Thünen, Weber, Hotelling, Christaller-Lösch y Krugman",
                "formula": r"LR = Y(m - c) - Ytd \quad | \quad IM = \frac{\text{Peso MP Localizadas}}{\text{Peso Producto Final}} \quad | \quad p^*(x) = \frac{aW(x)}{\rho}",
                "tip": (
                    "En Von Thünen la renta agrícola decrece con la distancia formando anillos concéntricos. "
                    "En Weber, si IM > 1 la fábrica se ubica cerca de los insumos; si IM < 1 se ubica cerca del mercado, "
                    "desviándose hacia un enclave laboral barato solo si éste cae dentro de la isodápana crítica. "
                    "En Krugman (1995), el patrón centro-periferia emerge de economías de escala, bajos costos de transporte y fuerzas centrípetas."
                ),
                "fuente": (
                    "Néstor Duch Brown (Universitat de Barcelona), 'La_teoria_de_la_localizacion.pdf', "
                    "Secciones 1.1 a 1.4 (págs. 6-23) y Secciones 2.1 a 3 (págs. 34-66)."
                ),
                "marcador_moodle": "TERRITORIAL 2026/La_teoria_de_la_localizacion.pdf | Página 7",
                "extracto_literal": (
                    "--- [TERRITORIAL 2026/La_teoria_de_la_localizacion.pdf | Páginas 7, 12, 13 y 43] ---\n"
                    "• Von Thünen (Pág. 7): LR = Y(m - c) - Y*t*d (donde LR es renta por unidad de tierra, Y producto, m precio mercado, c costo producción, t tarifa transporte, d distancia).\n"
                    "• Weber (Pág. 12-13): IM = peso de las materias primas localizadas / peso del producto final. Aquella isodápana que tiene el mismo valor que el ahorro en el coste de la mano de obra se denomina isodápana crítica.\n"
                    "• Krugman (Pág. 43): Fuerzas Centrípetas (ventajas naturales, economías externas pecuniarias de acceso a mercados/productos, spillovers tecnológicos) vs. Fuerzas Centrífugas (altas rentas inmobiliarias, congestión, contaminación)."
                ),
                "links": [
                    ("Abrir Plataforma Desarrollo y Gestión Territorial", "https://desarrollo-y-gestion-territorial-2026.streamlit.app/"),
                    ("Repositorio GitHub Territorial 2026", "https://github.com/mauriciovargas1516-ux/DESARROLLO-Y-GESTION-TERRITORIAL-2026"),
                ],
            },
            {
                "id": "terr_ot_guttman",
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
                    "• Índice de Primacía: establece una relación entre el peso relativo del principal centro poblado del territorio, en referencia a la suma de los tres siguientes.\n"
                    "• Escala de Gutmann / Matriz de Rondinelli: registra presencia (1) o ausencia (0) de servicios, infraestructura o funciones. Ya que las localidades están ordenadas en función a su población, el índice funcional debe tener una jerarquía decreciente.\n\n"
                    "--- [TERRITORIAL 2026/Unidad 5. Ordenamiento Territorial.pdf | Página 1] ---\n"
                    "La idea es encontrar DIFERENCIAS entre las comunas de su territorio. Es decir, si todas tuvieran valor 1 en todas las categorías, se debe cambiar/incorporar por otras variables. Como mínimo, deben existir 7 variables."
                ),
                "links": [
                    ("Manual Elaboración PLADECO (SUBDERE PDF)", "http://www.subdere.gov.cl/sites/default/noticiasold/articles-77172_recurso_1.pdf"),
                    ("Abrir Módulo Guttman / Rondinelli en App Territorial", "https://desarrollo-y-gestion-territorial-2026.streamlit.app/"),
                ],
            },
            {
                "id": "terr_dini_ucinet",
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
                    "Entrevista 1: Gremio, cooperativa u organización articuladora (Cooperación y visión del territorio).\n"
                    "Entrevista 2: Empresa o productor del rubro (Operación, proveedores y compradores).\n"
                    "Entrevista 3: Empresa de otro eslabón (Contrastar flujos y dificultades).\n"
                    "Durante y después: No sugieran que necesariamente debe existir un clúster. No hablen de DEBILIDADES; indiquen desafíos, mejoras o aspectos para fortalecer."
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
                "titulo": "1. Determinación Mensual del IVA, Crédito Fiscal y Exclusión de Automóviles (D.L. N° 825)",
                "formula": r"\text{Neto Boleta} = \frac{\text{Total Bruto}}{1,19} \quad | \quad \text{Remanente UTM} = \frac{\text{Remanente CLP}}{\text{UTM}_{\text{mes declaración}}}",
                "tip": (
                    "El IVA en la compra de automóviles o station wagons (Art. 23 N° 4 D.L. 825) NO da derecho a crédito fiscal "
                    "y se registra como 'IVA no recuperable' (a diferencia de un furgón de reparto o una grúa horquilla, que sí dan crédito). "
                    "Si el Crédito supera al Débito, el remanente (cód. 77 F29) se convierte a UTM y se reajusta el mes siguiente (cód. 504)."
                ),
                "fuente": (
                    "Prof. RVS (2026), 'Apunte IVA 2026.pdf' (págs. 1-8), 'IVA y Toma de Decisiones.pdf' (pág. 3) "
                    "y 'Ejerc-03 / Ejerc-04 Ejercicio IVA (Datos).xlsx' (Hojas Libro Compras y Resumen IVA)."
                ),
                "marcador_moodle": "TRIBUTARIA 2026/IVA y Toma de Decisiones.pdf | Página 3",
                "extracto_literal": (
                    "--- [TRIBUTARIA 2026/IVA y Toma de Decisiones.pdf | Página 3] ---\n"
                    "Si el Crédito Fiscal > Débito Fiscal, se genera un remanente de crédito fiscal que puede ser imputado a los débitos fiscales de períodos posteriores:\n"
                    "Remanente Anterior en UTM = Remanente Anterior $ / UTM Mes siguiente.\n"
                    "Luego, en el mes siguiente: Remanente actualizado = Remanente Anterior en UTM x UTM Mes siguiente.\n\n"
                    "--- [TRIBUTARIA 2026/Ejerc-04 Ejercicio IVA (Datos).xlsx | Hoja Libro Compras] ---\n"
                    "El IVA del automóvil (Art. 23 N°4 DL 825: Automóvil station wagon para gerencia) no da derecho a crédito fiscal: se registra como IVA no recuperable."
                ),
                "links": [
                    ("D.L. N° 825 Ley sobre Impuesto a las Ventas y Servicios (BCN)", "https://www.bcn.cl/leychile/navegar?idNorma=6369"),
                    ("Guía SII Empresario Individual y 1.ª Categoría (PDF)", "https://www.sii.cl/siieduca/aprende-con-nosotros/docs/empresario_individual.pdf"),
                    ("Abrir Suite Tributaria 2026 en Streamlit", "https://gestion-tributaria-2026.streamlit.app/"),
                ],
            },
            {
                "id": "trib_art97_delitos",
                "titulo": "2. Infracciones y Delitos Tributarios (Art. 97 Código Tributario y Ley N° 20.393)",
                "formula": r"\text{Art. 97 N° 4 CT (Facturas Falsas): Multa } 50\%\text{–}400\% \text{ del tributo eludido} + \text{Presidio}",
                "tip": (
                    "En el caso 'El Espejo Tributario (Constructora del Sur S.A.)', ingresar 3 facturas falsas por $50.000.000 netos "
                    "($9.500.000 de IVA) de un proveedor simulado obliga a restituir el IVA Crédito Fiscal, rechaza el gasto en Renta, "
                    "aplica intereses penales (1,5% mensual), configura delito penal bajo el Art. 97 N° 4 del Código Tributario y activa "
                    "la responsabilidad penal de la persona jurídica bajo la Ley N° 20.393."
                ),
                "fuente": (
                    "Prof. RVS (2026), 'Caso GTTD Emision Facturas Falsas (Datos).pdf' (págs. 1-2), "
                    "'Clase Infracciones Sanciones Delitos GTD.pdf' (láminas 4-21) y 'Clase Notificaciones GTD.pdf' (láminas 4-12)."
                ),
                "marcador_moodle": "TRIBUTARIA 2026/Caso GTTD Emision Facturas Falsas (Datos).pdf | Página 1",
                "extracto_literal": (
                    "--- [TRIBUTARIA 2026/Caso GTTD Emision Facturas Falsas (Datos).pdf | Páginas 1 y 2] ---\n"
                    "Servicios y Asesorías Global SpA emite a Constructora del Sur S.A. tres facturas electrónicas por $50.000.000 netos más $9.500.000 de IVA ($59.500.000 total) sin prestación real.\n"
                    "• Artículo 97 N°4 CT: Sanciona la presentación maliciosa de declaraciones incompletas o falsas mediante facturas falsas o simuladas con multas de 50% a 300% (o hasta 400%) del tributo evadido más presidio.\n\n"
                    "--- [TRIBUTARIA 2026/Clase Infracciones Sanciones Delitos GTD.pdf | Página 20] ---\n"
                    "Bajo la Ley N° 20.393, las empresas responden penalmente por delitos tributarios (Art. 97 N° 4) cometidos por sus dueños o ejecutivos en beneficio social, exigiendo un Modelo de Prevención de Delitos (MPD)."
                ),
                "links": [
                    ("Código Tributario D.L. N° 830 en Biblioteca del Congreso Nacional", "https://www.bcn.cl/leychile/navegar?idNorma=6374"),
                    ("Portal SII Educación Fiscal y Cumplimiento", "https://www.sii.cl/destacados/sii_educa/"),
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
                "titulo": "1. Análisis de Casos y Clasificación Funcional (Para Atletismo vs. Para Powerlifting)",
                "formula": r"\text{Para Atletismo: } T\text{ (Pista)} / F\text{ (Campo)} \quad | \quad \text{Para Powerlifting: Categorías solo por Peso Corporal}",
                "tip": (
                    "Caso 1 (Martín, amputación transtibial unilateral con prótesis en 100/200m): deficiencia por amputación/disminución de "
                    "longitud de extremidad; clase probable T64. Caso 2 (Carolina, lesión medular T10): elegible en Para Powerlifting, "
                    "donde NO hay clases por nivel de lesión sino solo divisiones por sexo y peso corporal. Caso 3 (Diego, parálisis cerebral "
                    "espástica ambulatoria en bala): hipertonía/espasticidad, clases F35-F38. Caso 4 (Valentina, discapacidad visual): "
                    "puede competir en disco (F11-F13), pero NO en World Para Powerlifting porque la deficiencia visual no es elegible allí."
                ),
                "fuente": (
                    "Prof. Exal García Carrillo (2026), 'Taller_II_Deporte_Paralimpico.pdf', Casos 1 al 4, págs. 1-3; y "
                    "'Entrevista para deportista.pdf', págs. 1-5."
                ),
                "marcador_moodle": "Taller_II_Deporte_Paralimpico.pdf | Página 1",
                "extracto_literal": (
                    "--- [[2026]A1 INTRODUCCIÓN AL DEPORTE PARALÍMPICO 2026/Taller_II_Deporte_Paralimpico.pdf | Páginas 1-3] ---\n"
                    "• Caso 1 (Martín, 24 años): amputación transtibial pierna derecha, usa prótesis, pruebas de 100 y 200 m en para atletismo.\n"
                    "• Caso 2 (Carolina, 30 años): lesión medular completa T10, usa silla de ruedas, desea competir en para powerlifting.\n"
                    "• Caso 3 (Diego, 19 años): parálisis cerebral espástica ambulatoria, alteraciones de equilibrio y coordinación, lanzamiento de bala.\n"
                    "• Caso 4 (Valentina, 22 años): discapacidad visual congénita severa, desea entrenar lanzamiento de disco y consulta por para powerlifting."
                ),
                "links": [
                    ("Clasificación Oficial Comité Paralímpico Internacional (IPC)", "https://www.paralympic.org/classification"),
                    ("Reglamento World Para Athletics", "https://www.paralympic.org/athletics/classification"),
                    ("Reglamento World Para Powerlifting", "https://www.paralympic.org/powerlifting/classification"),
                ],
            },
        ],
    },
}


# ==============================================================================
# 3. MOTOR ANTI-RATE-LIMIT: DESCARGA ZIP VÍA CODELOAD Y FALLBACK DE REPOSITORIOS
# ==============================================================================

EXTENSIONES_TEXTO_PERMITIDAS = (
    ".py", ".md", ".txt", ".toml", ".json", ".yaml", ".yml",
    ".css", ".html", ".js", ".rmd", ".r", ".sql", ".sh", ".csv"
)


@st.cache_data(show_spinner=False)
def cargar_texto_destilado_local():
    carpeta = os.path.dirname(os.path.abspath(__file__))
    for f in os.listdir(carpeta):
        if f.lower().endswith(".txt") and f not in ("requirements.txt", "packages.txt"):
            ruta = os.path.join(carpeta, f)
            try:
                with open(ruta, "r", encoding="utf-8", errors="replace") as fp:
                    return f, fp.read()
            except Exception:
                pass
    return None, ""


def buscar_pagina_en_destilado_local(marcador):
    _, texto_completo = cargar_texto_destilado_local()
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
    """
    Si api.github.com devuelve HTTP 403 (rate limit exceeded), obtiene los repositorios
    directamente del HTML público de GitHub (que no tiene límite de 60 llamadas) y los
    combina con el catálogo de asignaturas conocido.
    """
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
        # Fallback instantáneo sin error 403
        return _listar_repositorios_fallback_html_y_catalogo(usuario), True


def _descargar_zip_repositorio_en_memoria(usuario, nombre_repo, rama_preferida="main", token=""):
    """
    Descarga el archivo .ZIP completo del repositorio desde codeload.github.com en una sola
    petición HTTP (NO consume cuota de api.github.com y es inmune al Error 403).
    """
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
    """
    Extrae el inventario y todos los archivos de código de un repositorio descomprimiendo su
    paquete ZIP en memoria RAM (0 llamadas a api.github.com).
    """
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
# 4. RENDERIZADOR DE CUADRILLAS CON HIPERVÍNCULOS EXTERNOS E INTERNOS
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
                        f"Ver Extracto Literal de la Página/Lámina</a>"
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

                    with st.expander(f"Abrir transcripción exacta de la página ({t['marcador_moodle']})", expanded=False):
                        st.code(t["extracto_literal"], language="text")
                        fragmento_repo = buscar_pagina_en_destilado_local(t.get("marcador_moodle", ""))
                        if fragmento_repo:
                            st.caption("Coincidencia directa verificada en el archivo destilado del repositorio:")
                            st.code(fragmento_repo, language="text")


# ==============================================================================
# 5. INTERFAZ PRINCIPAL DE USUARIO Y DETECTOR DE HIPERVÍNCULO INTERNO (?cita=...)
# ==============================================================================

st.markdown(
    """
    <div class="top-banner">
        <h1>HUB DE APLICACIONES Y EXTRACTOR DE CONTEXTO ACADÉMICO POR RAMO (ULAGOS 2026)</h1>
        <p>Compilación en vivo vía descarga directa ZIP (sin límite de llamadas API) con nomenclatura dinámica por asignatura, cuadrillas metodológicas e hipervínculos directos a la literatura.</p>
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
                    VISOR DE EVIDENCIA LITERAL DE CÁTEDRA — {ramo_c.upper()} ({doc_c})
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
        st.markdown("**Extracto literal de la página / diapositiva donde se explica este concepto:**")
        st.code(tarjeta_c["extracto_literal"], language="text")
        frag_local = buscar_pagina_en_destilado_local(tarjeta_c.get("marcador_moodle", ""))
        if frag_local:
            st.markdown("**Contexto extendido extraído en vivo desde el archivo maestro del repositorio:**")
            st.code(frag_local, language="text")
        if st.button("Cerrar Visor de Cita Literal"):
            st.query_params.clear()
            st.rerun()
        st.divider()

with st.sidebar:
    st.markdown("### Configuración de Conexión")
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
        "Incluir Cuadrilla de Literatura e Hipervínculos dentro del .TXT descargado",
        value=True,
    )
    if st.button("Actualizar Lista de Repositorios", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

tab1, tab2, tab3, tab4 = st.tabs([
    "1. Extractor Personalizado por Ramo (Sin Límite API)",
    "2. Cuadrillas con Hipervínculos a la Literatura",
    "3. Directorio de Plataformas Streamlit en Vivo",
    "4. Buscador en Archivos de Cátedra Destilados",
])

# ------------------------------------------------------------------------------
# PESTAÑA 1: EXTRACTOR PERSONALIZADO POR RAMO (INMUNE A ERROR 403)
# ------------------------------------------------------------------------------
with tab1:
    st.markdown(
        "<div class='sec-header'>1. SELECCIÓN DE RAMOS / REPOSITORIOS Y NOMENCLATURA PERSONALIZADA</div>",
        unsafe_allow_html=True,
    )

    lista_repos, usando_fallback = listar_repositorios_usuario(usuario_gh, token=token_gh)
    if usando_fallback:
        st.caption(
            "Modo Directo Codeload Activo: Lista de repositorios cargada vía catálogo web directo "
            "(evitando el límite de 60 consultas/hora de api.github.com)."
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

        with st.expander("Ver vista previa del nuevo encabezado personalizado del archivo .TXT", expanded=False):
            st.code(encabezado_sugerido, language="text")

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
# PESTAÑA 2: CUADRILLAS CON HIPERVÍNCULOS DIRECTOS A LA LITERATURA (#page=N)
# ------------------------------------------------------------------------------
with tab2:
    st.markdown(
        "<div class='sec-header'>2. CUADRILLAS METODOLÓGICAS CON HIPERVÍNCULOS A LA PÁGINA EXACTA DE LA LITERATURA</div>",
        unsafe_allow_html=True,
    )
    st.caption(
        "Haz clic en los botones azules de cada tarjeta para abrir el PDF oficial o la ley en la página exacta (#page=N), "
        "o en el botón verde para abrir el extracto literal de la lámina/página de Moodle."
    )
    ramos_disponibles_lit = ["Mostrar Todos los Ramos"] + list(CUADRILLAS_LITERATURA_POR_RAMO.keys())
    filtro_ramo_lit = st.selectbox("Filtrar cuadrillas por asignatura:", options=ramos_disponibles_lit)

    if filtro_ramo_lit == "Mostrar Todos los Ramos":
        for nombre_r in CUADRILLAS_LITERATURA_POR_RAMO:
            renderizar_cuadrillas_ramo(nombre_r)
    else:
        renderizar_cuadrillas_ramo(filtro_ramo_lit)

# ------------------------------------------------------------------------------
# PESTAÑA 3: DIRECTORIO DE PLATAFORMAS STREAMLIT EN VIVO
# ------------------------------------------------------------------------------
with tab3:
    st.markdown(
        "<div class='sec-header'>3. DIRECTORIO CENTRAL DE APLICACIONES WEB EN VIVO (STREAMLIT CLOUD)</div>",
        unsafe_allow_html=True,
    )
    filas_dir = []
    for k_repo, v_meta in MAPA_REPOS_A_RAMOS.items():
        if k_repo == "FINANZAS-AVANZADAS":
            continue
        filas_dir.append({
            "Asignatura / Plataforma": v_meta["ramo"],
            "Docente": v_meta["docente"],
            "Repositorio GitHub": k_repo,
            "Enlace GitHub": v_meta["repo_url"],
            "Aplicación Web en Vivo": v_meta["app_url"],
            "Alcance Técnico": v_meta["descripcion"],
        })
    df_dir = pd.DataFrame(filas_dir)
    st.dataframe(
        df_dir,
        column_config={
            "Enlace GitHub": st.column_config.LinkColumn("Repositorio GitHub"),
            "Aplicación Web en Vivo": st.column_config.LinkColumn("Abrir App en Streamlit"),
        },
        hide_index=True,
        use_container_width=True,
    )

# ------------------------------------------------------------------------------
# PESTAÑA 4: BUSCADOR DE PÁGINAS EN ARCHIVOS DE CÁTEDRA DESTILADOS
# ------------------------------------------------------------------------------
with tab4:
    st.markdown(
        "<div class='sec-header'>4. BUSCADOR DIRECTO DE PÁGINAS Y AUTORES EN ARCHIVOS DE CÁTEDRA ALOJADOS</div>",
        unsafe_allow_html=True,
    )
    carpeta_actual = os.path.dirname(os.path.abspath(__file__))
    archivos_locales = [
        f for f in os.listdir(carpeta_actual)
        if os.path.isfile(os.path.join(carpeta_actual, f))
        and f.lower().endswith((".txt", ".zip", ".md"))
        and f not in ("requirements.txt", "packages.txt", "README.md")
    ]

    if not archivos_locales:
        st.info("No se detectaron archivos .txt o .zip adicionales en la raíz del repositorio local.")
    else:
        arch_elegido = st.selectbox("Selecciona un archivo de cátedra alojado en el servidor:", options=archivos_locales)
        ruta_completa_local = os.path.join(carpeta_actual, arch_elegido)
        tam_mb = os.path.getsize(ruta_completa_local) / (1024 * 1024)
        st.caption(f"Archivo seleccionado: `{arch_elegido}` ({tam_mb:.2f} MB)")

        with open(ruta_completa_local, "rb") as f_loc:
            bytes_locales = f_loc.read()

        st.download_button(
            label=f"DESCARGAR {arch_elegido}",
            data=bytes_locales,
            file_name=arch_elegido,
            mime="application/octet-stream",
            use_container_width=True,
        )

        if arch_elegido.lower().endswith(".txt"):
            texto_local = bytes_locales.decode("utf-8", errors="replace")
            busqueda = st.text_input(
                "Buscar autor, fórmula o marcador de página (ej. 'Fontaine', 'Hamada', 'Weber', 'Página 20'):"
            )
            if busqueda.strip():
                lineas_tot = texto_local.splitlines()
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
