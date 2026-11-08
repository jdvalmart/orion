# ---- Build stage ----
FROM python:3.12-slim AS builder

WORKDIR /build
RUN pip install --no-cache-dir --upgrade pip
COPY pyproject.toml README.md ./
COPY src/ src/
RUN pip install --no-cache-dir --prefix=/install ".[semantic]"


# ---- Runtime stage ----
FROM python:3.12-slim

RUN useradd --create-home --uid 1000 orion
COPY --from=builder /install /usr/local

ENV ORION_DATA_DIR=/data
RUN mkdir -p /data && chown orion:orion /data
USER orion
VOLUME ["/data"]
EXPOSE 9099

# ORION_TOKEN is required: the server refuses to bind 0.0.0.0 without it.
ENTRYPOINT ["orion", "--transport", "http", "--host", "0.0.0.0", "--port", "9099"]
