# nauta-monitor

Monitor sencillo y claro para tu cuenta **Nauta Hogar**. Consulta el saldo en CUP, calcula las horas de servicio restantes según tu tarifa, estima cuándo se te acabará el saldo y mide la velocidad real de tu internet con fast.com.

**Ideal para:** ver rápido cuánto te queda, vigilar tu consumo diario/semanal y tenerlo corriendo en segundo plano con Docker.

## Cómo funciona

Replica el flujo del portal de acceso ETECSA:

1. `GET https://secure.etecsa.net:8443/` obtiene el formulario de login con los
   campos ocultos `CSRFHW` y `wlanuserip` (requiere estar dentro de la red Nauta).
2. `POST .../EtecsaQueryServlet` con usuario, contraseña, `wlanuserip` y
   `CSRFHW` devuelve el estado de la cuenta: estado, **crédito en CUP**,
   fecha de expiración, áreas de acceso y las últimas sesiones.
3. **Horas restantes = crédito / tarifa** (`cup_per_hour`, por defecto 12.5 CUP/h).
4. La velocidad se mide contra **fast.com** (`api.fast.com`): latencia, bajada y
   subida. Refleja tu internet internacional, así que necesita la sesión Nauta
   activa y consume datos/tiempo real (`max_duration = 10` s por dirección).

## Instalación rápida (3 pasos)

```bash
# 1) Clonar
git clone <repo> && cd nauta_monitor

# 2) Crear entorno e instalar
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/macOS
pip install -e .

# 3) Configurar e iniciar
nauta-monitor init             # Asistente interactivo (recomendado)
# o: cp config.example.toml config.toml && nano config.toml
nauta-monitor doctor           # Comprobar conexión y credenciales
nauta-monitor                  # Ver panel en vivo
```

En `cmd.exe` la ruta de activación usa barras invertidas (`.venv\Scripts\activate`) y el
último paso lleva punto final: `pip install -e .`.

## Configuración

Copia `config.example.toml` a `config.toml` y rellena tus datos:

```toml
[nauta]
username = "usuario@nauta.com.cu"
# password = "mi-clave"          # o usa la variable de entorno NAUTA_PASS
portal_interface = ""            # ej. "wlo1" para consultar el portal fuera del VPN
cup_per_hour = 12.5              # CUPs que consume cada hora (tu tarifa)
saldo_interval = 3600            # segundos entre consultas de saldo
speedtest_interval = 1800        # segundos entre pruebas de velocidad (0 = off)

[speedtest]
api_url = "https://api.fast.com" # fast.com (Netflix)
connections = 3                  # conexiones paralelas de descarga
max_duration = 10                # segundos por dirección
max_mb = 50                      # tope de datos por dirección
```

También se aceptan `NAUTA_USERNAME` y `NAUTA_PASS` como variables de entorno.

En Linux, si usas un VPN que desvía el tráfico del portal, puedes configurar
`portal_interface = "wlo1"` con la interfaz conectada a la red Nauta. Esto solo
vincula las conexiones al portal con esa interfaz; no cambia las rutas del
sistema ni la ruta del speedtest. La resolución DNS continúa usando el resolver
del sistema. Deja el campo vacío para usar el enrutamiento normal.

El speedtest mide contra **fast.com**, así que consume datos y tiempo de conexión
real: con `speedtest_interval = 1800` son unos 16 minutos al día. Si te importa el
saldo, usa `3600` o desactívalo con `0`.

## Uso

```bash
# Panel en vivo (comando por defecto)
nauta-monitor

# Consulta rápida
nauta-monitor status        # Consulta única
nauta-monitor status --json # Para scripts/automatismos

# Diagnóstico
nauta-monitor doctor

# Configuración interactiva
nauta-monitor init
```

`watch` (por defecto) muestra un panel limpio con el **crédito**, las **horas restantes**,
el **consumo medio** (horas/día), **fin estimado** del saldo al ritmo actual y la
**velocidad** real contra fast.com (↓/↑). Debajo aparece un gráfico de barras con el consumo de los
últimos 7 días (calculado del historial; los huecos largos se ignoran).

Si la salida no es una terminal (contenedor, systemd, redirección a archivo)
escribe una línea de log por cada actualización, sin códigos ANSI.

Opciones del modo `watch` (todas opcionales):

