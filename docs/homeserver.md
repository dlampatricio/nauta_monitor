# Homeserver / Consola física

Para mostrar el monitor en la pantalla física de un mini PC/laptop (sin monitor externo separado):

## ¿Cómo funciona?

```
Pantalla física (tty1, autologin + tmux "dash")
├─ Pane 1: deploy/status.sh   (lee data/history.jsonl con jq)
├─ Pane 2: docker logs -f     (logs en vivo del contenedor)
└─ Pane 3: htop               (recursos del sistema)
```

## Instalación

```bash
# Dependencias
sudo apt update && sudo apt install -y tmux htop jq docker.io docker-compose-plugin
sudo usermod -aG docker $USER
# Cerrar sesión y volver a entrar

# Clonar y configurar
git clone <repo> /opt/nauta-monitor
cd /opt/nauta-monitor
cp .env.example .env
cp config.example.toml config.toml && nano config.toml
mkdir data

# Arrancar contenedor
docker compose -f docker-compose.yml -f deploy/docker-compose.server.yml pull
docker compose -f docker-compose.yml -f deploy/docker-compose.server.yml up -d

# Configurar dashboard en tty1
chmod +x deploy/*.sh
./deploy/install_dashboard.sh
sudo reboot
```

## Uso

- **En la consola física**: Aparecerá el dashboard automáticamente al arrancar
- **Por SSH**: `ssh usuario@equipo` → `tmux attach -t dash` (la pantalla física no se interrumpe)
- **Desconectar sin cerrar**: `Ctrl+b` luego `d`
- **Ver solo dashboard**: `./deploy/dashboard.sh`

## Personalizar

Edita `deploy/dashboard.sh` para añadir más paneles (otros contenedores, logs, etc.).

## Notas

- El dashboard **solo lee** datos (historial + logs), no consulta el portal directamente
- Funciona con autologin en tty1, la pantalla no se apaga automáticamente
- Usa tmux para permitir múltiples clientes simultáneos
