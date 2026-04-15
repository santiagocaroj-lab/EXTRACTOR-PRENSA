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
from concurrent.futures import ThreadPoolExecutor

# ==========================================
# 1. ESTÉTICA Y PERSONALIDAD
# ==========================================
st.set_page_config(page_title="LUCAS V2 - Alto Rendimiento", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .lucas-header {
        background: linear-gradient(90deg, #1e3a8a, #3b82f6);
        color: white; padding: 20px; border-radius: 10px;
        text-align: center; margin-bottom: 20px;
    }
    .nodal-critico { background-color: #ffe4e6 !important; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<div class='lucas-header'><h1>🤖 LUCAS V2: Extractor de Sentencias (Modo Turbo)</h1></div>", unsafe_allow_html=True)

# ==========================================
# 2. CONFIGURACIÓN TÉCNICA
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
    "Optimizando núcleos de procesamiento...",
    "Buscando co-ocurrencias críticas...",
    "Leyendo PDFs a velocidad luz...",
    "Solicitando ayuda externa de los bomberos (por si se calienta el servidor)...",
    "¿No había algo más sencillo? LUCAS dice que no.",
    "Analizando el tejido jurisprudencial..."
]

# ==========================================
# 3. EL MOTOR DE ANÁLISIS (Optimizado)
# ==========================================

def analizar_sentencia_paralelo(archivo_info):
    """Función para procesar un solo PDF (usada por el ThreadPool)"""
    ruta_pdf, nombre_archivo = archivo_info
    try:
        doc = fitz.open(ruta_pdf)
        texto_completo = ""
        paginas_encontradas = set()
        keywords_detectadas = set()
        
        for num_pag, pagina in enumerate(doc):
            contenido = pagina.get_text().lower()
            texto_completo += contenido
            for kw in KEYWORDS:
                if kw.lower() in contenido:
                    keywords_detectadas.add(kw)
                    paginas_encontradas.add(num_pag + 1)
        
        doc.close()

        if not keywords_detectadas:
            return None

        # --- ALGORITMO DE ATENCIÓN (Puntos Nodales) ---
        conteo_keywords = len(keywords_detectadas)
        es_punto_nodal = "🔥 CRÍTICO" if conteo_keywords >= 3 else "Normal"
        
        # Extraer Sentencia y Año
        match_s = re.search(r'(?i)(Sentencia\s+[TCSU]+-?\s*\d+/?\d*)', texto_completo[:5000])
        sentencia_id = match_s.group(1).upper() if match_s else nombre_archivo
        
        match_a = re.search(r'\b(199[2-9]|20[0-2][0-9])\b', texto_completo)
        anio = int(match_a.group(1)) if match_a else 0

        return {
            "Año": anio,
            "Sentencia": sentencia_id,
            "Relevancia": es_punto_nodal,
            "Keywords Halladas": conteo_keywords,
            "Puntos Nodales (Palabras)": ", ".join(list(keywords_detectadas)),
            "Páginas": ", ".join(map(str, sorted(paginas_encontradas)))
        }
    except:
        return None

# ==========================================
# 4. EJECUCIÓN PRINCIPAL
# ==========================================

if st.button("🚀 INICIAR EXTRACCIÓN TURBO"):
    TEMP_DIR = "fast_temp_lucas"
    placeholder_carga = st.empty()
    progreso = st.progress(0)
    
    try:
        # Limpieza inicial
        if os.path.exists(TEMP_DIR): shutil.rmtree(TEMP_DIR)
        os.makedirs(TEMP_DIR)

        # Descarga
        placeholder_carga.info("📡 Conectando con Google Drive...")
        gdown.download_folder(url=LINK_DRIVE, output=TEMP_DIR, quiet=True)
        
        archivos = [(os.path.join(TEMP_DIR, f), f) for f in os.listdir(TEMP_DIR) if f.lower().endswith('.pdf')]
        total = len(archivos)
        
        if total == 0:
            st.error("No se detectaron archivos. Verifica el acceso al link.")
            st.stop()

        # --- PROCESAMIENTO MULTI-HILO ---
        resultados = []
        placeholder_carga.markdown(f"### ⚡ Procesando {total} archivos en paralelo...")
        
        # Usamos 4 hilos para no saturar el servidor de Streamlit pero ir mucho más rápido
        with ThreadPoolExecutor(max_workers=4) as executor:
            for i, res in enumerate(executor.map(analizar_sentencia_paralelo, archivos)):
                if res:
                    resultados.append(res)
                # Actualizar progreso cada 10%
                progreso.progress(int((i+1)/total * 100))
                if i % 5 == 0:
                    placeholder_carga.markdown(f"### ⏳ {random.choice(FRASES_CARGA)} \n *Analizando: {i+1}/{total}*")

        if resultados:
            df = pd.DataFrame(resultados).sort_values(by="Año")
            
            # Resaltar puntos críticos
            def resaltar_nodales(val):
                color = 'background-color: #ffcccc' if val == '🔥 CRÍTICO' else ''
                return color

            st.success(f"✅ Análisis Finalizado. {len(resultados)} sentencias encontradas.")
            
            # Mostrar con estilo
            st.dataframe(df.style.applymap(resaltar_nodales, subset=['Relevancia']), use_container_width=True)

            # Descargas
            c1, c2 = st.columns(2)
            with c1:
                towrite = io.BytesIO()
                df.to_excel(towrite, index=False, engine='openpyxl')
                st.download_button("📥 Excel", towrite.getvalue(), "LUCAS_Turbo.xlsx")
            with c2:
                # PDF simple
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=10)
                pdf.cell(200, 10, txt="REPORTE LUCAS - LIBERTAD DE PRENSA", ln=1, align='C')
                for i, r in df.iterrows():
                    pdf.multi_cell(0, 10, txt=f"AÑO: {r['Año']} | {r['Sentencia']} | RELEVANCIA: {r['Relevancia']}\nKeywords: {r['Puntos Nodales (Palabras)']}\nPáginas: {r['Páginas']}\n" + "-"*40)
                st.download_button("📥 Reporte PDF", pdf.output(dest='S').encode('latin-1'), "LUCAS_Reporte.pdf")

        else:
            st.warning("No se hallaron coincidencias en los documentos analizados.")

    except Exception as e:
        st.error(f"Error en el sistema: {e}")
    finally:
        if os.path.exists(TEMP_DIR): shutil.rmtree(TEMP_DIR)
