import streamlit as st
import pandas as pd
from thefuzz import fuzz

# 1. Configuración de la página
st.set_page_config(page_title="Sistema Centralizado de Cotejo", page_icon="🚨", layout="wide")

st.title("🚨 Sistema Centralizado de Cotejo - Terremoto Venezuela")
st.write("Esta plataforma lee en tiempo real los datos recopilados en la nube y busca coincidencias automáticamente.")

# ENLACES CORREGIDOS CON TU ID REAL DE GOOGLE SHEETS
URL_DESAPARECIDOS = "https://docs.google.com/spreadsheets/d/1qvqPo-D5VtPIGqCgtWCvoJGyL5xSrNCbY8ADmo_pmt4/export?format=csv&sheet=Form_Responses"
URL_HOSPITALES = "https://docs.google.com/spreadsheets/d/1qvqPo-D5VtPIGqCgtWCvoJGyL5xSrNCbY8ADmo_pmt4/export?format=csv&sheet=PestañaHospitales"

if st.button("🔄 Actualizar y Sincronizar Datos de la Nube"):
    st.cache_data.clear()

@st.cache_data
def cargar_datos(url):
    try:
        df = pd.read_csv(url)
        df.columns = [c.strip() for c in df.columns]
        df = df.dropna(how='all')
        df = df.fillna("")
        return df
    except Exception as e:
        return pd.DataFrame()

# Carga de datos base
df_desaparecidos_raw = cargar_datos(URL_DESAPARECIDOS)
df_hospitales_raw = cargar_datos(URL_HOSPITALES)

# ==========================================
# SECCIÓN DE BÚSQUEDA GENERAL (Sidebar)
# ==========================================
st.sidebar.header("🔍 Buscador de Personas")
termino_busqueda = st.sidebar.text_input(
    "Buscar por Nombre, Apellido o Cédula:", 
    placeholder="Ej: KEKVIN ACOSTA o 11344630"
).strip().lower()

def filtrar_por_termino(df, termino):
    if df.empty or not termino:
        return df
    mascara = pd.Series(False, index=df.index)
    for col in df.columns:
        mascara |= df[col].astype(str).str.lower().str.contains(termino, na=False)
    return df[mascara]

# Filtrar datos para los contadores
df_desaparecidos_filtrados = filtrar_por_termino(df_desaparecidos_raw, termino_busqueda)
df_hospitales_filtrados = filtrar_por_termino(df_hospitales_raw, termino_busqueda)

# 2. Mostrar contadores principales dinámicos
col1, col2 = st.columns(2)
with col1:
    st.metric("Total Desaparecidos Reportados", len(df_desaparecidos_filtrados))
with col2:
    st.metric("Total Heridos Registrados en Hospitales", len(df_hospitales_filtrados))

st.markdown("---")

# 3. Sección de Coincidencias Inteligentes
st.subheader("📊 Posibles Coincidencias Detectadas")

coincidencias = []

if not df_desaparecidos_raw.empty and not df_hospitales_raw.empty:
    # Detectar la columna de nombres de desaparecidos (búsqueda flexible por palabra clave)
    col_nom_des = [c for c in df_desaparecidos_raw.columns if "nombre" in c.lower() or "persona" in c.lower()]
    col_nom_des = col_nom_des[0] if col_nom_des else df_desaparecidos_raw.columns[0]
    
    # Detectar la columna de nombres de hospitales
    col_nom_hosp = [c for c in df_hospitales_raw.columns if "nombre" in c.lower() or "persona" in c.lower()]
    col_nom_hosp = col_nom_hosp[0] if col_nom_hosp else df_hospitales_raw.columns[0]
    
    for _, des in df_desaparecidos_raw.iterrows():
        nombre_des = str(des[col_nom_des]).strip()
        if not nombre_des or nombre_des.lower() == "nan":
            continue
            
        for _, hosp in df_hospitales_raw.iterrows():
            nombre_hosp = str(hosp[col_nom_hosp]).strip()
            if not nombre_hosp or nombre_hosp.lower() == "nan":
                continue
                
            # Calcular nivel de similitud entre nombres completo
            score = fuzz.token_sort_ratio(nombre_des.lower(), nombre_hosp.lower())
            
            if score >= 70:
                if termino_busqueda:
                    match_en_datos = (termino_busqueda in nombre_des.lower() or 
                                     termino_busqueda in nombre_hosp.lower() or 
                                     termino_busqueda in str(des).lower() or 
                                     termino_busqueda in str(hosp).lower())
                    if not match_en_datos:
                        continue
                
                coincidencias.append({
                    "Nombre en Reporte Desaparecido": nombre_des,
                    "Nombre Detectado en Hospital": nombre_hosp,
                    "Similitud de Coincidencia": f"{score}%"
                })

if coincidencias:
    df_coincide = pd.DataFrame(coincidencias)
    st.dataframe(df_coincide, use_container_width=True)
else:
    st.info("No se detectan alertas de coincidencia bajo los criterios actuales.")
