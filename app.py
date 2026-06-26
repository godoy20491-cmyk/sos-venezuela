import streamlit as st
import pandas as pd
from thefuzz import fuzz

# 1. Configuración de la página
st.set_page_config(page_title="Sistema Centralizado de Cotejo", page_icon="🚨", layout="wide")

st.title("🚨 Sistema Centralizado de Cotejo - Terremoto Venezuela")
st.write("Esta plataforma lee en tiempo real los datos recopilados desde los formularios web móviles y busca coincidencias automáticamente.")

# Enlaces corregidos y estables a tu Google Sheets "BD_Terremoto_Venezuela"
URL_DESAPARECIDOS = "https://docs.google.com/spreadsheets/d/1Xv3R_uLh8HymK6pIsXg9xSjO-zEwB0T6y2G8Lp_S3Z0/gviz/tq?tqx=out:csv&sheet=Desaparecidos"
URL_HOSPITALES = "https://docs.google.com/spreadsheets/d/1Xv3R_uLh8HymK6pIsXg9xSjO-zEwB0T6y2G8Lp_S3Z0/gviz/tq?tqx=out:csv&sheet=Hospitales"

if st.button("🔄 Actualizar y Sincronizar Datos de la Nube"):
    st.cache_data.clear()

@st.cache_data
def cargar_datos(url):
    try:
        df = pd.read_csv(url)
        # Limpiar espacios en los nombres de las columnas
        df.columns = [c.strip() for c in df.columns]
        # Eliminar filas donde falten datos esenciales para evitar los "nan"
        if not df.empty:
            df = df.dropna(how='all')
        return df
    except Exception as e:
        return pd.DataFrame()

# Carga de datos desde la nube
df_desaparecidos_raw = cargar_datos(URL_DESAPARECIDOS)
df_hospitales_raw = cargar_datos(URL_HOSPITALES)

# ==========================================
# SECCIÓN DE BÚSQUEDA GENERAL
# ==========================================
st.sidebar.header("🔍 Buscador de Personas")
termino_busqueda = st.sidebar.text_input(
    "Buscar por Nombre, Apellido o Cédula:", 
    placeholder="Ej: Juan Pérez o 12345678"
).strip().lower()

# Función para filtrar dinámicamente
def filtrar_por_termino(df, termino):
    if df.empty or not termino:
        return df
    mascara = pd.Series(False, index=df.index)
    for col in df.columns:
        mascara |= df[col].astype(str).str.lower().str.contains(termino, na=False)
    return df[mascara]

# Aplicar filtros del buscador
df_desaparecidos = filtrar_por_termino(df_desaparecidos_raw, termino_busqueda)
df_hospitales = filtrar_por_termino(df_hospitales_raw, termino_busqueda)

# 2. Mostrar contadores principales
col1, col2 = st.columns(2)
with col1:
    st.metric("Total Desaparecidos Reportados", len(df_desaparecidos))
with col2:
    st.metric("Total Heridos Registrados en Hospitales", len(df_hospitales))

st.markdown("---")

# 3. Sección de Coincidencias Inteligentes
st.subheader("📊 Posibles Coincidencias Detectadas")

coincidencias = []

if not df_desaparecidos_raw.empty and not df_hospitales_raw.empty:
    col_nom_des = df_desaparecidos_raw.columns[1] if len(df_desaparecidos_raw.columns) > 1 else df_desaparecidos_raw.columns[0]
    col_nom_hosp = df_hospitales_raw.columns[1] if len(df_hospitales_raw.columns) > 1 else df_hospitales_raw.columns[0]
    col_lugar_hosp = df_hospitales_raw.columns[2] if len(df_hospitales_raw.columns) > 2 else df_hospitales_raw.columns[-1]

    for _, des in df_desaparecidos_raw.iterrows():
        nombre_des = str(des[col_nom_des]).strip()
        nombre_hosp_original = str(des[df_desaparecidos_raw.columns[2]]).strip() if len(df_desaparecidos_raw.columns) > 2 else ""
        
        # Combinar si el formulario separa nombre y apellido
        if nombre_hosp_original and nombre_hosp_original.lower() != 'nan':
            nombre_des = f"{nombre_des} {nombre_hosp_original}"

        if nombre_des.lower() == 'nan' or not nombre_des:
            continue

        for _, hosp in df_hospitales_raw.iterrows():
            nombre_hosp = str(hosp[col_nom_hosp]).strip()
            apellido_hosp = str(hosp[df_hospitales_raw.columns[2]]).strip() if len(df_hospitales_raw.columns) > 2 else ""
            
            if apellido_hosp and apellido_hosp.lower() != 'nan':
                nombre_hosp = f"{nombre_hosp} {apellido_hosp}"
                
            lugar = str(hosp.iloc[-1]).strip() # Toma la última columna como ubicación si varía
            
            if nombre_hosp.lower() == 'nan' or not nombre_hosp:
                continue
            
            score = fuzz.token_sort_ratio(nombre_des.lower(), nombre_hosp.lower())
            
            if score >= 70: # Umbral optimizado para nombres compuestos
                if termino_busqueda:
                    if (termino_busqueda not in nombre_des.lower() and 
                        termino_busqueda not in nombre_hosp.lower()):
                        continue
                
                coincidencias.append({
                    "Nombre en Reporte": nombre_des,
                    "Nombre en Hospital": nombre_hosp,
                    "Detalles / Ubicación": lugar,
                    "Similitud": f"{score}%"
                })

if coincidencias:
    df_coincide = pd.DataFrame(coincidencias)
    st.dataframe(df_coincide, use_container_width=True)
else:
    st.info("No se detectan coincidencias bajo el umbral actual.")

st.markdown("---")

# 4. Sección de Listas Completas de Registros
st.subheader("📋 Listas de Personas Registradas en el Sistema")

tab1, tab2 = st.tabs(["👤 Desaparecidos Reportados", "🏥 Pacientes en Hospitales"])

with tab1:
    if not df_desaparecidos.empty:
        col_nom = df_desaparecidos.columns[1] if len(df_desaparecidos.columns) > 1 else df_desaparecidos.columns[0]
        st.dataframe(df_desaparecidos.sort_values(by=col_nom, ascending=True), use_container_width=True, hide_index=True)
    else:
        st.warning("No hay registros que coincidan.")

with tab2:
    if not df_hospitales.empty:
        col_nom_h = df_hospitales.columns[1] if len(df_hospitales.columns) > 1 else df_hospitales.columns[0]
        st.dataframe(df_hospitales.sort_values(by=col_nom_h, ascending=True), use_container_width=True, hide_index=True)
    else:
        st.warning("No hay registros que coincidan.")
