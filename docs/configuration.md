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
# fast.com (Netflix). Necesita sesión Nauta activa (internet internacional).
api_url = "https://api.fast.com"
# token = ""                   # vacío = token público de fast.com
connections = 3                # conexiones paralelas de descarga
max_duration = 10              # segundos por dirección (bajada y subida)
max_mb = 50                    # tope de datos por dirección, en MB

[alerts]
min_balance_hours = 24         # Alerta cuando queden menos de estas horas
# on_alert = "notify-send 'Nauta' 'Quedan menos de 24 horas'"
```

## Speedtest (fast.com)

`[speedtest]` configura la medición de velocidad. Usa los mismos endpoints que el
cliente JS de **fast.com** (Netflix), sin navegador ni dependencias extra:

| Clave | Por defecto | Descripción |
|-------|-------------|-------------|
| `api_url` | `https://api.fast.com` | Base de los endpoints de fast.com |
| `token` | vacío | Token público; déjalo vacío salvo que Netflix lo cambie |
| `connections` | `3` | Conexiones paralelas de descarga (1–8) |
| `max_duration` | `10` | Segundos por dirección (descarga y subida) |
| `max_mb` | `50` | Tope de datos por dirección, en MB |

La prueba necesita **internet internacional activo** (sesión Nauta iniciada): el
saldo se consulta en la red interna de ETECSA, pero fast.com no. Cada prueba
consume datos y tiempo real; con `speedtest_interval = 1800` son ~16 min/día, así
que `3600` (8 min/día) o `0` son alternativas razonables.

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
