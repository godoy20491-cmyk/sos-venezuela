import streamlit as st
import pandas as pd
from thefuzz import fuzz
from thefuzz import process
import unicodedata

st.set_page_config(page_title="SOS Venezuela 2026 - Cotejo Centralizado", layout="wide", page_icon="🚨")

st.title("🚨 Sistema Centralizado de Cotejo - Terremoto Venezuela")
st.write("Esta plataforma lee en tiempo real los datos recopilados desde los formularios web móviles y busca coincidencias automáticamente.")

# REEMPLAZA ESTOS ENLACES CON LOS ENLACES CSV DE TU GOOGLE SHEETS PUBLICADO
URL_CSV_DESAPARECIDOS = "PEGA_AQUI_EL_PRIMER_ENLACE_CSV"
URL_CSV_HOSPITALES = "PEGA_AQUI_EL_SEGUNDO_ENLACE_CSV"

def limpiar_texto(texto):
    if pd.isna(texto): return ""
    texto = str(texto).strip().lower()
    return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

# Botón manual para refrescar datos de la nube
if st.button("🔄 Actualizar y Sincronizar Datos de la Nube"):
    st.cache_data.clear()

@st.cache_data(ttl=60) # Actualiza los datos de la nube automáticamente cada 60 segundos
def cargar_datos_nube():
    try:
        df_des = pd.read_csv(URL_CSV_DESAPARECIDOS)
        df_her = pd.read_csv(URL_CSV_HOSPITALES)
        return df_des, df_her
    except Exception as e:
        st.error("Error al conectar con la base de datos de Google Sheets. Verifica la publicación de los enlaces.")
        return None, None

df_des, df_her = cargar_datos_nube()

if df_des is not None and df_her is not None:
    # Mostrar estadísticas en tiempo real
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Total Desaparecidos Reportados", len(df_des))
    with c2:
        st.metric("Total Heridos Registrados en Hospitales", len(df_her))
        
    st.divider()
    st.subheader("📊 Posibles Coincidencias Detectadas")
    
    if len(df_des) > 0 and len(df_her) > 0:
        col_nombre_des = df_des.columns[1] 
        col_nombre_her = df_her.columns[1] 
        
        df_des['nombre_limpio'] = df_des[col_nombre_des].apply(limpiar_texto)
        df_her['nombre_limpio'] = df_her[col_nombre_her].apply(limpiar_texto)
        
        coincidencias = []
        umbral = 75
        
        for idx, fila_des in df_des.iterrows():
            nom_des = fila_des['nombre_limpio']
            if not nom_des: continue
                
            resultado = process.extractOne(nom_des, df_her['nombre_limpio'].tolist(), scorer=fuzz.token_sort_ratio)
            
            if resultado and resultado[1] >= umbral:
                nombre_coincidente, puntuacion = resultado[0], resultado[1]
                datos_herido = df_her[df_her['nombre_limpio'] == nombre_coincidente].iloc[0]
                
                info = {
                    'Desaparecido Buscado': fila_des[col_nombre_des],
                    'Paciente Encontrado': datos_herido[col_nombre_her],
                    'Certeza': f"{puntuacion}%"
                }
                
                for col in df_her.columns:
                    if col != 'nombre_limpio' and col != col_nombre_her:
                        info[f"Hosp: {col}"] = datos_herido[col]
                        
                coincidencias.append(info)
                
        if coincidencias:
            df_final = pd.DataFrame(coincidencias)
            st.dataframe(df_final, use_container_width=True)
        else:
            st.info("No se detectan coincidencias bajo el umbral actual. Los datos ingresados no presentan similitudes directas.")
    else:
        st.warning("Esperando que los voluntarios ingresen registros en los formularios para iniciar el cotejo.")
