

import streamlit as st
import pandas as pd
from datetime import datetime
import re
from io import StringIO, BytesIO
import time

# Asumiendo que se han importado previamente las funciones necesarias de otro archivo
# O, si son definidas aquí, asegurarse de incluirlas correctamente en este archivo.

def pruebas_unitarias2():
    # Funciones para extraer prefijo, sufijo y fecha
    def extraer_prefijo(nombre_archivo):
        return re.split(r'[-_]', nombre_archivo)[0]

    def extraer_sufijo(nombre_archivo):
        partes = re.split(r'[-_]', nombre_archivo)
        if len(partes) > 2:
            return partes[-2]
        else:
            st.error("El archivo no tiene suficiente información para extraer el sufijo.")
            return None

    def extraer_fecha(nombre_archivo):
        match = re.search(r'(\d{2}-\d{2}-\d{4})|(\d{8})', nombre_archivo)
        if match:
            return match.group(0)
        else:
            #st.error(f"El archivo '{nombre_archivo}' no contiene una fecha válida.")
            return None

    # Función para validar archivo
    def validar_archivo_nombre(archivo):
        nombre_archivo = archivo.name
        prefijo = extraer_prefijo(nombre_archivo)
        sufijo = extraer_sufijo(nombre_archivo)
        fecha = extraer_fecha(nombre_archivo)
        
        if prefijo and sufijo and fecha:
            st.success(f"Archivo cargado correctamente.\nPrefijo: {prefijo}\nSufijo: {sufijo}\nFecha: {fecha}")
       
        
        return prefijo, sufijo, fecha

    # Inicialización del estado del DataFrame
    if 'original_df' not in st.session_state:
        st.session_state.original_df = None
    if 'final_df' not in st.session_state:
        st.session_state.final_df = None
    if 'df_seleccionado' not in st.session_state:
        st.session_state.df_seleccionado = None
    if 'columnas_seleccionadas' not in st.session_state:
        st.session_state.columnas_seleccionadas = False




    # Inicialización del estado del DataFrame
    if 'original_df' not in st.session_state:
        st.session_state.original_df = None
    if 'final_df' not in st.session_state:
        st.session_state.final_df = None
    if 'df_seleccionado' not in st.session_state:
        st.session_state.df_seleccionado = None


    if 'guardar_csv' not in st.session_state:
        st.session_state.guardar_csv = False
    if 'guardar_excel' not in st.session_state:
        st.session_state.guardar_excel = False
    if 'guardar_json' not in st.session_state:
        st.session_state.guardar_json = False
    if 'guardar_parquet' not in st.session_state:
        st.session_state.guardar_parquet = False
        
    if 'ingresar_mayusculas' not in st.session_state:
        st.session_state.ingresar_mayusculas = False
    if 'datos_parceados' not in st.session_state:
        st.session_state.datos_parceados = False
    if 'valores_nulos' not in st.session_state:
        st.session_state.valores_nulos = False
    if 'caracteres_especiales' not in st.session_state:
        st.session_state.caracteres_especiales = False
    if 'borrar_columna' not in st.session_state:
        st.session_state.borrar_columna = False
    if 'validar_esquema' not in st.session_state:
        st.session_state.validar_esquema = False
    if 'cantidad_datos' not in st.session_state:
        st.session_state.cantidad_datos = False
    if 'validacion_data' not in st.session_state:
        st.session_state.validacion_data = False
        
        
    if 'montos_negativos' not in st.session_state:
        st.session_state.montos_negativos = False
        
    if 'montos_en_cero' not in st.session_state:
        st.session_state.montos_en_cero = False
        
    if 'fecha_usuario' not in st.session_state:
        st.session_state.fecha_usuario = False




    # Subida de archivos y creación de DataFrame
    st.header("TestDataLab")
    archivos_subidos = st.file_uploader("Sube uno o varios archivos de datos (CSV, Parquet, JSON, Excel):", type=["csv", "parquet", "json", "xlsx"], accept_multiple_files=True,key="multiple")

    # Mostrar opciones solo cuando se carga un archivo por primera vez
    if archivos_subidos and st.session_state.original_df is None:
        # Listas de opciones para encoding, delimitador y decimales
        encodings = ['utf-8', 'latin1', 'ascii', 'utf-16']
        delimitadores = [',', ';', '|', '\t']
        decimales = ['.', ',']

        nombres_archivos = [archivo.name for archivo in archivos_subidos]
        
        # Mostrar la lista de archivos subidos y permitir seleccionar uno para trabajar
        archivo_seleccionado = st.selectbox("Selecciona el archivo con el que deseas trabajar", nombres_archivos)
        
        if archivo_seleccionado:
            archivo = next(archivo for archivo in archivos_subidos if archivo.name == archivo_seleccionado)
            
            prefijo, sufijo, fecha = validar_archivo_nombre(archivo)
            file_type = archivo.name.split('.')[-1]

            # Opciones adicionales para la carga de archivos CSV
            if file_type == 'csv':
                delimitador = st.selectbox("Selecciona el delimitador del archivo CSV:", delimitadores)
                encoding = st.selectbox("Selecciona el encoding:", encodings)
                decimal = st.selectbox("Selecciona el símbolo decimal:", decimales)
                try:
                    st.session_state.original_df = pd.read_csv(archivo, delimiter=delimitador, encoding=encoding, decimal=decimal, low_memory=False)
                except Exception as e:
                    st.error(f"Error al cargar el archivo CSV: {str(e)}")
            elif file_type == 'xlsx':


                decimal = st.selectbox("Selecciona el símbolo decimal:", decimales)
                
                try:
                    st.session_state.original_df = pd.read_excel(archivo, decimal=decimal)
                except Exception as e:
                    st.error(f"Error al cargar el archivo Excel: {str(e)}")
            elif file_type == 'json':
                encoding = st.selectbox("Selecciona el encoding:", encodings)

                try:
                    st.session_state.original_df = pd.read_json(archivo, encoding=encoding)
                except Exception as e:
                    st.error(f"Error al cargar el archivo JSON: {str(e)}")
            elif file_type == 'parquet':
                try:
                    st.session_state.original_df = pd.read_parquet(archivo)
                except Exception as e:
                    st.error(f"Error al cargar el archivo Parquet: {str(e)}")

            # Inicializar el DataFrame final si aún no está definido
            if st.session_state.final_df is None or st.session_state.final_df.empty:
                st.session_state.final_df = st.session_state.original_df.copy()
                with st.spinner('Se está Cargando el Archivo'):
                    time.sleep(5)
                    st.success('Puedes ver y seleccionar columnas del archivo cargado')
                    st.dataframe(st.session_state.final_df)
                    

    # Si el usuario selecciona columnas, las almacenamos en session_state
    if st.session_state.original_df is not None:
        with st.expander("Seleccionar columnas"):
            lista_columnas = st.text_input("Introduce una lista de columnas separadas por comas (ejemplo: columna1, columna2, columna3):")
            if lista_columnas:
                columnas = [col.strip() for col in lista_columnas.split(',')]
                columnas_validas = [col for col in columnas if col in st.session_state.final_df.columns]
                columnas_invalidas = [col for col in columnas if col not in st.session_state.final_df.columns]

                if columnas_invalidas:
                    st.error(f"Las siguientes columnas no existen en el DataFrame: {', '.join(columnas_invalidas)}")
                
                if columnas_validas:
                    df_seleccionado = st.session_state.final_df[columnas_validas]
                    st.write(f"Columnas seleccionadas: {', '.join(columnas_validas)}")
                    st.session_state.df_seleccionado = df_seleccionado
                    st.session_state.columnas_seleccionadas = True

    # Mostrar DataFrame seleccionado si se han seleccionado columnas
    if st.session_state.columnas_seleccionadas:


        st.write("### DataFrame Seleccionado")
        
        st.dataframe(st.session_state.df_seleccionado)
        
        with st.expander("DataFrame Original"):
            st.dataframe(st.session_state.original_df.copy())

    # Sidebar con opciones de transformación y validaciones de archivo
    with st.sidebar:
        st.title("Casos de prueba")
        
        st.header("Modificación de Datos:")
        uppercase_option = st.checkbox("Ingresar Mayúsculas")
        parse_data_option = st.checkbox("Datos Parceados")
        null_values_option = st.checkbox("Valores Nulos")
        special_characters_option = st.checkbox("Agregar Caracteres especiales")
        montos_negativos = st.checkbox("Procesar Montos Negativos")
        montos_en_cero = st.checkbox("Procesar Montos en Cero")
        fecha_usuario = st.checkbox("Ingresa una Fecha")
        
        st.header("Eliminación de Datos:")
        delete_column_option = st.checkbox("Borrar columna")
        
        #st.header("Validación de Esquema:")
        #validate_schema_option = st.checkbox("Validar el Esquema")
        #data_quantity_option = st.checkbox("Cantidad de Datos")
        #data_validation_option = st.checkbox("Validación de la Data")
        #nombre_columnas = st.checkbox("Nombre de las Columnas")
        #orden_columnas = st.checkbox("Orden de las Columnas")
        #t#ipo_dato = st.checkbox("Validación tipo de Datos en la Tabla")
        #valores_permitidos = st.checkbox("Valores Permitidos (Nulos, Caracteres especiales, Duplicados)")
        
        st.title("Opciones de Guardado")
        guardar_csv = st.checkbox("Guardar como CSV")
        guardar_excel = st.checkbox("Guardar como Excel")
        guardar_json = st.checkbox("Guardar como JSON")
        guardar_parquet = st.checkbox("Guardar como Parquet")
        nombre_archivo = st.text_input("Nombre del archivo:", value="datos_modificados")

    # Funciones de transformación y validaciones adicionales

    def procesar_montos_negativos(df, column_name):
        try:
            df[column_name] = df[column_name].apply(lambda x: -abs(x))
        except Exception as e:
            st.error(f"Error al procesar montos negativos: {str(e)}")
        return df

    def procesar_montos_en_cero(df, column_name):
        try:
            df[column_name] = 0
        except Exception as e:
            st.error(f"Error al procesar montos en cero: {str(e)}")
        return df

    def aplicar_fecha_usuario(df, column_name, fecha):
        try:
            df[column_name] = fecha
        except Exception as e:
            st.error(f"Error al aplicar fecha: {str(e)}")
        return df

    def add_timestamp_column(df, column_name='TIMESTAMP'):
        try:
            df[column_name] = datetime.now()
        except Exception as e:
            st.error(f"Error al agregar timestamp: {str(e)}")
        return df

    def uppercase_column_names(df):
        try:
            df.columns = [col.upper() for col in df.columns]
        except Exception as e:
            st.error(f"Error al convertir nombres a mayúsculas: {str(e)}")
        return df

    def valores_nulos(df, column_name):
        if column_name not in df.columns:
            st.error(f"La columna '{column_name}' no existe en el DataFrame.")
            return df
        new_value = ' '
        df[column_name] = new_value
        return df
        

    def agregar_caracteres_especiales(df, column_name):
        try:
            if column_name not in df.columns:
                raise ValueError(f"La columna '{column_name}' no existe en el DataFrame.")
            df[column_name] = df[column_name].astype(str) + " @!"
        except Exception as e:
            st.error(f"Error al agregar caracteres especiales: {str(e)}")
        return df

    def borrar_columna(df, column_name):
        try:
            if column_name not in df.columns:
                raise ValueError(f"La columna '{column_name}' no existe en el DataFrame.")
            df.drop(columns=[column_name], inplace=True)
        except Exception as e:
            st.error(f"Error al borrar columna: {str(e)}")
        return df

    # Aplicación de transformaciones inmediatas

    if st.session_state.df_seleccionado is not None:
        
        # Procesar Mayúsculas
        if uppercase_option:
            temp_df = uppercase_column_names(st.session_state.df_seleccionado)
            st.write("Vista previa de cambio: Mayúsculas")
            st.dataframe(temp_df)
            if st.button("Mantener Cambios (Mayúsculas)"):
                st.session_state.final_df = temp_df.copy()

        # Procesar Datos Parceados
        if parse_data_option:
            temp_df = add_timestamp_column(st.session_state.df_seleccionado)
            st.write("Vista previa de cambio: Marca de Tiempo")
            temp_df
            if st.button("Mantener Cambios (Marca de Tiempo)"):
               st.session_state.final_df = temp_df

        # Procesar Valores Nulos
        if null_values_option:
            columna_nulos = st.text_input("Escribe el nombre de la columna para reemplazar valores nulos:")
            if columna_nulos:
                temp_df = valores_nulos(st.session_state.df_seleccionado, columna_nulos)
                st.write(f"Vista previa de cambio: Valores Nulos en {columna_nulos}")
                st.dataframe(temp_df)
                if st.button("Mantener Cambios (Valores Nulos)"):
                    st.session_state.final_df = temp_df.copy()

        # Procesar Caracteres Especiales
        if special_characters_option:
            columna_caracteres = st.text_input("Escribe el nombre de la columna para agregar caracteres especiales:")
            if columna_caracteres:
                temp_df = agregar_caracteres_especiales(st.session_state.df_seleccionado, columna_caracteres)
                st.write(f"Vista previa de cambio: Caracteres Especiales en {columna_caracteres}")
                st.dataframe(temp_df)
                if st.button("Mantener Cambios (Caracteres Especiales)"):
                     st.session_state.final_df = temp_df.copy()

        # Borrar columna
        if delete_column_option:
            columna_borrar = st.text_input("Escribe el nombre de la columna para borrar:")
            if columna_borrar:
                temp_df = borrar_columna(st.session_state.df_seleccionado, columna_borrar)
                st.write(f"Vista previa de cambio: Borrar columna {columna_borrar}")
                st.dataframe(temp_df)
                if st.button("Mantener Cambios (Borrar columna)"): 
                    st.session_state.final_df = temp_df.copy()
        
        
        if montos_negativos:
            datosnegativos = st.text_input("Escribe el nombre de la columna para ingresar datos negativos:")
            if datosnegativos:
                temp_df = procesar_montos_negativos(st.session_state.df_seleccionado, datosnegativos)
                st.write(f"Vista previa de cambio: Datos Negativos {datosnegativos}")
                st.dataframe(temp_df)
                if st.button("Mantener Cambios (datosnegativos )"): 
                    st.session_state.final_df = temp_df.copy()
                    
        
        
        if montos_en_cero:
            montosencero = st.text_input("Escribe el nombre de la columna para ingresar datos negativos:")
            if montosencero :
                temp_df = procesar_montos_en_cero(st.session_state.df_seleccionado, montosencero )
                st.write(f"Vista previa de cambio: Datos Negativos {montosencero}")
                st.dataframe(temp_df)
                if st.button("Mantener Cambios (montosencero)"): 
                    st.session_state.final_df = temp_df.copy()
        
        
        
        if fecha_usuario:
            fechausuario = st.text_input("Escribe el nombre de la columna para ingresar datos negativos:")
            fecha = st.date_input("Selecciona una Fecha")
            if fechausuario :
                temp_df = aplicar_fecha_usuario(st.session_state.df_seleccionado, fechausuario,fecha )
                st.write(f"Vista previa de cambio: Datos Negativos {fechausuario}")
                st.dataframe(temp_df)
                if st.button("Mantener Cambios (fechausuario)"): 
                    st.session_state.final_df = temp_df.copy()
        
    # Guardar archivos en diferentes formatos
    if st.session_state.df_seleccionado is not None:
        if guardar_csv:
            csv = StringIO()
            st.session_state.df_seleccionado.to_csv(csv, index=False)
            csv.seek(0)
            st.download_button("Descargar CSV", csv.getvalue(), f"{nombre_archivo}.csv")

        if guardar_excel:
            excel = BytesIO()
            with pd.ExcelWriter(excel, engine='xlsxwriter') as writer:
                st.session_state.df_seleccionado.to_excel(writer, index=False)
                excel.seek(0)
            st.download_button("Descargar Excel", excel.getvalue(), f"{nombre_archivo}.xlsx")

        if guardar_json:
            json_data = st.session_state.df_seleccionado.to_json(orient='records')
            st.download_button("Descargar JSON", json_data, f"{nombre_archivo}.json")

        if guardar_parquet:
            parquet_buffer = BytesIO()
            st.session_state.df_seleccionado.to_parquet(parquet_buffer, index=False)
            st.download_button("Descargar Parquet", parquet_buffer.getvalue(), f"{nombre_archivo}.parquet")

    if st.button("Finalizar y Limpiar"):
        st.session_state.final_df = None
        st.session_state.original_df = None
        st.session_state.df_seleccionado = None
        st.session_state.columnas_seleccionadas = False
        st.success("Sesión finalizada.")
        st.rerun()