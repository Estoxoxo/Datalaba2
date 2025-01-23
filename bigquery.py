import streamlit as st

from google.cloud import bigquery

from google.oauth2 import service_account

import pandas as pd
import os
import json


# Ajustar la ruta a las credenciales

credentials_json = os.environ.get("BIGQUERY")
if credentials_json is None:
    raise ValueError("El secret 'BIGQUERY' no está configurado en el entorno.")

credentials_dict = json.loads(credentials_json)
credentials = service_account.Credentials.from_service_account_info(credentials_dict)

client = bigquery.Client(credentials=credentials)



# Inicializar DataFrame de resultados si no existe

if 'results_df' not in st.session_state:

    st.session_state.results_df = pd.DataFrame()



def color_text(text, color):

    return f'<span style="color:{color}">{text}</span>'



def actualizar_resultados(tabla_id, prueba, valor_html):

    df = st.session_state.results_df

    if tabla_id not in df.index:

        df.loc[tabla_id, prueba] = valor_html

    else:

        df.at[tabla_id, prueba] = valor_html

    st.session_state.results_df = df



def todas_iguales(valores):

    return len(set(valores)) == 1



def obtener_numero_campos(client, tablas):

    for t in tablas:

        tabla = client.get_table(t)

        num_campos = len(tabla.schema)

        actualizar_resultados(t, "Número de campos", color_text(f"{num_campos} campos", "black"))



def verificar_tipos_campos_multiple(esquemas, tablas):

    tablas_campos = {}

    for t, esquema in zip(tablas, esquemas):

        tablas_campos[t] = {c.name: c.field_type for c in esquema}



    all_fields = set()

    for m in tablas_campos.values():

        all_fields.update(m.keys())



    diferencias = []

    for field in all_fields:

        tipos_por_tabla = {}

        for t in tablas:

            if field in tablas_campos[t]:

                tipos_por_tabla[t] = tablas_campos[t][field]

            else:

                tipos_por_tabla[t] = None

        tipos_set = set(tipos_por_tabla.values())

        if len(tipos_set) > 1:

            detalle = ", ".join([f"{tt}: {tp if tp else 'No existe'}" for tt, tp in tipos_por_tabla.items()])

            diferencias.append(f"Campo '{field}' difiere: {detalle}")



    if len(diferencias) == 0:

        return color_text("Todos los tipos coinciden (100%)", "green")

    else:

        return color_text("Diferencias en tipos de campos:<br>" + "<br>".join(diferencias), "red")



def verificar_tipos_campos(client, tablas, esquemas):

    if len(tablas) == 1:

        t = tablas[0]

        actualizar_resultados(t, "Verificar tipos de campos", color_text("Sin comparación (solo una tabla)", "black"))

    else:

        resultado = verificar_tipos_campos_multiple(esquemas, tablas)

        for t in tablas:

            actualizar_resultados(t, "Verificar tipos de campos", resultado)



def consultar_campos_enmascarados(client, tablas):

    resultados_tablas = {}

    for t in tablas:

        tabla = client.get_table(t)

        campos_string = [campo for campo in tabla.schema if campo.field_type == 'STRING']



        if not campos_string:

            resultados_tablas[t] = {"total": 0, "detalles": {}}

            continue



        partes_consulta = []

        for campo in campos_string:

            parte = f"""

            SELECT

                '{campo.name}' AS nombre_campo,

                COUNTIF({campo.name} LIKE '%XXXX%') AS conteo_enmascarado

            FROM `{t}`

            """

            partes_consulta.append(parte)



        consulta = "\nUNION ALL\n".join(partes_consulta)

        res = client.query(consulta).result()



        total_enmascarado = 0

        detalles = {}

        for fila in res:

            total_enmascarado += fila.conteo_enmascarado

            detalles[fila.nombre_campo] = fila.conteo_enmascarado

        resultados_tablas[t] = {"total": total_enmascarado, "detalles": detalles}



    if len(tablas) == 1:

        t = tablas[0]

        total = resultados_tablas[t]["total"]

        actualizar_resultados(t, "Campos enmascarados", color_text(f"Total enmascarados: {total}", "black"))

        return



    totales = [resultados_tablas[t]["total"] for t in tablas]

    if not todas_iguales(totales):

        msg = "Diferencias en totales enmascarados:<br>" + "<br>".join([f"{t}: {resultados_tablas[t]['total']}" for t in tablas])

        resultado_html = color_text(msg, "red")

    else:

        # Totales iguales

        all_fields = set()

        for t in tablas:

            all_fields.update(resultados_tablas[t]["detalles"].keys())

        diferencias_campos = []

        for f in all_fields:

            vals = [resultados_tablas[t]["detalles"].get(f,0) for t in tablas]

            if not todas_iguales(vals):

                diff = "<br>".join([f"{t}: {resultados_tablas[t]['detalles'].get(f,0)}" for t in tablas])

                diferencias_campos.append(f"Campo {f} difiere:<br>{diff}")



        if len(diferencias_campos) == 0:

            resultado_html = color_text("Todos los datos enmascarados coinciden entre las tablas", "green")

        else:

            resultado_html = color_text("Diferencias en campos enmascarados:<br>" + "<br>".join(diferencias_campos), "red")



    for t in tablas:

        actualizar_resultados(t, "Campos enmascarados", resultado_html)



