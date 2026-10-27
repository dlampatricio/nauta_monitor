# Preguntas frecuentes

## General

**¿Funciona desde internet fuera de Cuba/red Nauta?**
No. El portal `secure.etecsa.net:8443` solo es accesible desde la red Nauta de ETECSA.

**¿Es seguro guardar mi contraseña en config.toml?**
El archivo solo lo lee el usuario que lo ejecuta. Usa `chmod 600 config.toml` en Linux. También puedes usar variables de entorno `NAUTA_USERNAME`/`NAUTA_PASS`.

**¿Puedo usarlo en varios equipos?**
Sí, pero cada instancia consulta el portal por separado. El historial es local por instalación.

## Uso

**¿Qué significa "cup/h"?**
Son los CUP que consume 1 hora de navegación según tu tarifa Nauta Hogar. Por defecto 12.5, pero puede variar según tu plan.

**¿Cómo se calcula "días restantes"?**
Se basa en tu **consumo real** de los últimos días (promedio de horas/día). Si no hay historial suficiente, muestra "Aún sin historial suficiente".

**¿Por qué se ignoran huecos largos en el gráfico?**
Para no distorsionar el promedio. Si el monitor estuvo apagado varios días, esos saltos se ignoran al calcular consumo.

**¿Qué hace "once/status"?**
Hace una única consulta y sale. Perfecto para scripts, cron o healthchecks.

## Docker

**¿Necesito terminal para verlo?**
No. En Docker corre en modo logs. Puedes verlo con `docker compose logs -f`.

**¿Puedo ver el panel en mi pantalla física?**
Sí, con el [dashboard para homeserver](homeserver.md) usando tmux.

**¿Se pierde el historial al actualizar?**
No, si montas el volumen `./data:/app/data` o usas `history.jsonl` persistente. En la configuración por defecto se guarda en `./data/history.jsonl`.

## Speedtest

**¿Es obligatorio el speedtest?**
No. Puedes poner `speedtest_interval = 0` o usar `--no-speedtest`.

**¿Por qué da valores bajos?**
Usa el servidor LibreSpeed de ETECSA en Cuba. Los resultados son representativos del enlace real en esa red.

## Desarrollo

**¿Puedo contribuir?**
Sí, revisa [Contribuir](contributing.md).

**¿Dónde se reportan bugs?**
En la sección Issues del repositorio.
