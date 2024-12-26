#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 28 18:50:41 2024

@author: esteban.jimenez
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 28 16:22:00 2024

@author: esteban.jimenez
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 17 23:46:57 2024

@author: esteban.jimenez
"""

import streamlit as st
import pandas as pd


def upload_file(key):
    """Función para subir archivos, maneja múltiples archivos o uno solo."""
    uploaded_files = st.file_uploader(
        "Sube uno o varios archivos de datos (CSV, Parquet, JSON, Excel):", 
        type=["csv", "parquet", "json", "xlsx"], 
        accept_multiple_files=True, 
        key=key
    )
    
    if uploaded_files:
        # Si es un solo archivo, convertir a lista para unificación de lógica
        if not isinstance(uploaded_files, list):
            uploaded_files = [uploaded_files]

        # Cargar todos los archivos en un solo DataFrame concatenado
        dataframes = []
        for file in uploaded_files:
            if file.name.endswith(".csv"):
                df = pd.read_csv(file)
            elif file.name.endswith(".parquet"):
                df = pd.read_parquet(file)
            elif file.name.endswith(".json"):
                df = pd.read_json(file)
            elif file.name.endswith(".xlsx"):
                df = pd.read_excel(file)
            else:
                st.error(f"Formato no soportado: {file.name}")
                return None
            
            dataframes.append(df)

        # Concatenar todos los DataFrames en uno solo
        if dataframes:
            st.session_state['data'] = pd.concat(dataframes, ignore_index=True)
            st.success("Archivo(s) cargado(s) exitosamente.")
            return st.session_state['data']
    
    return None


