# -*- coding: utf-8 -*-
"""
app.py — HUB CENTRAL DE APLICACIONES Y EXTRACTOR DE CONTEXTO POR RAMO (ULAGOS 2026)
Repositorio: https://github.com/mauriciovargas1516-ux/github-context-extractor
- Personaliza automáticamente el nombre del archivo .txt y su encabezado según el ramo o los
  repositorios seleccionados (reemplazando el nombre genérico SUPER_CONTEXTO).
- Incorpora Cuadrillas Metodológicas e Informativas con citas exactas de la literatura oficial
  (autor, documento de Moodle, capítulo y página/lámina) para cada asignatura.
- Permite inyectar la cuadrilla bibliográfica directamente en el .txt descargado.
- Detecta y permite descargar archivos locales de cátedra presentes en el repositorio.
"""

import os
import re
import json
import base64
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
        margin-bottom: 12px;
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
        padding: 6px 10px;
        font-size: 11.8px;
        color: #0F172A;
        font-weight: 600;
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
# 2. CATÁLOGO OFICIAL DE RAMOS, REPOSITORIOS Y LITERATURA (CON PÁGINAS EXACTAS)
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
        "descripcion": "Motor centralizado de compilación vía API REST de GitHub y biblioteca metodológica con citas de cátedra.",
    },
}

