# Imagen base de Python 3.12 optimizada
FROM python:3.12-slim

# Variables de entorno para Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema requeridas para la compilación si fuera necesario
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivo de requerimientos e instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente de la aplicación backend
COPY . /app

# Exponer el puerto de FastAPI
EXPOSE 8000

# Comando para arrancar el servidor con Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
