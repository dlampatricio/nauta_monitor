#!/usr/bin/env bash
set -euo pipefail

# Lector del estado Nauta para la pantalla del homeserver.
# Lee las últimas muestras del historial (JSONL) y las formatea con jq.
# No consulta al portal: solo refleja lo que ya escribió el contenedor.
# No muestra una muestra antigua como si fuera el saldo actual.

NAUTA_HOME="${NAUTA_HOME:-/opt/nauta-monitor}"
HIST="$NAUTA_HOME/data/history.jsonl"

if [ ! -f "$HIST" ]; then
    echo "Sin datos todavia: revisa 'docker compose logs -f'"
    exit 0
fi

SAMPLE="$(tail -n 1 "$HIST")"
TIMESTAMP="$(printf '%s\n' "$SAMPLE" | jq -r '.timestamp // empty')"
MAX_AGE="${NAUTA_MAX_SAMPLE_AGE:-7200}"

if [ -z "$TIMESTAMP" ] || ! SAMPLE_EPOCH="$(date -d "$TIMESTAMP" +%s 2>/dev/null)" \
    || [ "$(( $(date +%s) - SAMPLE_EPOCH ))" -gt "$MAX_AGE" ]; then
    echo "Saldo no disponible: sin actualización reciente del portal Nauta"
    exit 0
fi

printf '%s\n' "$SAMPLE" | jq -r \
    '"\(.timestamp) | \(.credit // 0) CUP | horas \(.hours // 0) | desc \(.download_mbps // 0) Mbps | sub \(.upload_mbps // 0) Mbps | ping \(.ping_ms // 0) ms"'
