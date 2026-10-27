# Solución de problemas

## Errores comunes

### "No se pudo acceder a https://secure.etecsa.net:8443"

**Causa:** No estás conectado a la red Nauta de ETECSA.

**Solución:**
1. Conéctate al WiFi/cable Nauta
2. Ejecuta `nauta-monitor doctor` para verificar
3. Prueba desde otra terminal si hay conectividad

---

### "No se encontró el formulario de acceso en el portal"

**Causa:** Estás en red Nauta pero el portal responde de forma distinta o hay caché.

**Solución:**
1. Usa `nauta-monitor status --verbose` para ver la respuesta HTML
2. Verifica que no hay captive portal intermedio
3. Intenta con otra conexión Nauta

---

### "Faltan credenciales"

**Causa:** No hay usuario/contraseña configurados.

**Solución:**
```bash
nauta-monitor init
# o editar config.toml
# o usar NAUTA_USERNAME / NAUTA_PASS
```

---

### "Speedtest falló"

**Causa:** El servidor LibreSpeed de ETECSA no es accesible desde tu red.

**Solución:**
- Es **normal** y **no crítico**. El monitor sigue mostrando saldo/horas
- Puedes desactivarlo: `speedtest_interval = 0` en `config.toml`
- O cambiar el servidor en `[speedtest]` si conoces otro

---

### El panel no se actualiza / se queda congelado

**Solución:**
1. Pulsa `Ctrl+C` y vuelve a iniciar
2. Revisa logs: `nauta-monitor status` para ver errores
3. Ejecuta `nauta-monitor doctor`

---

### Docker: contenedor unhealthy

**Causa:** El healthcheck no puede consultar el portal.

**Solución:**
1. Verifica que el contenedor está en red Nauta
2. Revisa logs: `docker compose logs nauta-monitor`
3. El healthcheck consulta cada 5 min - puede tardar en actualizar estado

---

## Comandos de diagnóstico

```bash
# Diagnóstico completo
nauta-monitor doctor

# Ver config cargada
nauta-monitor status --verbose  # Muestra más info en errores

# Comprobar versión
nauta-monitor --version
```

## Consejos

- **Siempre en red Nauta:** El portal solo es accesible desde la red de ETECSA
- **Usa doctor primero:** `nauta-monitor doctor` te dice exactamente qué falla
- **Historial vacío:** Es normal la primera vez, el gráfico aparecerá tras unos días de uso
- **Hora incorrecta:** Configura `TZ` correctamente en Docker