CUADRILLAS_LITERATURA_POR_RAMO = {
    "Evaluación Integrada de Proyectos (FDIC26)": {
        "docente": "Dra. Luz María Ferrada B.",
        "tarjetas": [
            {
                "titulo": "1. Precios Sociales Vigentes SNI 2026 (Mano de Obra, Divisa y TSD)",
                "formula": r"TSD = 5,5\% \quad | \quad PSMO = Salario_{Bruto} \times FCSMO \quad (MOC=0,97;\; MOSC=0,95;\; MONC=0,91;\; Divisa=1,00)",
                "tip": (
                    "El Precio Social de la Mano de Obra (PSMO) es siempre menor o igual al salario privado. "
                    "Según la tabla CIUO-08 del SNI, los choferes de buses interregionales u operadores de máquinas "
                    "corresponden a Mano de Obra Semicalificada (MOSC = 0,95), no a MONC. Además, aunque un terreno sea "
                    "municipal, siempre debe valorizarse a su costo de oportunidad social."
                ),
                "fuente": (
                    "Ministerio de Desarrollo Social y Familia [MDSF] (2026), 'Precios-Sociales-2026.pdf', Cap. 1, "
                    "Tablas 1.1 a 1.4, págs. 4-6; y Dra. Luz María Ferrada (2026), 'Proceso2 RA1.pdf', Preguntas I.11, I.15 y II.3, págs. 1-2."
                ),
            },
            {
                "titulo": "2. Valor Social de la Producción (Fontaine): Eficiencia vs. Agencia",
                "formula": r"VSP = AD + LR = VPP + \Delta EC + \Delta EP \quad | \quad P_{social} = \frac{P_0 + P_1}{2}",
                "tip": (
                    "En un mercado sin distorsiones ni comercio exterior, al entrar el proyecto la oferta se desplaza "
                    "(Q' = Q + Q_proy) y el precio baja de P0 a P1. El Aumento en Disponibilidad (AD) se mide bajo la curva "
                    "de demanda entre Q0 y Qd1; la Liberación de Recursos (LR) se mide bajo la curva de oferta antigua entre Qo1 y Q0."
                ),
                "fuente": (
                    "Ernesto R. Fontaine (2008), 'Evaluación Social de Proyectos' (13.ª ed.), Cap. V (págs. 199-255) y "
                    "Cap. VII (págs. 373-385); y Dra. Luz María Ferrada (2026), 'Clase2.pdf', Ejercicio Mercado de la Leche, láminas 15-25."
                ),
            },
            {
                "titulo": "3. Cuándo elegir entre VAN, VAC y CAE en el SNI",
                "formula": r"VAC = \sum_{t=0}^{n} \frac{C_t}{(1 + r)^t} \quad | \quad CAE = VAC \cdot \frac{r(1 + r)^n}{(1 + r)^n - 1}",
                "tip": (
                    "Usa VAN cuando las alternativas tienen igual vida útil y los beneficios son medibles. "
                    "Usa VAC cuando los beneficios son iguales o difíciles de medir y las alternativas tienen igual horizonte. "
                    "Usa CAE (o CAE por producto/tonelada) cuando las alternativas tienen distinta vida útil o distinto volumen de producción."
                ),
                "fuente": (
                    "Dra. Luz María Ferrada (2026), 'Clase2.pdf' (lámina 12) y 'Proceso2 RA1.pdf' (Sección II.1, pág. 2); "
                    "MDSF (2025), 'METODOLOGIA-GENERAL-2025.pdf', Sección III.4, págs. 55-58; y 'Metodologia_GIRS_vf.pdf', pág. 10."
                ),
            },
            {
                "titulo": "4. Árboles Causales, Población SNI y Matriz de Marco Lógico (MML)",
                "formula": r"\text{Población Referencia} \supset \text{Población Afectada (Con Problema)} \supset \text{Población Objetivo}",
                "tip": (
                    "Nunca redactes el problema como 'falta de una solución' (ej. 'falta un camión recolector' o 'no hay consultorio'). "
                    "En el Marco Lógico: (1) cada proyecto tiene un único Propósito (que nace del Objetivo Central del árbol), "
                    "(2) los indicadores se dividen en Eficacia, Eficiencia, Calidad y Economía, y (3) a nivel de Actividades no se definen supuestos."
                ),
                "fuente": (
                    "Ortegón, Pacheco y Roura (2005), 'Serie Manuales CEPAL N° 39', Cap. I, págs. 10-21; "
                    "Dra. Luz María Ferrada (2026), 'Presentación_2.pdf' (láminas 5-21), 'Clase3.pdf' (láminas 7-8) y 'MARCO LOGICO.pdf' (láminas 6-21)."
                ),
            },
            {
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
            },
            {
                "titulo": "6. Flujo Privado Puro vs. Flujo Financiado y Capital de Trabajo",
                "formula": r"Cuota = P \cdot \frac{r(1+r)^n}{(1+r)^n - 1} \quad | \quad CT_{desfase} = \frac{\text{Costos Anuales} \times \text{Días Desfase}}{365}",
                "tip": (
                    "En el flujo con deuda, solo los intereses bancarios se restan antes de impuestos (creando escudo fiscal), "
                    "mientras que la amortización del principal se resta después de impuestos. Los costos hundidos son obligaciones "
                    "contraídas en el pasado e inevitables, por lo que son irrelevantes en un flujo incremental."
                ),
                "fuente": (
                    "Dra. Luz María Ferrada (2026), 'Clase1 (18 ago).pdf', láminas 17-18 (Capital de Trabajo), "
                    "láminas 23-32 (Flujo Puro vs. Financiado y Tabla de Crédito) y láminas 33-36 (Flujos Incrementales y Costos Hundidos)."
                ),
            },
        ],
    },
    "Finanzas Avanzadas": {
        "docente": "Prof.ª Camila Bustos Rosas",
        "tarjetas": [
            {
                "titulo": "1. Modelo Consumo-Inversión y Principio de Separación de Fisher",
                "formula": r"U = f(C_0, C_1) \quad | \quad \text{Óptimo Productivo: } RMgI = r_f \quad | \quad \text{Óptimo Consumo: } TMS(C_0, C_1) = -(1 + r_f)",
                "tip": (
                    "En un mercado de capitales perfecto (sin fricciones, costos de transacción ni impuestos), la decisión de inversión "
                    "de la empresa es objetiva y delegable a los administradores (aceptar proyectos hasta que la rentabilidad marginal "
                    "iguale la tasa de mercado rf), independientemente de las preferencias subjetivas de consumo intertemporal de cada dueño."
                ),
                "fuente": (
                    "Camila Bustos Rosas (2026), 'Consumo - Inversión.pdf', láminas 2-10; y "
                    "Brealey, Myers y Allen (2010), 'Principios de Finanzas Corporativas' (9.ª ed.), Cap. 2, Sección 2.2, págs. 19-22."
                ),
            },
            {
                "titulo": "2. Actitudes frente al Riesgo, Juego Justo y Valor de la Información",
                "formula": r"E(W) = \sum_{i=1}^{n} Pr_i \cdot W_i \quad | \quad \sigma = \sqrt{\sum_{i=1}^{n} Pr_i \cdot [W_i - E(W)]^2}",
                "tip": (
                    "Un juego es 'justo' cuando la riqueza esperada de aceptarlo es exactamente igual a la riqueza segura inicial. "
                    "El inversionista averso al riesgo tiene utilidad marginal positiva pero decreciente y siempre rechaza un juego justo. "
                    "El valor de la información perfecta jamás puede superar el costo de tomar una mala decisión sin ella."
                ),
                "fuente": (
                    "Camila Bustos Rosas (2026), 'Relación riesgo rentabilidad.pdf', láminas 7-21; y "
                    "'Guía introductoria - Finanzas.pdf', Ejercicios 1 al 5, pág. 1."
                ),
            },
            {
                "titulo": "3. Poder Generador de Utilidades (PGU) y Descomposición DuPont",
                "formula": r"PGU = \underbrace{\left(\frac{\text{Resultado Operacional}}{\text{Ventas}}\right)}_{\text{Margen Operacional}} \times \underbrace{\left(\frac{\text{Ventas}}{\text{Activos Operacionales}}\right)}_{\text{Rotación de Activos}}",
                "tip": (
                    "El administrador financiero enfrenta el dilema permanente entre Liquidez (capacidad de pagar deudas de corto plazo, "
                    "clave para sobrevivir) y Rentabilidad (capacidad de generar fondos futuros). El riesgo total del accionista suma "
                    "el riesgo operacional (variabilidad de las ventas/PGU) más el riesgo financiero (carga fija por intereses de deuda)."
                ),
                "fuente": (
                    "Camila Bustos Rosas (2026), 'Relación riesgo rentabilidad.pdf', láminas 23-35; "
                    "Ross, Westerfield y Jordan (2010), Cap. 3 (pág. 64); y Gitman y Zutter (2012), Cap. 3, págs. 73-84."
                ),
            },
            {
                "titulo": "4. Teoría de la Cartera de Markowitz y Taller Frontera Eficiente (252 días)",
                "formula": r"E(R_p) = \sum_{i=1}^{n} w_i E(R_i) \quad | \quad \sigma_p = \sqrt{w_A^2 \sigma_A^2 + w_B^2 \sigma_B^2 + 2 w_A w_B \rho_{AB} \sigma_A \sigma_B} \quad | \quad \sigma_{anual} = \sigma_{diaria} \sqrt{252}",
                "tip": (
                    "Mientras la correlación sea menor a +1 (rho < 1), la desviación estándar del portafolio es estrictamente menor "
                    "que el promedio ponderado de las desviaciones individuales. En el Taller del IPSA (Dupla 13: Parque Arauco, Andina-B, "
                    "Cenco Malls, Banco de Chile, Vapores), los precios faltantes se rellenan con el cierre del día anterior (nunca con cero)."
                ),
                "fuente": (
                    "Camila Bustos Rosas (2026), 'Teoría de mercado de capitales.pdf' (láminas 11-36), "
                    "'Instrucciones taller frontera eficiente.pdf' (págs. 1-2) y 'Taller Frontera Eficiente Ing Comercial.xlsx' (Hoja División cartera)."
                ),
            },
            {
                "titulo": "5. Modelo CAPM, Riesgo Sistemático y Ecuación de Hamada",
                "formula": r"R_e = R_f + \beta_L (R_m - R_f) \quad | \quad \beta_i = \frac{Cov(R_i, R_m)}{Var(R_m)} \quad | \quad \beta_L = \beta_U \left[1 + (1 - t)\frac{B}{S}\right]",
                "tip": (
                    "La diversificación elimina el riesgo no sistemático (específico), por lo que el mercado solo premia el riesgo "
                    "sistemático medido por Beta. Si una empresa no transa en bolsa, se toma la Beta apalancada (Beta_L) de un comparable, "
                    "se divide por [1 + (1-t)(B/S)] para obtener la Beta pura del negocio (Beta_U) y se reapalanca con la deuda objetivo."
                ),
                "fuente": (
                    "Camila Bustos Rosas (2026), 'Teoría de mercado de capitales.pdf', láminas 37-50; y "
                    "Brealey, Myers y Allen (2010), Cap. 8 y 9 (págs. 189-225) y Cap. 19."
                ),
            },
        ],
    },
    "Desarrollo y Gestión Territorial": {
        "docente": "Prof. Claudio Mancilla",
        "tarjetas": [
            {
                "titulo": "1. Modelos Clásicos de Localización: Von Thünen y Triángulo de Weber",
                "formula": r"LR = Y(m - c) - Y \cdot t \cdot d \quad | \quad IM = \frac{\text{Peso Materias Primas Localizadas}}{\text{Peso Producto Final}}",
                "tip": (
                    "En Von Thünen la renta agrícola (LR) es un residuo tras descontar costos de transporte (Y*t*d), generando anillos concéntricos. "
                    "En Weber, si el Índice Material IM > 1 (insumos pierden peso), la planta se acerca a la materia prima; si IM < 1, "
                    "se acerca al mercado. Un sitio con mano de obra barata atrae a la firma solo si está dentro de la isodápana crítica."
                ),
                "fuente": (
                    "Néstor Duch Brown (Universitat de Barcelona), 'La_teoria_de_la_localizacion.pdf', "
                    "Sección 1.1 (Von Thünen, págs. 6-10) y Sección 1.2 (Launhardt-Weber e Isodápanas, págs. 10-16)."
                ),
            },
            {
                "titulo": "2. Competencia Espacial (Hotelling), Lugares Centrales (Christaller-Lösch) y Krugman",
                "formula": r"\text{Christaller: Umbral (Demanda mínima)} \;\text{vs.}\; \text{Rango (Distancia máxima)} \quad | \quad \text{Krugman: } p^*(x) = \frac{a W(x)}{\rho}",
                "tip": (
                    "En Hotelling (demanda inelástica en mercado lineal), dos firmas convergen al centro aunque el óptimo social sea "
                    "ubicarse en los cuartiles (1/4 y 3/4). Con productos diferenciados (D'Aspremont et al., 1979), aglomerarse desata "
                    "una guerra de precios a lo Bertrand. En Krugman (1995), la aglomeración surge de fuerzas centrípetas (encadenamientos, "
                    "mercado laboral conjunto, spillovers) frente a fuerzas centrífugas (rentas del suelo, congestión)."
                ),
                "fuente": (
                    "Néstor Duch Brown, 'La_teoria_de_la_localizacion.pdf', Sección 1.3 (Hotelling, págs. 17-19), "
                    "Sección 1.4 (Christaller-Lösch, págs. 19-23), Sección 1.5 (pág. 24) y Sección 2.3-3 (Krugman, págs. 42-66)."
                ),
            },
            {
                "titulo": "3. Indicadores de Ordenamiento Territorial: Primacía, Guttman/Rondinelli y Aislamiento",
                "formula": r"IP = \frac{P_1}{P_2 + P_3 + P_4} \quad | \quad \text{Matriz de Rondinelli: } 1 = \text{Presente},\; 0 = \text{Ausente}",
                "tip": (
                    "Un Índice de Primacía alto refleja macrocefalia urbana en la comuna o ciudad principal. "
                    "Para construir la Escala de Guttman / Matriz de Rondinelli en las 10 comunas más pobladas (mínimo 7 variables), "
                    "las variables elegidas deben mostrar diferencias reales entre comunas (si todas tienen 1, debes cambiar la variable)."
                ),
                "fuente": (
                    "Prof. Claudio Mancilla (2024/2026), '06 OT 2024.pdf' (láminas 10-15), 'Unidad 5. Ordenamiento Territorial.pdf' (pág. 1) "
                    "y 'Ejemplo Matriz Rondinelli OT.xlsx'; y SUBDERE-CEPAL (2011), 'PROT', págs. 11-22."
                ),
            },
            {
                "titulo": "4. Redes Empresariales (Dini 2010), UCINET y Cadenas de Valor",
                "formula": r"\text{Densidad Red Dirigida} = \frac{L}{N(N - 1)} \quad (\text{con diagonal } A_{ii} = 0)",
                "tip": (
                    "En el trabajo de campo de Cadenas de Valor y Redes (Control 4), entrevista a 3 actores de al menos 2 eslabones "
                    "(1 gremio + 2 empresas). Regla metodológica del profesor: jamás sugieras que 'debe existir un clúster' ni hables "
                    "de 'debilidades'; pregunta por 'desafíos o aspectos por fortalecer'."
                ),
                "fuente": (
                    "Marco Dini (2010), 'Competitividad, redes de empresas y cooperación empresarial' (CEPAL); "
                    "Prof. Claudio Mancilla (2026), 'Unidad 5. Redes y Cadena de Valor.dcx.pdf', págs. 1-4; y '20210827 MIPE y Ecosistema en Los Lagos.pdf', págs. 6-18."
                ),
            },
        ],
    },
    "Gestión Tributaria para la Toma de Decisiones": {
        "docente": "Prof. RVS",
        "tarjetas": [
            {
                "titulo": "1. Determinación Mensual del IVA, Boletas y Crédito Fiscal (D.L. N° 825)",
                "formula": r"\text{Neto Boleta} = \frac{\text{Total Bruto}}{1,19} \quad | \quad \text{Remanente UTM} = \frac{\text{Remanente CLP}}{\text{UTM}_{\text{mes declaración}}}",
                "tip": (
                    "Desde la Ley N° 21.420 (2023), todos los servicios remunerados son afectos a IVA salvo exención expresa (como Sociedades "
                    "de Profesionales o educación/salud). El IVA en la compra de automóviles o station wagons NO da derecho a crédito fiscal "
                    "(Art. 23 N° 4 D.L. 825) y constituye un mayor costo o gasto ('IVA no recuperable'), a diferencia de un furgón de reparto o grúa horquilla."
                ),
                "fuente": (
                    "Prof. RVS (2026), 'Apunte IVA 2026.pdf' (págs. 1-8), 'IVA y Toma de Decisiones.pdf' (págs. 1-6) "
                    "y 'Ejerc-03 / Ejerc-04 Ejercicio IVA (Datos).xlsx' (Hojas Libro Compras y Resumen IVA)."
                ),
            },
            {
                "titulo": "2. Retenciones en Formulario 29: Honorarios (2026), Remuneraciones y PPM",
                "formula": r"\text{Retención BHE 2026} = 15,25\% \quad | \quad \text{Honorario Bruto} = \frac{\text{Líquido}}{0,8475} \quad | \quad \text{Tope Gratif.} = \frac{4,75 \times IMM}{12}",
                "tip": (
                    "Las Boletas de Honorarios Electrónicas no llevan IVA, pero su retención de 2.ª Categoría (15,25% en 2026) se entera "
                    "en el código 151 del F29. El Impuesto Único de Segunda Categoría de los trabajadores se calcula sobre la Base Tributable "
                    "(Total Imponible menos AFP, Salud 7% y Seguro de Cesantía 0,6%) y se declara en el código 48 del F29."
                ),
                "fuente": (
                    "Prof. RVS (2026), 'Ejerc-02 Ejercicio IVA (Pauta) 211026 (Datos).xlsx' (Hojas L-Honor, L-Remun y Form-29) "
                    "y 'Ejerc-04 Ejercicio IVA (Datos).xlsx' (Hoja Parámetros, IMM = $553.553, Tope Gratificación = $219.115)."
                ),
            },
            {
                "titulo": "3. Infracciones y Delitos Tributarios (Art. 97 CT) y Responsabilidad Penal (Ley 20.393)",
                "formula": r"\text{Art. 97 N° 4 CT (Facturas Falsas): Multa } 50\% \text{ a } 400\% \text{ del tributo eludido} + \text{Presidio}",
                "tip": (
                    "Contabilizar facturas por servicios inexistentes (caso 'Constructora del Sur S.A. / Global SpA') obliga a revertir "
                    "el IVA Crédito Fiscal, rechaza el gasto en Renta, aplica intereses penales (1,5% mensual), configura delito tributario "
                    "doloso bajo el Art. 97 N° 4 del Código Tributario y expone a la empresa a disolución o prohibición de contratar con el "
                    "Estado bajo la Ley N° 20.393 si carece de un Modelo de Prevención de Delitos (MPD)."
                ),
                "fuente": (
                    "Prof. RVS (2026), 'Caso GTTD Emision Facturas Falsas (Datos).pdf' (págs. 1-2), "
                    "'Clase Infracciones Sanciones Delitos GTD.pdf' (láminas 4-21) y 'Clase Facultades Fiscalizadoras GTD.pdf' (láminas 4-16)."
                ),
            },
        ],
    },
    "Introducción al Deporte Paralímpico": {
        "docente": "Prof. Exal García Carrillo",
        "tarjetas": [
            {
                "titulo": "1. Deficiencias Elegibles y Clasificación Funcional (Para Atletismo vs. Para Powerlifting)",
                "formula": r"\text{Para Atletismo: Prefijos } T\text{ (Pista/Salto) y } F\text{ (Campo)} \quad | \quad \text{Para Powerlifting: Clase única por Peso Corporal}",
                "tip": (
                    "En Para Atletismo las clases agrupan por impacto funcional: F11-F13 (discapacidad visual), T35-T38 / F35-F38 (hipertonía, "
                    "ataxia o atetosis como parálisis cerebral espástica ambulatoria), y T64 (amputación transtibial unilateral con prótesis). "
                    "En cambio, World Para Powerlifting NO tiene clases por nivel de discapacidad ni permite discapacidad visual (caso Valentina): "
                    "exige deficiencia elegible en tren inferior/cadera y agrupa en una clase única dividida solo por sexo y categoría de peso."
                ),
                "fuente": (
                    "Prof. Exal García Carrillo (2026), 'Taller_II_Deporte_Paralimpico.pdf', Casos 1 (Martín), 2 (Carolina), "
                    "3 (Diego) y 4 (Valentina), págs. 1-3."
                ),
            },
            {
                "titulo": "2. Estructura de la Entrevista y Análisis Teórico (Modelos e Inclusión)",
                "formula": r"\text{Evaluación: } 60\% \text{ Informe Escrito (6 a 8 págs.)} + 40\% \text{ Exposición Oral (5 a 10 min)}",
                "tip": (
                    "El informe no debe ser una transcripción literal de las preguntas, sino una síntesis analítica organizada en los "
                    "5 bloques (Trayectoria, Discapacidad y deporte, Entorno y accesibilidad, Competición/clasificación y Reflexión) "
                    "vinculada explícitamente con al menos dos conceptos teóricos del curso (ej. inclusión vs. integración, clasificación funcional)."
                ),
                "fuente": (
                    "Prof. Exal García Carrillo (2026), 'Entrevista para deportista.pdf', Secciones 1 a 9, págs. 1-5."
                ),
            },
        ],
    },
}


