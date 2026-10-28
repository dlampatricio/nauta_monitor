# Registro de cambios

## [0.4.0] - 2026-10-28

### Cambiado
- El speedtest ahora usa **fast.com** (Netflix Open Connect) en lugar del servidor LibreSpeed interno de ETECSA: mide latencia, bajada y subida de tu internet internacional, sin navegador ni dependencias nuevas.
- `[speedtest]` se simplifica a `api_url`, `token`, `connections`, `max_duration` y `max_mb`. Las claves antiguas (`base_url`, `dl_url`, `ping_url`, `download_chunks`…) se ignoran sin error.
- Cada prueba dura `max_duration` segundos por dirección (10 por defecto) con tope de `max_mb` por dirección (50 MB).
- Panel del modo `watch` rediseñado con los colores estándar del terminal (texto normal y acentos cyan), borde simple, barras limpias, sin footer de estado, sin fecha duplicada y con el error del speedtest visible en la fila **Velocidad**.

### Añadido
- Medición de subida contra fast.com vía `api.fast.com/oca/speedtest` (el endpoint `api-global.netflix.com` que usa la web está bloqueado en la red Nauta).
- Ciudad del servidor e IP pública en el resultado (`server`, `ip`).

### Corregido
- El primer request ya no infla el jitter: se descarta un request de calentamiento antes de medir latencia.

## [0.3.0] - 2026-10-28

### Corregido
- `nauta-monitor` sin subcomando fallaba con `AttributeError: 'Namespace' object has no attribute 'interval'`.
  Ahora el comando por defecto (`watch`) recibe sus opciones también cuando no se escribe el subcomando.

### Cambiado
- Se eliminó el alias `once`: usa `nauta-monitor status` (acepta `--json`, `--no-speedtest` y `--no-history`).
- El arranque del speedtest en segundo plano ya no está duplicado en `watch`.
- El healthcheck de Docker usa `status`.

### Documentación
- README, uso, FAQ y solución de problemas actualizados al CLI simplificado.

## [0.2.0] - 2026-10-27

### Añadido
- Comando `init` - Asistente interactivo para crear `config.toml`
- Comando `doctor` - Diagnóstico completo de configuración, red y conectividad
- Comando `status` como alias de `once` (más intuitivo)
- Fecha estimada de fin de saldo en el panel
- Timestamp de última actualización en el panel
- Mensajes de error más claros con sugerencias
- Mejor ayuda con ejemplos en `--help`
- Documentación web con MkDocs Material

### Mejorado
- Panel más limpio con título "Nauta Monitor"
- Gráfico con texto "Consumo semanal (últimos 7 días)"
- Mensajes más descriptivos
- README más claro con inicio rápido en 3 pasos
- Mejor experiencia para nuevos usuarios

### Corregido
- Inconsistencia en valor por defecto de `upload_kib` (ahora 256)
- Test frágil dependiente de fecha en `test_week_chart_has_seven_days`
- Tests actualizados para nuevos comportamientos del panel

## [0.1.0] - Inicial

### Añadido
- Monitor en vivo con panel Rich
- Consulta de saldo y horas restantes
- Medición de velocidad con LibreSpeed
- Historial en JSONL
- Cálculo de consumo semanal
- Modo logs para contenedores
- Soporte Docker
- Healthcheck
- Dashboard para homeserver con tmux
- Alertas por saldo bajo
- Soporte para variables de entorno
- Publicación a GHCR
