# Usar una imagen base oficial de Python
FROM python:3.8-slim

# Establecer el directorio de trabajo en el contenedor
WORKDIR /app

# Copiar los archivos necesarios al contenedor
COPY . /app

# Actualizar pip e instalar las dependencias de Python
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Exponer el puerto que Streamlit usará
EXPOSE 8501

# Comando para ejecutar la aplicación
CMD ["streamlit", "run", "home.py", "--server.address=0.0.0.0"]

