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
1. Usa `nauta-monitor --verbose status` para ver la respuesta HTML
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

**Causa:** No hay internet internacional activo (sesión Nauta caída) o `api.fast.com` no es accesible.

**Solución:**
- Es **normal** y **no crítico**. El monitor sigue mostrando saldo/horas
- Comprueba que puedes abrir `https://fast.com` en el navegador
- Si tu red bloquea fast.com, desactívalo: `speedtest_interval = 0` en `config.toml`
- Si cambió el token, ponlo en `[speedtest] token = "..."`

---

### `'.venv' is not recognized as an internal or external command` (Windows)

**Causa:** En `cmd.exe` la ruta se escribe con **barras invertidas** (`\`), no con `/`.

**Solución:**
```bat
.venv\Scripts\activate
```

- PowerShell: `.venv\Scripts\Activate.ps1` (si bloquea scripts: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`).
- Instala el proyecto con el punto final: `pip install -e .` (no `pip install -e`).
- Comprueba que el comando existe con `where nauta-monitor`.

---

### `AttributeError: 'Namespace' object has no attribute 'interval'`

**Causa:** Bug de las versiones ≤ 0.2.0 al ejecutar `nauta-monitor` sin subcomando.

**Solución:** Actualiza a 0.3.0 (o usa `nauta-monitor watch` mientras tanto).

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
nauta-monitor --verbose status  # Muestra el HTML crudo del portal

# Comprobar versión
nauta-monitor --version
```

## Consejos

- **Siempre en red Nauta:** El portal solo es accesible desde la red de ETECSA
- **Usa doctor primero:** `nauta-monitor doctor` te dice exactamente qué falla
- **Historial vacío:** Es normal la primera vez, el gráfico aparecerá tras unos días de uso
- **Hora incorrecta:** Configura `TZ` correctamente en Docker
