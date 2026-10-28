# Uso

## Comandos principales

| Comando | Descripción |
|---------|-------------|
| `nauta-monitor` | Panel en vivo (por defecto). Se actualiza automáticamente. |
| `nauta-monitor watch` | Igual que el anterior, con opciones avanzadas. |
| `nauta-monitor status` | Consulta única, ideal para scripts. |
| `nauta-monitor init` | Asistente interactivo para crear `config.toml`. |
| `nauta-monitor doctor` | Diagnóstico completo (config, red, portal, speedtest). |

## Panel en vivo

El panel muestra:

- **Crédito** - Saldo actual en CUP
- **Horas** - Horas restantes calculadas
- **Consumo** - Consumo medio (h/día) y días estimados hasta agotarse
- **Fin estimado** - Fecha aproximada cuando se acabará el saldo al ritmo actual
- **Velocidad** - Última medición contra fast.com (↓/↑ Mbps), estado de medición o error
- **Consumo semanal** - Gráfico de barras con los últimos 7 días

## Consulta única

```bash
# Salida legible
nauta-monitor status

# Salida JSON (ideal para scripts)
nauta-monitor status --json

# Sin speedtest (más rápido)
nauta-monitor status --no-speedtest

# Sin guardar en historial
nauta-monitor status --no-history
```

## Opciones del modo watch

```bash
# Cambiar intervalo de consulta de saldo (segundos)
nauta-monitor watch --interval 1800

# Cambiar intervalo de speedtest
nauta-monitor watch --speedtest-interval 3600

# Desactivar speedtest
nauta-monitor watch --no-speedtest

# Especificar archivo de historial
nauta-monitor watch --history /ruta/a/historial.jsonl
```

## Modo no-interactivo (logs)

Cuando se ejecuta sin terminal (Docker, systemd, cron con redirección), muestra una línea por actualización sin colores/ANSI. Perfecto para logs.

## Atajos

- `Ctrl+C` para salir del modo watch
- `--verbose` para ver el HTML crudo del portal (debugging)
- `--config` para usar un archivo de configuración distinto
