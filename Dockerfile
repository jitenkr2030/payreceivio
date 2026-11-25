FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev libxml2 libxslt1.1 libjpeg-dev zlib1g-dev \
    postgresql-client netcat-openbsd && \
    rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements/base.txt /app/requirements/base.txt
RUN pip install --upgrade pip && pip install -r /app/requirements/base.txt

# Copy project
COPY . /app/

# Create non-root user
RUN useradd -m payreceivio && chown -R payreceivio:payreceivio /app
USER payreceivio

EXPOSE 8000

# Entrypoint
ENTRYPOINT ["/bin/sh", "-c"]
CMD ["gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120"]