def contar_nulos_y_requeridos(client, tablas, columnas_requeridas):

    resultados = {}

    for t in tablas:

        tabla = client.get_table(t)

        esquema = tabla.schema

        names_esquema = [c.name for c in esquema]

        esquema_dict = {c.name:c for c in esquema}



        faltan = []

        no_requeridas = []



        for col in columnas_requeridas:

            if col not in names_esquema:

                faltan.append(col)

            else:

                if esquema_dict[col].mode == 'NULLABLE':

                    no_requeridas.append(col)



        if faltan or no_requeridas:

            resultados[t] = {"status": "error", "faltan": faltan, "no_req": no_requeridas, "nulos": {}}

        else:

            partes = [f"SUM(CASE WHEN {c} IS NULL THEN 1 ELSE 0 END) AS {c}_null_count" for c in columnas_requeridas]

            consulta = f"SELECT {', '.join(partes)} FROM `{t}`"

            res = client.query(consulta).result()

            fila = list(res)[0]



            nulos_dict = {}

            for c in columnas_requeridas:

                n = getattr(fila, f"{c}_null_count")

                nulos_dict[c] = n

            resultados[t] = {"status": "ok", "nulos": nulos_dict, "faltan": [], "no_req": []}



    if any(r["status"] == "error" for r in resultados.values()):

        mensajes = []

        for t, val in resultados.items():

            if val["status"] == "error":

                msg = f"{t}: "

                if val["faltan"]:

                    msg += f"Faltan columnas requeridas: {', '.join(val['faltan'])}. "

                if val["no_req"]:

                    msg += f"Columnas no requeridas: {', '.join(val['no_req'])}. "

                mensajes.append(msg)

            else:

                mensajes.append(f"{t}: OK")

        resultado_html = color_text("Diferencias en columnas requeridas:<br>" + "<br>".join(mensajes), "red")

    else:

        diferencias_nulos = []

        for c in columnas_requeridas:

            vals = [resultados[t]["nulos"][c] for t in tablas]

            if not todas_iguales(vals):

                diffs = "<br>".join([f"{t}: {results[t]['nulos'][c]}" for t, results in resultados.items()])

                diferencias_nulos.append(f"Columna {c} difiere en nulos:<br>{diffs}")



        if diferencias_nulos:

            resultado_html = color_text("Diferencias en nulos requeridos:<br>" + "<br>".join(diferencias_nulos), "red")

        else:

            info_nulos = []

            for c in columnas_requeridas:

                vals = [f"{t}:{resultados[t]['nulos'][c]}" for t in tablas]

                info_nulos.append(f"{c}: " + ", ".join(vals))

            resultado_html = color_text("Todas las columnas requeridas presentes y sin diferencias<br>" + "<br>".join(info_nulos), "green")



    for t in tablas:

        actualizar_resultados(t, "Nulos y requeridos", resultado_html)



def obtener_timestamp_columns(esquemas):

    ts_cols = set()

    for esquema in esquemas:

        for c in esquema:

            if c.field_type.upper() in ["TIMESTAMP", "DATETIME"]:

                ts_cols.add(c.name)

    return list(ts_cols)



