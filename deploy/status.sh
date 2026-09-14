#!/usr/bin/env bash
set -euo pipefail

# Lector del estado Nauta para la pantalla del homeserver.
# Lee las últimas muestras del historial (JSONL) y las formatea con jq.
# No consulta al portal: solo refleja lo que ya escribió el contenedor.

NAUTA_HOME="${NAUTA_HOME:-/opt/nauta-monitor}"
HIST="$NAUTA_HOME/data/history.jsonl"

if [ ! -f "$HIST" ]; then
    echo "Sin datos todavia: revisa 'docker compose logs -f'"
    exit 0
fi

tail -n 3 "$HIST" | jq -r \
    '"\(.timestamp) | \(.credit // 0) CUP | horas \(.hours // 0) | desc \(.download_mbps // 0) Mbps | sub \(.upload_mbps // 0) Mbps | ping \(.ping_ms // 0) ms"'