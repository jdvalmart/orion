# ---- Build stage ----
FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && pip install --no-cache-dir --upgrade pip

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ---- Runtime stage ----
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libffi8 \
    openssl \
    && rm -rf /var/lib/apt/lists/* \
    && addgroup --gid 1000 --system orion \
    && adduser --uid 1000 --system --gid 1000 --home /app orion

COPY --from=builder /install /usr/local

COPY server.py app.py orion_config.py .
COPY tools/ tools/

RUN mkdir -p /app/data /app/logs \
    && chown -R orion:orion /app

USER 1000:1000

EXPOSE 9099

ENTRYPOINT ["python", "server.py", "--transport", "http", "--host", "0.0.0.0", "--port", "9099"]