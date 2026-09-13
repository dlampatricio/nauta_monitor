# nauta-monitor

Monitor de línea de comandos para la cuenta **Nauta Hogar**. Consulta el saldo
en CUP, calcula las horas de servicio restantes según tu tarifa y mide la
velocidad real del enlace contra el servidor LibreSpeed de ETECSA.

## Cómo funciona

Replica el flujo del portal de acceso ETECSA:

1. `GET https://secure.etecsa.net:8443/` obtiene el formulario de login con los
   campos ocultos `CSRFHW` y `wlanuserip` (requiere estar dentro de la red Nauta).
2. `POST .../EtecsaQueryServlet` con usuario, contraseña, `wlanuserip` y
   `CSRFHW` devuelve el estado de la cuenta: estado, **crédito en CUP**,
   fecha de expiración, áreas de acceso y las últimas sesiones.
3. **Horas restantes = crédito / tarifa** (`cup_per_hour`, por defecto 12.5 CUP/h).
4. La velocidad se mide con el protocolo LibreSpeed contra el servidor de
   ETECSA (`http://speedtest.cd.etecsa.cu/`, configurable).

## Instalación

```bash
git clone ... && cd nauta_monitor
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/macOS (homelab)
pip install -e ".[dev]"
```

## Configuración

Copia `config.example.toml` a `config.toml` y rellena tus datos:

```toml
[nauta]
username = "usuario@nauta.com.cu"
# password = "mi-clave"          # o usa la variable de entorno NAUTA_PASS
cup_per_hour = 12.5              # CUPs que consume cada hora (tu tarifa)
saldo_interval = 3600            # segundos entre consultas de saldo
speedtest_interval = 1800        # segundos entre pruebas de velocidad (0 = off)
```

También se aceptan `NAUTA_USERNAME` y `NAUTA_PASS` como variables de entorno.

## Uso

```bash
# Consulta única
nauta-monitor once
nauta-monitor once --json            # salida JSON para scripts

# Bucle con panel en vivo (en el homelab)
nauta-monitor watch
nauta-monitor watch --interval 1800 --speedtest-interval 3600

# Últimas muestras guardadas
nauta-monitor history --limit 20
```

> `watch` detecta si la salida es una terminal: si lo es muestra el panel en
> vivo; si no (contenedor, systemd, redirección a archivo) escribe una línea de
> log por cada actualización, sin códigos ANSI.

### Alerta por saldo bajo

Con `[alerts].min_balance_hours` se activa una alerta cuando quedan menos horas
que ese umbral. Puedes ejecutar un comando arbitrario con `[alerts].on_alert`
(por ejemplo, un `notify-send` o un mensaje por Telegram).

## Docker

El contenedor corre `nauta-monitor watch` en modo logs, reinicia solo y persiste
el historial. No necesita terminal interactiva.

```bash
# 0. Variables opcionales (NAUTA_PASS para no dejar la clave en el TOML)
cp .env.example .env

# 1. Copia la plantilla y rellena tus datos
cp config.example.toml config.toml   # chmod 600
mkdir data          # volumen para el historial

# 2. Construye y arranca
docker compose up -d --build

# 3. Ver estado, logs y salud
docker compose ps                     # columna HEALTH = healthy/unhealthy
docker compose logs -f
docker compose logs nauta-monitor --tail 20    # última línea de saldo
```

- La configuración se monta de **solo lectura** (`./config.toml:/app/config.toml:ro`).
- El historial vive en `./data/history.jsonl` y sobrevive reinicios.
- El **healthcheck** consulta el portal cada 5 minutos; si el contenedor no
  puede alcanzar ETECSA (o no hay `config.toml` válido), termina marcado como
  `unhealthy`.
- Zona horaria configurable con `TZ` (por defecto `America/Havana`).
- Logs del contenedor rotan automáticamente (`json-file`, máx 10 MiB × 3).

## Homeserver: dashboard en la consola (laptop Ubuntu)

El monitor corre en Docker; la **pantalla solo ve**. `deploy/` contiene los
scripts para el dashboard de tmux que se muestra en la consola física.

```
pantalla de la laptop (tty1, autologin + tmux "dash")
├─ pane ESTADO: watch -n 60 deploy/status.sh   (lee data/history.jsonl con jq)
├─ pane LOGS:   docker logs -f nauta-monitor    (saldo/speedtest en vivo)
└─ pane HTOP:   recursos del homeserver
```

Toda la preparación del servidor (una vez):

```bash
sudo apt update && sudo apt install -y tmux htop jq docker.io
sudo usermod -aG docker $USER   # y vuelve a entrar a la sesión

git clone <repo> /opt/nauta-monitor
cd /opt/nauta-monitor
cp .env.example .env
cp config.example.toml config.toml && nano config.toml   # credenciales
mkdir data
make up                          # arranca el contenedor

chmod +x deploy/*.sh
./deploy/install_dashboard.sh    # autologin tty1 + pantalla que no se apaga
sudo reboot                      # al encender aparece el dashboard
```

Atajos tmux: `Ctrl-b d` (detach, la sesión sigue viva), `Ctrl-b %`/`"` (partir
paneles), `Ctrl-b o` (saltar panes), `tmux attach -t dash` (volver).

Por SSH desde otro equipo: `ssh usuario@laptop` y luego `tmux attach -t dash`
(cada cliente de tmux renderiza su propia copia; la pantalla de la laptop no se
molesta). Solo para ver logs: `make logs`.

Para agregar más programas al dashboard, edita `deploy/dashboard.sh` y añade
otro `split-window` + `send-keys` (p. ej. `docker logs -f <otro-servicio>`).

## Notas

- El host del portal (`https://secure.etecsa.net:8443`) normalmente es
  inalcanzable fuera de la red Nauta: este monitor debe correr en el enrutador o
  una máquina dentro de la red.
- `config.toml`, `.env`, `history.jsonl` y `data/` están en `.gitignore`: no
  los comprometas.
- En el homelab, el monitor corre **nativo en Docker**; el dashboard de la
  consola es solo un visor (no consulta al portal: lee el historial y los logs).

## Desarrollo

```bash
pip install -e ".[dev]"
python -m pytest
```