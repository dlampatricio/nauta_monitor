FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=America/Havana

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends tzdata \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY nauta_monitor/ ./nauta_monitor/

RUN pip install --no-cache-dir .

RUN useradd -m -u 1000 nauta
USER nauta

CMD ["nauta-monitor", "watch"]