# ==============================================================================
# 3. FUNCIONES DE NOMENCLATURA PERSONALIZADA Y EXTRACCIÓN GITHUB API
# ==============================================================================

EXTENSIONES_TEXTO_PERMITIDAS = (
    ".py", ".md", ".txt", ".toml", ".json", ".yaml", ".yml",
    ".css", ".html", ".js", ".rmd", ".r", ".sql", ".sh", ".csv"
)


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
    """
    Genera un nombre de archivo .txt y un encabezado interno personalizados según el ramo
    o la combinación exacta de repositorios seleccionados por el usuario.
    """
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
    """Convierte la cuadrilla bibliográfica de un ramo en texto estructurado para inyectar al .txt."""
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


@st.cache_data(ttl=300, show_spinner=False)
def listar_repositorios_usuario(usuario, token=""):
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
    return repos


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

    url_tree = f"https://api.github.com/repos/{usuario}/{nombre_repo}/git/trees/{rama}?recursive=1"
    tree_data = _github_api_get(url_tree, token=token)
    items = [x for x in tree_data.get("tree", []) if x.get("type") == "blob"]

    bloques.append("#### INVENTARIO DE ARCHIVOS:")
    for it in items:
        bloques.append(f"  - {it['path']} ({it.get('size', 0)} bytes)")
    bloques.append("")

    for it in items:
        ruta_arch = it["path"]
        if ruta_arch.lower().endswith(EXTENSIONES_TEXTO_PERMITIDAS):
            bloques.append(f"#### ARCHIVO: {nombre_repo}/{ruta_arch}")
            bloques.append("-" * 70)
            try:
                blob_url = it["url"]
                blob_json = _github_api_get(blob_url, token=token)
                contenido_b64 = blob_json.get("content", "")
                texto_decodificado = base64.b64decode(contenido_b64).decode("utf-8", errors="replace")
                bloques.append(texto_decodificado)
            except Exception as exc:
                bloques.append(f"[Aviso: No se pudo decodificar {ruta_arch}: {exc}]")
            bloques.append("\n")

    return "\n".join(bloques)


