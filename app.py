import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import re
import io
import time
import random
import os
import shutil
import gdown
from fpdf import FPDF
from datetime import date

# ==========================================
# 1. CONFIGURACIÓN ESTÉTICA Y PERSONALIDAD "LUCAS"
# ==========================================
st.set_page_config(page_title="LUCAS - Extractor Jurisprudencial", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f4f4f9; }
    .lucas-title {
        font-size: 40px; font-weight: 900; color: #1e3a8a;
        border-left: 15px solid #ffc106; padding-left: 20px;
        margin-bottom: 30px; text-transform: uppercase; font-family: 'Segoe UI', sans-serif;
    }
    .stButton>button {
        background-color: #1e3a8a; color: white; border-radius: 12px;
        height: 3em; width: 100%; font-weight: bold; border: none;
    }
    .stButton>button:hover { background-color: #ffc106; color: #1e3a8a; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<div class='lucas-title'>🤖 LUCAS: Sistema de Análisis de Libertad de Prensa</div>", unsafe_allow_html=True)

# ==========================================
# 2. DEFINICIÓN DE CRITERIOS
# ==========================================
LINK_DRIVE = "https://drive.google.com/drive/folders/1viRyVTy0sIpkxvsz5JpgoBGmDauNFXCf"

KEYWORDS = [
    "libertad de prensa", "libertad de información", "libertad de opinión",
    "prensa e información", "periodista", "comunicador social", 
    "periodista independiente", "comunicación social", "medios de comunicación",
    "periodismo", "periodismo feminista", "periodismo investigativo",
    "rectificación", "censura", "censura previa", "censura prohibida",
    "autocensura", "derecho a informar", "medios masivos", "veracidad e imparcialidad"
]

FRASES_CARGA = [
    "Descargando expedientes de la nube...",
    "Revisando palabras clave...",
    "Leyendo PDF de la Corte Constitucional...",
    "Solicitando ayuda externa de los bomberos...",
    "¿No había algo más sencillo?",
    "Organizando el universo de sentencias...",
    "LUCAS está pensando (esto es raro)..."
]

# ==========================================
# 3. FUNCIONES DE EJECUCIÓN REAL (Gdown + PyMuPDF)
# ==========================================

def extraer_info_pdf(ruta_pdf, keywords):
    """Abre un PDF físico, busca sentencias, fechas y palabras clave."""
    try:
        documento = fitz.open(ruta_pdf)
    except Exception:
        return None  # Si el archivo está corrupto, lo salta

    texto_completo = ""
    paginas_encontradas = []
    keywords_presentes = set()
    
    for i in range(len(documento)):
        pagina = documento.load_page(i)
        contenido = pagina.get_text().lower()
        texto_completo += contenido
        
        encontrado_en_pagina = False
        for kw in keywords:
            if kw.lower() in contenido:
                keywords_presentes.add(kw)
                encontrado_en_pagina = True
        
        if encontrado_en_pagina:
            paginas_encontradas.append(str(i + 1))
            
    # Lógica AND solicitada
    if "libertad de expresión" in texto_completo:
        if any(x in texto_completo for x in ["libertad de prensa", "libertad de opinión", "libertad de información"]):
            keywords_presentes.add("Lógica Especial: Libertad de Expresión + Prensa/Opinión/Info")

    if not keywords_presentes:
        return None # No cumple los requisitos, no entra al universo
    
    # Extraer un número de sentencia (Aproximación mediante Regex)
    match_sentencia = re.search(r'(?i)(Sentencia\s+[TCSU]+-?\s*\d+/?\d*)', texto_completo)
    sentencia_id = match_sentencia.group(1).upper() if match_sentencia else os.path.basename(ruta_pdf)
    
    # Extraer un año para el orden cronológico (Busca años entre 1992 y 2025)
    match_anio = re.search(r'\b(199[2-9]|20[0-2][0-9])\b', texto_completo)
    anio_referencia = int(match_anio.group(1)) if match_anio else 1900

    documento.close()
    
    return {
        "Archivo Original": os.path.basename(ruta_pdf),
        "Sentencia (Aprox)": sentencia_id,
        "Año": anio_referencia,
        "Páginas": ", ".join(paginas_encontradas),
        "Puntos Nodales": ", ".join(list(keywords_presentes))
    }

def generar_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sentencias_LUCAS')
    return output.getvalue()

def generar_pdf_reporte(df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Reporte Universo de Sentencias - LUCAS", 0, 1, 'C')
    pdf.ln(10)
    pdf.set_font("Arial", '', 10)
    for i, row in df.iterrows():
        # Limpieza de caracteres para evitar errores en FPDF
        texto_celda = f"Sentencia: {row['Sentencia (Aprox)']} | Año: {row['Año']} | Páginas: {row['Páginas']} \nKeywords: {row['Puntos Nodales']}\n" + "-"*50
        texto_celda = texto_celda.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 10, texto_celda)
    return pdf.output(dest='S').encode('latin-1')

# ==========================================
# 4. INTERFAZ Y EJECUCIÓN
# ==========================================

st.info(f"📁 Origen de Datos Configurado: {LINK_DRIVE}")

if st.button("🚀 EJECUTAR EXTRACCIÓN REAL"):
    
    placeholder_carga = st.empty()
    progreso = st.progress(0)
    
    TEMP_DIR = "temp_pdfs_lucas"
    
    try:
        # 1. Preparar directorio temporal
        if os.path.exists(TEMP_DIR):
            shutil.rmtree(TEMP_DIR)
        os.makedirs(TEMP_DIR)
        
        # 2. Descargar de Google Drive
        placeholder_carga.markdown(f"### ⏳ {FRASES_CARGA[0]} (Esto puede tardar dependiendo del tamaño)")
        progreso.progress(10)
        
        # gdown permite descargar carpetas completas usando la URL directa
        gdown.download_folder(url=LINK_DRIVE, output=TEMP_DIR, quiet=True, use_cookies=False)
        
        # 3. Procesar Archivos
        archivos_pdf = [f for f in os.listdir(TEMP_DIR) if f.lower().endswith('.pdf')]
        total_archivos = len(archivos_pdf)
        
        if total_archivos == 0:
            st.error("No se encontraron archivos PDF en el enlace proporcionado o Google Drive bloqueó la descarga.")
            st.stop()

        resultados = []
        
        for i, archivo in enumerate(archivos_pdf):
            # Animación de frases y barra de progreso real
            frase = random.choice(FRASES_CARGA[1:])
            porcentaje = int(10 + (90 * (i / total_archivos)))
            progreso.progress(porcentaje)
            placeholder_carga.markdown(f"### ⏳ {frase} \n*(Analizando {i+1} de {total_archivos} documentos)*")
            
            ruta_completa = os.path.join(TEMP_DIR, archivo)
            info = extraer_info_pdf(ruta_completa, KEYWORDS)
            
            if info:
                resultados.append(info)
                
        # 4. Finalizar Análisis
        if not resultados:
            st.warning("Se analizaron los PDFs, pero ninguno contenía las palabras clave.")
        else:
            df_resultados = pd.DataFrame(resultados)
            # Orden cronológico (del más antiguo al más reciente)
            df_resultados = df_resultados.sort_values(by='Año').reset_index(drop=True)
            
            placeholder_carga.empty()
            progreso.empty()
            
            st.success(f"✅ Análisis Completo: Se encontró el universo en {len(resultados)} sentencias.")
            
            # Mostrar Tabla
            st.table(df_resultados)
            
            # Botones de Descarga
            col1, col2 = st.columns(2)
            
            with col1:
                excel_data = generar_excel(df_resultados)
                st.download_button(
                    label="📥 Descargar Excel",
                    data=excel_data,
                    file_name=f"LUCAS_Reporte_{date.today()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
            with col2:
                pdf_data = generar_pdf_reporte(df_resultados)
                st.download_button(
                    label="📥 Descargar Reporte PDF",
                    data=pdf_data,
                    file_name=f"LUCAS_Reporte_{date.today()}.pdf",
                    mime="application/pdf"
                )
                
    except Exception as e:
        placeholder_carga.empty()
        st.error(f"Ocurrió un error crítico durante la ejecución: {e}")
        
    finally:
        # 5. Limpieza del servidor (Vital para no llenar el disco)
        if os.path.exists(TEMP_DIR):
            shutil.rmtree(TEMP_DIR)
