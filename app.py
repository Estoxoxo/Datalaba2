# app.py

import streamlit as st
from home import show_home
from pruebas_unitarias import automatizacion
from automatizacion_pruebas import pruebas_unitarias2
from bigquery import mostrar_analisis_bigquery

# Definir las páginas de la aplicación
PAGES = {
    "Home": show_home,
    "Automatización de Pruebas": automatizacion,
    "Pruebas Unitarias": pruebas_unitarias2,
    "Validacion de Migraciaones": mostrar_analisis_bigquery,  # Página que mostrará el análisis interactivo
}

def main():
    # Verificar si hay un parámetro de URL para seleccionar la página (opcional, depende de la lógica del proyecto)
    page = st.query_params.get("page", "Home")  # "Home" por defecto
    st.session_state.page_selector = page if page in PAGES else "Home"

    # Sidebar para la navegación
    st.sidebar.title("Navegación")
    selection = st.sidebar.radio("Ir a", list(PAGES.keys()), index=list(PAGES.keys()).index(st.session_state.page_selector))
    
    # Actualizar parámetros de URL y estado de la sesión (opcional, depende de tu lógica)
    st.query_params.page = selection
    st.session_state.page_selector = selection

    # Mostrar la página correspondiente
    PAGES[st.session_state.page_selector]()

if __name__ == "__main__":
    main()