def obtener_primer_registro(client, tablas, columna_timestamp):

    valores = {}

    for t in tablas:

        consulta = f"SELECT MIN({columna_timestamp}) AS primer_registro FROM `{t}`"

        res = client.query(consulta).result()

        fila = list(res)[0]

        valores[t] = fila.primer_registro



    if todas_iguales(list(valores.values())):

        resultado = color_text(f"Primer registro igual en todas las tablas: {valores[tablas[0]]}", "green")

    else:

        detalles = "<br>".join([f"{t}: {valores[t]}" for t in tablas])

        resultado = color_text("Diferencias en primer registro:<br>" + detalles, "red")



    for t in tablas:

        actualizar_resultados(t, "Primer registro", resultado)



def obtener_ultimo_registro(client, tablas, columna_timestamp):

    valores = {}

    for t in tablas:

        consulta = f"SELECT MAX({columna_timestamp}) AS ultimo_registro FROM `{t}`"

        res = client.query(consulta).result()

        fila = list(res)[0]

        valores[t] = fila.ultimo_registro



    if todas_iguales(list(valores.values())):

        resultado = color_text(f"Último registro igual en todas las tablas: {valores[tablas[0]]}", "green")

    else:

        detalles = "<br>".join([f"{t}: {valores[t]}" for t in tablas])

        resultado = color_text("Diferencias en último registro:<br>" + detalles, "red")



    for t in tablas:

        actualizar_resultados(t, "Último registro", resultado)



def obtener_peso_tabla(client, tablas):
    """
    Obtiene el número de filas y el tamaño en bytes de las tablas especificadas.

    Args:
        client: Un cliente de BigQuery.
        tablas: Una lista de identificadores de tablas.

    Returns:
        None
    """

    filas = {}  # Inicializamos el diccionario para almacenar el número de filas
    resultados = {}

    for t in tablas:
        tabla = client.get_table(t)
        job_config = bigquery.QueryJobConfig()
        job_config.dry_run = True
        query_job = client.query(f"SELECT COUNT(*) FROM `{t}`", job_config=job_config)
        stats = query_job.total_bytes_processed
        filas[t] = tabla.num_rows
        resultados[t] = {
            'num_filas': tabla.num_rows,
            'tamaño_bytes': stats
        }

    if len(tablas) > 1:
        # Comparar el número de filas y el tamaño en bytes
        diferencias_filas = any(filas[t] != filas[tablas[0]] for t in tablas[1:])
        diferencias_bytes = any(resultados[t]['tamaño_bytes'] != resultados[tablas[0]]['tamaño_bytes'] for t in tablas[1:])

        if diferencias_filas or diferencias_bytes:
            detalles = "<br>".join([f"{t}: {filas[t]} filas, {resultados[t]['tamaño_bytes']} bytes" for t in tablas])
            resultado = color_text("Diferencias en número de filas y tamaño:<br>" + detalles, "red")
        else:
            detalles = "<br>".join([f"{t}: {filas[t]} filas, {resultados[t]['tamaño_bytes']} bytes" for t in tablas])
            resultado = color_text("Número de filas y tamaño similares:<br>" + detalles, "green")
    else:
        resultado = color_text(f"{t}: {filas[t]} filas, {resultados[t]['tamaño_bytes']} bytes", "black")

    for t in tablas:
        actualizar_resultados(t, "Peso de la tabla", resultado)
        
        

def verificar_duplicados(client, tablas, llaves):

    duplicados = {}

    ll = ', '.join(llaves)

    for t in tablas:

        consulta = f"""

        SELECT COUNT(*) AS cnt

        FROM (

            SELECT {ll}, COUNT(*) c

            FROM `{t}`

            GROUP BY {ll}

            HAVING c > 1

        )

        """

        res = client.query(consulta).result()

        fila = list(res)[0]

        duplicados[t] = fila.cnt



    if len(tablas) > 1 and not todas_iguales(list(duplicados.values())):

        detalles = "<br>".join([f"{t}: {duplicados[t]}" for t in tablas])

        resultado = color_text("Diferencias en duplicados:<br>" + detalles, "red")

    else:

        resultado = color_text(", ".join([f"{t}: {duplicados[t]} duplicados" for t in tablas]), "green" if len(tablas)>1 else "black")



    for t in tablas:

        actualizar_resultados(t, "Duplicados", resultado)