# ==============================================================================
# 4. RENDERIZADOR DE CUADRILLAS INFORMATIVAS CON CITAS DE LA LITERATURA
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
                    st.markdown(
                        f"""
                        <div class="tip-card">
                            <div class="tip-title">{t['titulo']}</div>
                            <div class="tip-body">{t['tip']}</div>
                            <div class="tip-source">Ubicación en la Literatura: {t['fuente']}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    if t.get("formula"):
                        st.latex(t["formula"])


# ==============================================================================
# 5. INTERFAZ PRINCIPAL DE USUARIO (4 PESTAÑAS)
# ==============================================================================

st.markdown(
    """
    <div class="top-banner">
        <h1>HUB DE APLICACIONES Y EXTRACTOR DE CONTEXTO ACADÉMICO POR RAMO (ULAGOS 2026)</h1>
        <p>Compilación en vivo vía API REST de GitHub con nomenclatura dinámica por asignatura y cuadrillas metodológicas referenciadas a la literatura oficial de cátedra.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### Configuración de Conexión")
    usuario_gh = st.text_input("Usuario GitHub:", value=GITHUB_USER_DEFAULT)
    token_default = ""
    try:
        token_default = st.secrets.get("GITHUB_TOKEN", "")
    except Exception:
        token_default = ""
    token_gh = st.text_input(
        "Token GitHub (Opcional para ampliar límite API):",
        value=token_default,
        type="password",
    )
    incluir_lit_en_txt = st.checkbox(
        "Incluir Cuadrilla de Literatura y Páginas Exactas dentro del .TXT descargado",
        value=True,
    )
    if st.button("Actualizar Lista de Repositorios", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

tab1, tab2, tab3, tab4 = st.tabs([
    "1. Extractor Personalizado por Ramo (GitHub API)",
    "2. Cuadrillas Informativas y Literatura Oficial",
    "3. Directorio de Plataformas Streamlit en Vivo",
    "4. Archivos de Cátedra Destilados en Repositorio",
])

# ------------------------------------------------------------------------------
# PESTAÑA 1: EXTRACTOR PERSONALIZADO POR RAMO
# ------------------------------------------------------------------------------
with tab1:
    st.markdown(
        "<div class='sec-header'>1. SELECCIÓN DE RAMOS / REPOSITORIOS Y NOMENCLATURA PERSONALIZADA</div>",
        unsafe_allow_html=True,
    )

    try:
        lista_repos = listar_repositorios_usuario(usuario_gh, token=token_gh)
    except Exception as e:
        st.error(f"No fue posible consultar la API de GitHub en este momento: {e}")
        lista_repos = []

    if lista_repos:
        mapa_objetos_repo = {r["name"]: r for r in lista_repos}
        nombres_disponibles = list(mapa_objetos_repo.keys())

        # Filtro rápido por asignatura conocida o selección libre
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
                barra = st.progress(0, text="Iniciando extracción desde GitHub API...")
                for idx, r_nom in enumerate(repos_seleccionados):
                    barra.progress(
                        (idx) / len(repos_seleccionados),
                        text=f"Extrayendo {r_nom} ({obtener_meta_repo(r_nom)['ramo']})...",
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
# PESTAÑA 2: CUADRILLAS INFORMATIVAS Y LITERATURA OFICIAL (CON PÁGINAS Y LÁMINAS)
# ------------------------------------------------------------------------------
with tab2:
    st.markdown(
        "<div class='sec-header'>2. CUADRILLAS METODOLÓGICAS, FÓRMULAS Y UBICACIÓN EXACTA EN LA LITERATURA DE CÁTEDRA</div>",
        unsafe_allow_html=True,
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
# PESTAÑA 4: ARCHIVOS DE CÁTEDRA DESTILADOS LOCALES EN EL REPOSITORIO
# ------------------------------------------------------------------------------
with tab4:
    st.markdown(
        "<div class='sec-header'>4. ARCHIVOS DE CÁTEDRA DESTILADOS ALOJADOS EN ESTE REPOSITORIO</div>",
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
            busqueda = st.text_input("Buscar término, autor o concepto dentro del archivo de cátedra:")
            if busqueda.strip():
                coincidencias = [
                    linea for linea in texto_local.splitlines()
                    if busqueda.lower() in linea.lower()
                ]
                st.write(f"Se encontraron {len(coincidencias)} líneas con '{busqueda}':")
                st.code("\n".join(coincidencias[:80]), language="text")
            else:
                with st.expander("Ver primeras líneas del archivo de cátedra", expanded=False):
                    st.code("\n".join(texto_local.splitlines()[:100]), language="text")
