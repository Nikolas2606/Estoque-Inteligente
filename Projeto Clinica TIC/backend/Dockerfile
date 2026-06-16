# ============================================
# Dockerfile - Flask Application
# Sistema de Estoque Inteligente
# ============================================

FROM python:3.12-slim

# Evitar prompts interativos
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Diretório de trabalho
WORKDIR /app

# Instalar dependências de sistema (para PyMySQL + cryptography)
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libffi-dev && \
    rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código-fonte
COPY . .

# Porta exposta (uso interno na rede Docker)
EXPOSE 5000

# Comando para criar tabelas e popular o banco antes de iniciar o servidor
CMD ["sh", "-c", "python -c 'from app import create_app; create_app(\"development\").app_context().push(); from app.extensions import db; db.create_all()' && python seed.py && gunicorn -w 4 -b 0.0.0.0:5000 --timeout 120 run:app"]