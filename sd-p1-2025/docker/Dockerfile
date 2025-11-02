FROM python:3.13-slim

# Configuración base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/home/appuser/.local/bin:${PATH}" \
    PORT=9092 \
    HOST=0.0.0.0

# Dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl gcc build-essential && \
    rm -rf /var/lib/apt/lists/*

# Usuario no root
RUN useradd -ms /bin/bash appuser
WORKDIR /app

# Copia definición de dependencias
COPY Pipfile Pipfile.lock /app/

# Instala pipenv y dependencias desde el lockfile
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir pipenv && \
    pipenv install --system --deploy

# Copia el código fuente
COPY src /app/src

# Asigna propietario y cambia usuario
RUN chown -R appuser:appuser /app
USER appuser

# Expone el puerto interno
EXPOSE 9092

ENTRYPOINT ["python", "-u"]