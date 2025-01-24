import streamlit as st

from google.cloud import bigquery

from google.oauth2 import service_account

import pandas as pd
import os
import json
import io
import re

# Ajustar la ruta a las credenciales

credentials_json = os.environ.get("BIGQUERY")
if credentials_json is None:
    raise ValueError("El secret 'BIGQUERY' no está configurado en el entorno.")

credentials_dict = json.loads(credentials_json)
credentials = service_account.Credentials.from_service_account_info(credentials_dict)

client = bigquery.Client(credentials=credentials)


# Inicializar `results_df` en `st.session_state` si no existe
if 'results_df' not in st.session_state:
    st.session_state['results_df'] = pd.DataFrame()

# Ajustar la ruta a las credenciales

credentials_json = os.environ.get("BIGQUERY")
if credentials_json is None:
    raise ValueError("El secret 'BIGQUERY' no está configurado en el entorno.")

credentials_dict = json.loads(credentials_json)
credentials = service_account.Credentials.from_service_account_info(credentials_dict)

client = bigquery.Client(credentials=credentials)

# Función para aplicar colores condicionales
def color_text(text, color):
    return f"<span style='color:{color};'>{text}</span>"

# Actualizar resultados en el DataFrame global
def actualizar_resultados(tabla_id, prueba, valor):
    if 'results_df' not in st.session_state:
        st.session_state['results_df'] = pd.DataFrame()
    df = st.session_state['results_df']
    df.loc[tabla_id, prueba] = valor
    st.session_state['results_df'] = df

# Limpia HTML de las celdas del DataFrame
def limpiar_html_df(df):
    return df.applymap(lambda x: re.sub(r"<.*?>", "", x) if isinstance(x, str) else x)

# Función para guardar resultados en Excel
def guardar_como_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=True, sheet_name='Resultados')
    processed_data = output.getvalue()
    return processed_data

# Calcular totales de campos iguales y diferentes
def calcular_totales(df):
    df["Total Campos Iguales"] = df["Tipos de campos"].apply(lambda x: x.count("es igual") if isinstance(x, str) else 0)
    df["Total Campos Diferentes"] = df["Tipos de campos"].apply(lambda x: x.count("difiere") if isinstance(x, str) else 0)
    return df

