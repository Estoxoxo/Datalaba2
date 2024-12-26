import streamlit as st
import base64

def get_image_base64(image_path):
    """Devuelve una cadena base64 de la imagen ubicada en image_path."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def show_home():
    """Página inicial con opciones de navegación."""
    auto_pruebas_base64 = get_image_base64('/Users/esteban.jimenez/DataLab/Images/Auto_pruebas.png')
    unitarias_base64 = get_image_base64('/Users/esteban.jimenez/DataLab/Images/unitarias.png')
    Migraciaones_base64 = get_image_base64('/Users/esteban.jimenez/DataLab/Images/Bigquery.png')

    # Crear dos columnas con margen
    col1, col2,col3 = st.columns(3, gap="large")

    # Configuración de la primera columna (Automatización de Pruebas)
    with col1:
        st.markdown(
            f"""
            <div style="text-align: center;">
                <a href="?page=Automatización de Pruebas">
                    <img src="data:image/png;base64,{auto_pruebas_base64}" width="300" style="margin-bottom: 5px;">
                </a>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Configuración de la segunda columna (Pruebas Unitarias)
    with col2:
        st.markdown(
            f"""
            <div style="text-align: center;">
                <a href="?page=Pruebas Unitarias">
                    <img src="data:image/png;base64,{unitarias_base64}" width="300" style="margin-bottom: 5px;">
                </a>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        
    with col3:
         st.markdown(
                f"""
                <div style="text-align: center;">
                    <a href="?page=Validacion de Migraciaones">
                        <img src="data:image/png;base64,{Migraciaones_base64}" width="300" style="margin-bottom: 5px;">
                    </a>
                </div>
                """,
                unsafe_allow_html=True
            )
        
    
    
      
    
    