```bash
nauta-monitor watch --interval 1800           # segundos entre consultas de saldo
nauta-monitor watch --speedtest-interval 3600 # segundos entre speedtests
nauta-monitor watch --no-speedtest            # desactiva el speedtest
nauta-monitor watch --history ruta/hist.jsonl  # historial alternativo
```

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

### Controlar el monitor desde el plugin

Instala los comandos en un entorno de herramientas de usuario (Arch protege el
Python del sistema; no uses `pip --system`):

```bash
uv tool install --editable .
```

Abre el widget de Nauta, introduce usuario y contraseña y pulsa **Guardar e
iniciar**. El panel actualiza únicamente `username` y `password` en
`~/.config/nauta-monitor/config.toml`, manteniendo el resto de las preferencias
y comentarios existentes. Si ese archivo no tenía valores de tarifa o intervalos,
se usan los defaults ya definidos por el monitor; el helper no los vuelve a
declarar. El archivo queda con permisos `600` dentro de un directorio `700`.

El widget ofrece iniciar, detener, consultar, cambiar o eliminar credenciales.
La contraseña no se muestra después de guardarla y se entrega al helper por
stdin, nunca como argumento del proceso.

La gestión de credenciales es independiente de Omarchy y systemd. El backend
actual del botón **Guardar e iniciar** usa `systemd --user` en Linux; el cliente
Python y su configuración TOML siguen siendo portables. En otros sistemas, el
monitor se puede ejecutar con el entorno local existente, sin instalar este
backend de servicio.

Los eventos recientes de `journalctl --user -u nauta-monitor.service` aparecen
en el área de actividad. Speedtest queda apagado por defecto para no gastar saldo.
La configuración de credenciales puede eliminarse desde el panel; primero se
detiene y deshabilita el servicio y se quita su unidad de usuario, después se
limpian esos dos campos sin borrar las demás preferencias.

### Desplegar sin Docker Hub (GHCR)

En redes donde Docker Hub está bloqueado (p. ej. Nauta devuelve `403 Forbidden`),
la imagen se compila en GitHub Actions y se publica en
`ghcr.io/<dueño>/nauta_monitor` con los tags `latest` (rama por defecto), SHA
del commit y `vX.Y.Z` (tags git). El homelab solo la descarga:

```bash
# En una máquina sin acceso a Docker Hub:
docker compose -f docker-compose.yml -f deploy/docker-compose.server.yml pull
docker compose -f docker-compose.yml -f deploy/docker-compose.server.yml up -d
```

El push a `master` dispara el build automáticamente (pestaña *Actions* del
repo); también puedes dispararlo a mano desde *Actions → docker-image →
Run workflow*. Para desarrollo local (con acceso normal a Docker Hub) se sigue
usando `docker compose up -d --build`, que compila con `build: .`.

Si algún día GHCR exigiera autenticación para el `pull` (hoy no: la imagen es
pública), haz `docker login ghcr.io -u <usuario>` con un token de GitHub con
scope `read:packages`.

## Plugin Omarchy

El widget muestra una cuenta atrás local del tiempo estimado restante, actualizada
cada minuto a partir de la última consulta de saldo. No consulta ETECSA cada
minuto: la frecuencia de consulta sigue siendo la configurada en el monitor.
La cuenta atrás descuenta el tiempo transcurrido linealmente según la tarifa
configurada y se corrige con cada consulta exitosa, por lo que es una estimación.
El signo `!` indica que los datos están desactualizados o que falló la última
consulta; el panel conserva el estado del servicio y su registro de actividad.

Esta integración es para **Omarchy y el monitor en el mismo equipo**. El widget
lee un archivo local cada 30 segundos y al abrir el panel o pulsar **Volver a
leer**. No habla con ETECSA, no necesita Docker para funcionar como visor y no
lee credenciales. Los intervalos de consulta y speedtest siguen siendo del monitor.

Desde la raíz del repo, en una sesión de Omarchy Shell (manifiesto v1; Omarchy
4.5):

```bash
omarchy plugin validate ./nauta_monitor/platform/linux/omarchy
plugin_dir="$HOME/.config/omarchy/plugins/local.nauta-monitor"
mkdir -p "$plugin_dir"
cp -R ./nauta_monitor/platform/linux/omarchy/. "$plugin_dir/"
omarchy-shell shell rescanPlugins
omarchy plugin enable local.nauta-monitor --section right
```

**Con Docker Compose**, reconstruye el monitor y configura la ruta del volumen
en la barra:

