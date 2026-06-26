import streamlit as st
import pandas as pd
from thefuzz import fuzz

# Configuración de la página
st.set_page_config(page_title="Sistema Centralizado de Cotejo", page_icon="🚨", layout="wide")

st.title("🚨 Sistema Centralizado de Cotejo - Terremoto Venezuela")
st.write("Esta plataforma lee en tiempo real los datos recopilados desde los formularios web móviles y busca coincidencias automáticamente.")

# ENLACES DE TU GOOGLE SHEETS (Mantén los mismos que ya tenías)
# Reemplaza estas URL con tus enlaces reales de publicación CSV si el código de tu PC tenía unos específicos
URL_DESAPARECIDOS = "https://docs.google.com/spreadsheets/d/1Xv3R_uLh8HymK6pIsXg9xSjO-zEwB0T6y2G8Lp_S3Z0/gviz/tq?tqx=out:csv&sheet=Desaparecidos](https://docs.google.com/spreadsheets/d/1Xv3R_uLh8HymK6pIsXg9xSjO-zEwB0T6y2G8Lp_S3Z0/gviz/tq?tqx=out:csv&sheet=Desaparecidos"
URL_HOSPITALES = "https://docs.google.com/spreadsheets/d/1Xv3R_uLh8HymK6pIsXg9xSjO-zEwB0T6y2G8Lp_S3Z0/gviz/tq?tqx=out:csv&sheet=Hospitales](https://docs.google.com/spreadsheets/d/1Xv3R_uLh8HymK6pIsXg9xSjO-zEwB0T6y2G8Lp_S3Z0/gviz/tq?tqx=out:csv&sheet=Hospitales"

if st.button("🔄 Actualizar y Sincronizar Datos de la Nube"):
    st.cache_data.clear()

@st.cache_data
def cargar_datos(url):
    try:
        df = pd.read_csv(url)
        # Limpieza básica de espacios y nombres de columnas
        df.columns = [c.strip() for c in df.columns]
        return df
    except Exception as e:
        return pd.DataFrame()

df_desaparecidos = cargar_datos(URL_DESAPARECIDOS)
df_hospitales = cargar_datos(URL_HOSPITALES)

# Mostrar contadores principales
col1, col2 = st.columns(2)
with col1:
    st.metric("Total Desaparecidos Reportados", len(df_desaparecidos))
with col2:
    st.metric("Total Heridos Registrados en Hospitales", len(df_hospitales))

st.markdown("---")

# --- SECCIÓN 1: COINCIDENCIAS INTELIGENTES ---
st.subheader("📊 Posibles Coincidencias Detectadas")

coincidencias = []

if not df_desaparecidos.empty and not df_hospitales.empty:
    # Ajusta los nombres de las columnas según tus formularios si es necesario
    col_nom_des = df_desaparecidos.columns[1] if len(df_desaparecidos.columns) > 1 else df_desaparecidos.columns[0]
    col_nom_hosp = df_hospitales.columns[1] if len(df_hospitales.columns) > 1 else df_hospitales.columns[0]
    col_lugar_hosp = df_hospitales.columns[2] if len(df_hospitales.columns) > 2 else df_hospitales.columns[-1]

    for _, des in df_desaparecidos.iterrows():
        nombre_des = str(des[col_nom_des]).strip()
        for _, hosp in df_hospitales.iterrows():
            nombre_hosp = str(hosp[col_nom_hosp]).strip()
            lugar = str(hosp[col_lugar_hosp]).strip()
            
            # Cálculo de similitud difusa (0 a 100)
            score = fuzz.token_sort_ratio(nombre_des.lower(), nombre_hosp.lower())
            
            if score >= 75:  # Umbral de coincidencia
                coincidencias.append({
                    "Nombre en Reporte": nombre_des,
                    "Nombre en Hospital": nombre_hosp,
                    "Ubicación / Hospital": lugar,
                    "Similitud": f"{score}%"
                })

if coincidencias:
    df_coincide = pd.DataFrame(coincidencias)
    st.dataframe(df_coincide, use_container_width=True)
else:
    st.info("No se detectan coincidencias bajo el umbral actual. Los datos ingresados no presentan similitudes directas.")

st.markdown("---")

# --- SECCIÓN 2: LISTAS COMPLETA DE REGISTROS ---
st.subheader("📋 Listas de Personas Registradas en el Sistema")

tab1, tab2 = st.tabs(["👤 Desaparecidos Reportados", "🏥 Pacientes en Hospitales"])

with tab1:
    if not df_desaparecidos.empty:
        st.write("Esta es la lista completa de personas que las familias están buscando actualmente:")
        # Ordenar alfabéticamente si es posible por la columna de nombres
        col_nom = df_desaparecidos.columns[1] if len(df_desaparecidos.columns) > 1 else df_desaparecidos.columns[0]
        df_des_ordenado = df_desaparecidos.sort_values(by=col_nom, ascending=True)
        st.dataframe(df_des_ordenado, use_container_width=True)
    else:
        st.warning("Aún no hay registros de personas desaparecidas.")

with tab2:
    if not df_hospitales.empty:
        st.write("Esta es la lista completa de pacientes ingresados en los centros de salud:")
        col_nom_h = df_hospitales.columns[1] if len(df_hospitales.columns) > 1 else df_hospitales.columns[0]
        df_hosp_ordenado = df_hospitales.sort_values(by=col_nom_h, ascending=True)
        st.dataframe(df_hosp_ordenado, use_container_width=True)
    else:
        st.warning("Aún no hay registros de pacientes en hospitales.")
