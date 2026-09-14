#!/usr/bin/env bash
set -euo pipefail

# Dashboard del homeserver: sesión tmux "dash" con el estado Nauta,
# los logs del contenedor en vivo y htop. Idempotente: si la sesión
# ya existe, solo avisa. Ejecuta: ./deploy/dashboard.sh

SESSION="dash"
NAUTA_HOME="${NAUTA_HOME:-/opt/nauta-monitor}"

if tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "La sesion '$SESSION' ya existe. Adjuntate con: tmux attach -t $SESSION"
    exit 0
fi

tmux new-session -d -s "$SESSION" -n nauta
tmux send-keys -t "$SESSION:nauta.0" "watch -n 60 $NAUTA_HOME/deploy/status.sh" C-m
tmux split-window -h -t "$SESSION:nauta.0"
tmux send-keys -t "$SESSION:nauta.1" "docker logs -f --tail 50 nauta-monitor" C-m
tmux split-window -v -p 45 -t "$SESSION:nauta.1"
tmux send-keys -t "$SESSION:nauta.2" "htop" C-m
tmux select-layout -t "$SESSION:nauta" main-vertical

echo "Sesion '$SESSION' creada. Adjuntate con: tmux attach -t $SESSION"