```bash
docker compose up -d --build
omarchy bar set local.nauta-monitor statusPath "$PWD/data/status.json"
```

El contenedor escribe como UID `1000`. El directorio `data/` debe ser escribible
por ese UID y el escritorio debe poder leer `status.json`, que se publica con
permisos privados. El caso estándar es que ambos usen el mismo UID.

**Sin Docker**, escribe en la ruta predeterminada del widget:

```bash
nauta-monitor watch --no-speedtest --snapshot \
  "${XDG_STATE_HOME:-$HOME/.local/state}/nauta-monitor/status.json"
```

Para quitar el indicador de la barra: `omarchy plugin disable local.nauta-monitor`.
Esto no detiene el monitor.

El archivo JSON (`version: 1`) contiene `credit_cup`, `hours`, `account_status`,
`last_success_at`, `last_attempt_at`, `result` (`ok` o `error`) y
`stale_after_seconds` (intervalo de saldo más 60 segundos de margen). Las marcas
de tiempo son segundos Unix. Tras un error, el monitor conserva el último saldo
válido de esa ejecución y no añade una muestra al historial. Si aún no ha
obtenido un saldo válido en esa ejecución, los campos de saldo y última
consulta exitosa son `null`, no cero. El archivo se reemplaza de forma atómica y
no incluye usuario, contraseña, sesiones ni errores crudos.

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
sudo apt update && sudo apt install -y tmux htop jq docker.io docker-compose-plugin
sudo usermod -aG docker $USER   # y vuelve a entrar a la sesión

git clone <repo> /opt/nauta-monitor
cd /opt/nauta-monitor
cp .env.example .env
cp config.example.toml config.toml && nano config.toml   # credenciales
mkdir data
docker compose -f docker-compose.yml -f deploy/docker-compose.server.yml pull
docker compose -f docker-compose.yml -f deploy/docker-compose.server.yml up -d
docker compose logs -f                    # verifica la primera línea de saldo

chmod +x deploy/*.sh
./deploy/install_dashboard.sh    # autologin tty1 + pantalla que no se apaga
sudo reboot                      # al encender aparece el dashboard
```

Para revisar el estado en cualquier momento: `docker compose ps` y
`docker compose logs --tail 20`. Para ver solo el dashboard: `./deploy/dashboard.sh`.

Si algún día GHCR exigiera autenticación para el `pull` (hoy no: la imagen es
pública), haz `docker login ghcr.io -u <usuario>` con un token de GitHub con
scope `read:packages`.

Atajos tmux: `Ctrl-b d` (detach, la sesión sigue viva), `Ctrl-b %`/`"` (partir
paneles), `Ctrl-b o` (saltar panes), `tmux attach -t dash` (volver).

Por SSH desde otro equipo: `ssh usuario@laptop` y luego `tmux attach -t dash`
(cada cliente de tmux renderiza su propia copia; la pantalla de la laptop no se
molesta).

Para agregar más programas al dashboard, edita `deploy/dashboard.sh` y añade
otro `split-window` + `send-keys` (p. ej. `docker logs -f <otro-servicio>`).

## Notas

- El host del portal (`https://secure.etecsa.net:8443`) normalmente es
  inalcanzable fuera de la red Nauta: este monitor debe correr en el enrutador o
  una máquina dentro de la red.
- El portal usa un TLS antiguo: por eso el cliente fuerza `SECLEVEL=0` y acepta
  certificados autofirmados solo para esta conexión (nunca `verify=False` global).
- `config.toml`, `.env`, `history.jsonl` y `data/` están en `.gitignore`: no
  los comprometas.
- En el homelab, el monitor corre **nativo en Docker**; el dashboard de la
  consola es solo un visor (no consulta al portal: lee el historial y los logs).

## Documentación

- **Online**: [Documentación completa](https://dlampatricio.github.io/nauta_monitor/)
- **Local**: `pip install mkdocs mkdocs-material && mkdocs serve`

## Desarrollo

```bash
pip install -e ".[dev]"
python -m pytest
node --test tests/linux/test_omarchy_snapshot.cjs
```

La lógica portable vive en `nauta_monitor/`, las credenciales y sus pruebas
en `nauta_monitor/security/` y `tests/security/`, y las pruebas generales en
`tests/core/`. Las integraciones específicas de Linux/Omarchy y sus pruebas
están bajo `nauta_monitor/platform/linux/` y `tests/linux/`.
