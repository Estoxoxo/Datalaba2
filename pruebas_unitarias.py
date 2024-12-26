#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 28 16:21:25 2024

@author: esteban.jimenez
"""

import streamlit as st
import pandas as pd
from utiis import upload_file



def test_campo_rfcCEP_vacio():
    df = st.session_state.get('data')
    if 'rfcCEP' in df.columns and df['rfcCEP'].isnull().all():
        return True, "Prueba de campo rfcCEP vacío", "Aprobó"
    return False, "Prueba de campo rfcCEP vacío", "Falla: rfcCEP no está vacío o no existe en el archivo."

def test_campo_con_dos_decimales(column_names):
    df = st.session_state.get('data')
    results = []
    for column_name in column_names:
        if column_name in df.columns:
            df[column_name] = df[column_name].astype(str)
            for value in df[column_name]:
                if pd.notnull(value) and '.' in value:
                    decimal_part = value.split('.')[1]
                    if len(decimal_part) != 2:
                        results.append((False, f"Prueba de campo '{column_name}' con dos decimales", f"Falla: El campo {value} no tiene exactamente 2 decimales"))
                        continue
            results.append((True, f"Prueba de campo '{column_name}' con dos decimales", "Aprobó"))
        else:
            results.append((False, f"Prueba de campo '{column_name}' con dos decimales", f"Falla: La columna '{column_name}' no está en el archivo"))
    return results

def test_campo_no_existe_SPEIIN():
    df = st.session_state.get('data')
    field_nonexistent = 'urlCEP'
    if field_nonexistent not in df.columns:
        return True, "Prueba de campo no existente en SPEIIN", "Aprobó"
    return False, "Prueba de campo no existente en SPEIIN", f"Falla: La columna '{field_nonexistent}' existe y no debería."

def test_campo_sello_vacio():
    df = st.session_state.get('data')
    if 'sello' in df.columns and df['sello'].isnull().all():
        return True, "Prueba de campo sello vacío en SPEI-OUT", "Aprobó"
    return False, "Prueba de campo sello vacío en SPEI-OUT", "Falla: La columna 'sello' contiene valores no nulos o no está en el archivo."


def automatizacion():
    st.title("TestDataLab")
    
    # Cargar el archivo y guardarlo en session_state
    upload_file(key="pruebas_unitarias_uploader")
    
    # Verificar si los datos están cargados
    if 'data' in st.session_state:
        df = st.session_state['data']
        st.write("Vista previa de los datos:")
        st.dataframe(df.head())

        # Input para columnas con decimales
        columns_input = st.text_input("Introduce los nombres de las columnas para verificar decimales, separados por comas (ej: monto, costo, precio):")
        
        # Ejecutar todas las pruebas
        results = []
        results.append(test_campo_rfcCEP_vacio())
        
        if columns_input:
            column_names = [x.strip() for x in columns_input.split(',')]
            results.extend(test_campo_con_dos_decimales(column_names))
        
        results.append(test_campo_no_existe_SPEIIN())
        results.append(test_campo_sello_vacio())

        # Presentar resultados
        result_df = pd.DataFrame(results, columns=["Resultado", "Prueba", "Detalle"])
        st.write("Resultados de las pruebas:")
        st.dataframe(result_df[['Prueba', 'Detalle']])

        # Generar y permitir descarga del HTML
        result_html = result_df.to_html(index=False)
        st.download_button(
            label="Descargar resultados como HTML",
            data=result_html,
            file_name="resultados_pruebas_unitarias.html",
            mime="text/html"
        )

        # Mostrar mensaje final según los resultados
        if all(result[0] for result in results):
            st.success("Todas las pruebas pasaron exitosamente.")
        else:
            st.error("Algunas pruebas fallaron. Revisa la tabla de resultados para más detalles.")

