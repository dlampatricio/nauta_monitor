#!/usr/bin/env bash
set -euo pipefail

# Configura el dashboard en la consola física del homeserver:
#   1. Autologin del usuario en tty1 (override de getty).
#   2. El .bashrc del usuario lanza la sesión tmux "dash" al iniciar.
#   3. La pantalla de la consola no se apaga (setterm -blank 0).
# Ejecutar como el usuario normal (usará sudo internamente).

USER_TARGET="${SUDO_USER:-$(id -un)}"
HOME_TARGET="/home/$USER_TARGET"
DASH_CMD="/opt/nauta-monitor/deploy/dashboard.sh"
MARK_BEGIN="# >>> nauta-monitor dashboard"
MARK_END="# <<< nauta-monitor dashboard"

# 1) Autologin en tty1 (systemd drop-in).
sudo mkdir -p /etc/systemd/system/getty@tty1.service.d
sudo tee /etc/systemd/system/getty@tty1.service.d/autologin.conf > /dev/null <<EOF
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin $USER_TARGET --noclear tty1 38400 linux
EOF
sudo systemctl daemon-reload

# 2) Snippet en .bashrc (sin duplicar si se relanza).
if ! grep -q "$MARK_BEGIN" "$HOME_TARGET/.bashrc"; then
    cat >> "$HOME_TARGET/.bashrc" <<EOF

$MARK_BEGIN
if [ -z "\$TMUX" ] && [ "\$(tty)" = "/dev/tty1" ]; then
    exec tmux new-session -A -s dash 'bash $DASH_CMD'
fi
setterm -blank 0 2>/dev/null || true
$MARK_END
EOF
fi

echo "Listo. Reinicia (sudo reboot) para ver el dashboard en la consola."
echo "En tty1 se hará autologin, se abrirá tmux y aparecerán los paneles."
echo "En otras consolas (Ctrl+Alt+F2) o por SSH tendrás tu shell normal."