def mostrar_analisis_bigquery():

    st.title("TestDataLab")

    #st.title("Validacion de Migraciaones")



    st.sidebar.title("Opciones de Análisis")

    num_tablas = st.sidebar.selectbox("¿Cuántas tablas desea analizar?", [1, 2, 3, 4], index=0)



    tablas = []

    for i in range(num_tablas):

        tabla_id_input = st.sidebar.text_input(f"Ingrese la tabla {i+1} (ej: proyecto.dataset.tabla):", key=f"tabla_{i}")

        if tabla_id_input:

            tablas.append(tabla_id_input)



    if len(tablas) < num_tablas:

        st.warning("Ingrese todas las tablas para continuar.")

        return



    # Cargar esquemas

    esquemas = []

    try:

        for t in tablas:

            tabla_obj = client.get_table(t)

            esquemas.append(tabla_obj.schema)

    except Exception as e:

        st.error(f"No se pudo obtener el esquema de una tabla: {e}")

        return



    # Checkboxes para cada función

    ejecutar_num_campos = st.sidebar.checkbox("Número de campos")

    ejecutar_tipos_campos = st.sidebar.checkbox("Verificar tipos de campos")

    ejecutar_enmascarados = st.sidebar.checkbox("Campos enmascarados")

    ejecutar_nulos_req = st.sidebar.checkbox("Nulos y requeridos")

    ejecutar_peso = st.sidebar.checkbox("Peso de la tabla")

    ejecutar_primer_reg = st.sidebar.checkbox("Primer registro")

    ejecutar_ultimo_reg = st.sidebar.checkbox("Último registro")

    ejecutar_duplicados = st.sidebar.checkbox("Duplicados")



    # Si se usan nulos y requeridos, pedir columnas requeridas

    columnas_requeridas = []

    if ejecutar_nulos_req:

        columnas_str = st.sidebar.text_input("Ingrese las columnas requeridas (separadas por comas):")

        if columnas_str:

            columnas_requeridas = [x.strip() for x in columnas_str.split(",")]



    # Si se usan primer/último registro, pedir columna timestamp

    timestamp_cols = obtener_timestamp_columns(esquemas)

    columna_timestamp = None

    if (ejecutar_primer_reg or ejecutar_ultimo_reg) and timestamp_cols:

        columna_timestamp = st.sidebar.selectbox("Seleccione la columna timestamp:", timestamp_cols)



    # Si se ejecutan duplicados, pedir llaves

    llaves = []

    if ejecutar_duplicados:

        llaves_str = st.sidebar.text_input("Ingrese las llaves primarias (separadas por comas):", "_id_fivetran")

        llaves = [x.strip() for x in llaves_str.split(",")]



    if st.sidebar.button("Ejecutar análisis"):

        if ejecutar_num_campos:

            obtener_numero_campos(client, tablas)



        if ejecutar_tipos_campos:

            verificar_tipos_campos(client, tablas, esquemas)



        if ejecutar_enmascarados:

            consultar_campos_enmascarados(client, tablas)



        if ejecutar_nulos_req and columnas_requeridas:

            contar_nulos_y_requeridos(client, tablas, columnas_requeridas)



        if ejecutar_peso:

            obtener_peso_tabla(client, tablas)



        if ejecutar_primer_reg and columna_timestamp:

            obtener_primer_registro(client, tablas, columna_timestamp)



        if ejecutar_ultimo_reg and columna_timestamp:

            obtener_ultimo_registro(client, tablas, columna_timestamp)



        if ejecutar_duplicados and llaves:

            verificar_duplicados(client, tablas, llaves)

        

        



    if not st.session_state.results_df.empty:

        st.write("### Resultados acumulados:")

        st.markdown(st.session_state.results_df.to_html(escape=False), unsafe_allow_html=True)

        html = st.session_state.results_df.to_html(escape=False)

        st.download_button(

            label="Descargar resultados en HTML",

            data=html,

            file_name="resultados.html",

            mime="text/html"

        )

    

    if st.button("Refresh", key="w_refresh_button"):

        st.session_state.results_df = pd.DataFrame()