# Mostrar resultados acumulados y tabla pivot
def mostrar_tabla_pivot():
    if st.session_state['results_df'].empty:
        st.warning("No hay resultados que mostrar.")
        return

    # Limpiar HTML del DataFrame y calcular totales
    df_limpio = limpiar_html_df(st.session_state['results_df'])
    df_con_totales = calcular_totales(df_limpio)

    # Mostrar tabla pivot con totales
    st.write("### Resumen de resultados")
    st.dataframe(df_con_totales[["Total Campos Iguales", "Total Campos Diferentes"]])

    # Expansor para mostrar detalles completos
    with st.expander("Ver detalles completos"):
        st.dataframe(df_con_totales)

    # Descargar resultados
    output = guardar_como_excel(df_con_totales)
    st.download_button(
        label="Descargar resultados en Excel",
        data=output,
        file_name="resultados_limpios.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )




# Función de análisis: Número de campos
def obtener_numero_campos(client, tablas):
    for t in tablas:
        tabla = client.get_table(t)
        num_campos = len(tabla.schema)
        texto = color_text(f"{num_campos} campos", "green")
        actualizar_resultados(t, "Número de campos", texto)

# Verificar tipos de campos con comparación
def verificar_tipos_campos(client, tablas):
    tablas_campos = {t: {campo.name: campo.field_type for campo in client.get_table(t).schema} for t in tablas}
    all_campos = set().union(*[set(campos.keys()) for campos in tablas_campos.values()])
    iguales, diferencias = [], []

    for campo in all_campos:
        tipos_por_tabla = {t: tablas_campos[t].get(campo, None) for t in tablas}
        tipos_unicos = set(tipos_por_tabla.values())
        if len(tipos_unicos) == 1:
            iguales.append(color_text(f"Campo '{campo}' es igual en todas las tablas: {list(tipos_unicos)[0]}", "green"))
        else:
            detalles = ", ".join([f"{t}: {tipo if tipo else 'No existe'}" for t, tipo in tipos_por_tabla.items()])
            diferencias.append(color_text(f"Campo '{campo}' difiere: {detalles}", "red"))

    resultado_final = "Campos iguales:<br>" + "<br>".join(iguales) + "<br><br>Campos diferentes:<br>" + "<br>".join(diferencias)
    for t in tablas:
        actualizar_resultados(t, "Tipos de campos", resultado_final)

# Consultar campos enmascarados
def consultar_campos_enmascarados(client, tablas):
    for t in tablas:
        tabla = client.get_table(t)
        campos_enmascarados = [campo for campo in tabla.schema if campo.policy_tags is not None]
        texto = color_text("No se encontraron campos con políticas de enmascaramiento", "green") if not campos_enmascarados else color_text(f"Total de campos: {len(campos_enmascarados)}", "red")
        actualizar_resultados(t, "Campos enmascarados", texto)

# Nulos y requeridos
def contar_nulos_y_requeridos(client, tablas):
    for t in tablas:
        tabla = client.get_table(t)
        cols = {c.name: c.mode for c in tabla.schema}
        nulos = [col for col, mode in cols.items() if mode == 'NULLABLE']
        texto = color_text(f"NULLABLE: {len(nulos)} ({', '.join(nulos)})", "red") if nulos else color_text("No hay columnas NULLABLE", "green")
        actualizar_resultados(t, "Nulos y requeridos", texto)

# Peso de la tabla
def obtener_peso_tabla(client, tablas):
    for t in tablas:
        tabla = client.get_table(t)
        texto = color_text(f"{tabla.num_rows} filas, {tabla.num_bytes} bytes", "green")
        actualizar_resultados(t, "Peso de la tabla", texto)

# Primer registro
def obtener_primer_registro(client, tablas, columna_timestamp):
    for t in tablas:
        consulta = f"SELECT MIN({columna_timestamp}) AS primer_registro FROM `{t}`"
        res = client.query(consulta).result()
        primer_registro = list(res)[0].primer_registro
        texto = color_text(f"Primer registro: {primer_registro}", "green") if primer_registro else color_text("No se encontró un registro", "red")
        actualizar_resultados(t, "Primer registro", texto)

# Último registro
def obtener_ultimo_registro(client, tablas, columna_timestamp):
    for t in tablas:
        consulta = f"SELECT MAX({columna_timestamp}) AS ultimo_registro FROM `{t}`"
        res = client.query(consulta).result()
        ultimo_registro = list(res)[0].ultimo_registro
        texto = color_text(f"Último registro: {ultimo_registro}", "green") if ultimo_registro else color_text("No se encontró un registro", "red")
        actualizar_resultados(t, "Último registro", texto)

# Duplicados
def verificar_duplicados(client, tablas):
    for t in tablas:
        tabla = client.get_table(t)
        required_columns = [c.name for c in tabla.schema if c.mode == "REQUIRED"]
        if not required_columns:
            actualizar_resultados(t, "Duplicados", color_text("No existen columnas REQUIRED", "red"))
            continue

        consulta = f"""
        SELECT COUNT(*) AS duplicados
        FROM (
            SELECT {', '.join(required_columns)}, COUNT(*) AS c
            FROM `{t}`
            GROUP BY {', '.join(required_columns)}
            HAVING c > 1
        )
        """
        res = client.query(consulta).result()
        duplicados = list(res)[0].duplicados
        texto = color_text(f"Duplicados encontrados: {duplicados}", "red") if duplicados > 0 else color_text("No hay duplicados", "green")
        actualizar_resultados(t, "Duplicados", texto)

# Función principal para mostrar análisis
def mostrar_analisis_bigquery():
    st.title("TestDataLab")
    st.sidebar.title("Opciones de Análisis")

    # Selección de tablas y análisis
    num_tablas = st.sidebar.selectbox("¿Cuántas tablas desea analizar?", [1, 2, 3, 4], index=0)
    tablas = [st.sidebar.text_input(f"Tabla {i+1}:", key=f"tabla_{i}") for i in range(num_tablas)]
    tablas = [t for t in tablas if t]

    if not tablas:
        st.warning("Por favor, ingrese al menos una tabla.")
        return

    ejecutar_num_campos = st.sidebar.checkbox("Número de campos")
    ejecutar_tipos_campos = st.sidebar.checkbox("Verificar tipos de campos")
    ejecutar_enmascarados = st.sidebar.checkbox("Campos enmascarados")
    ejecutar_nulos_req = st.sidebar.checkbox("Nulos y requeridos")
    ejecutar_peso = st.sidebar.checkbox("Peso de la tabla")
    ejecutar_primer_reg = st.sidebar.checkbox("Primer registro")
    ejecutar_ultimo_reg = st.sidebar.checkbox("Último registro")
    ejecutar_duplicados = st.sidebar.checkbox("Duplicados")

    # Selección de columna timestamp
    columna_timestamp = None
    if ejecutar_primer_reg or ejecutar_ultimo_reg:
        timestamp_cols = {campo.name for tabla in tablas for campo in client.get_table(tabla).schema if campo.field_type in ["TIMESTAMP", "DATETIME"]}
        columna_timestamp = st.sidebar.selectbox("Columna de timestamp:", list(timestamp_cols)) if timestamp_cols else None

    # Ejecutar análisis
    if st.sidebar.button("Ejecutar análisis"):
        if ejecutar_num_campos:
            obtener_numero_campos(client, tablas)
        if ejecutar_tipos_campos:
            verificar_tipos_campos(client, tablas)
        if ejecutar_enmascarados:
            consultar_campos_enmascarados(client, tablas)
        if ejecutar_nulos_req:
            contar_nulos_y_requeridos(client, tablas)
        if ejecutar_peso:
            obtener_peso_tabla(client, tablas)
        if ejecutar_primer_reg and columna_timestamp:
            obtener_primer_registro(client, tablas, columna_timestamp)
        if ejecutar_ultimo_reg and columna_timestamp:
            obtener_ultimo_registro(client, tablas, columna_timestamp)
        if ejecutar_duplicados:
            verificar_duplicados(client, tablas)

    # Mostrar resultados acumulados y botón de refrescar
    if not st.session_state['results_df'].empty:
        mostrar_tabla_pivot()
        if st.button("Refresh"):
            st.session_state['results_df'] = pd.DataFrame()
            st.rerun()

# Ejecutar análisis
mostrar_analisis_bigquery()

