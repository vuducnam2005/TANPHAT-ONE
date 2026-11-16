FROM python:3.12-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libldap2-dev \
    libsasl2-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    libjpeg-dev \
    curl \
    git \
    postgresql-client \
    wkhtmltopdf \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Pre-install python packages for fast caching
COPY requirements.txt /workspace/
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8069

CMD ["python3", "odoo-bin", "-c", "/workspace/docker.odoo.conf"]
