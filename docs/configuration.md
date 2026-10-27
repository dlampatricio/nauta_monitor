# Configuración

## Método rápido (recomendado)

El asistente interactivo crea la configuración por ti:

```bash
nauta-monitor init
```

Te preguntará usuario, contraseña, tarifa (`cup/h`), intervalos, etc. Generará `config.toml` con permisos restringidos cuando sea posible.

## Método manual

Copia la plantilla:

```bash
cp config.example.toml config.toml
```

Edita `config.toml`:

```toml
[nauta]
username = "usuario@nauta.com.cu"
# password = "mi-clave"        # Opcional si usas variable de entorno
cup_per_hour = 12.5            # CUP por hora según tu tarifa
saldo_interval = 3600          # Segundos entre consultas de saldo
speedtest_interval = 1800      # Segundos entre speedtests (0 = desactivado)
history_path = "history.jsonl"

[speedtest]
base_url = "http://speedtest.cd.etecsa.cu/"
dl_url = "backend/garbage.php"
ul_url = "backend/empty.php"
ping_url = "backend/empty.php"
get_ip_url = "backend/getIP.php"
download_chunks = 200
upload_kib = 256
concurrent = 3
max_duration = 20

[alerts]
min_balance_hours = 24         # Alerta cuando queden menos de estas horas
# on_alert = "notify-send 'Nauta' 'Quedan menos de 24 horas'"
```

## Variables de entorno

También puedes usar variables de entorno (útiles en Docker/CI):

| Variable | Descripción |
|----------|-------------|
| `NAUTA_USERNAME` | Usuario Nauta |
| `NAUTA_PASS` | Contraseña Nauta |

## Rutas del archivo de configuración

Por defecto busca `config.toml` en el directorio actual. Puedes especificar otra ruta:

```bash
nauta-monitor --config /ruta/a/config.toml
```
