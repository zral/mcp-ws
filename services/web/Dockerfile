FROM python:3.11-slim

WORKDIR /app

# Installer systemavhengigheter
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Kopier og installer Python avhengigheter
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Installer ekstra web avhengigheter
RUN pip install --no-cache-dir fastapi uvicorn jinja2 python-multipart httpx

# Kopier applikasjonskode
COPY app.py .
COPY templates/ ./templates/

# Opprett bruker og sett rettigheter
RUN mkdir -p /data && \
    useradd -m -u 1000 webapp && \
    chown -R webapp:webapp /app /data

USER webapp

# Helse sjekk
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Start applikasjonen
CMD ["python", "app.py"]
