# Registro de cambios

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
