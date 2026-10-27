# Docker

## Despliegue rápido

```bash
# 1. Preparar
cp .env.example .env
cp config.example.toml config.toml
chmod 600 config.toml
mkdir -p data

# 2. Arrancar
docker compose up -d --build

# 3. Comprobar
docker compose ps
docker compose logs -f
```

## Características del contenedor

- **Modo logs**: Corre `nauta-monitor watch` sin terminal interactiva
- **Persistente**: El historial se guarda en `./data/history.jsonl`
- **Solo lectura**: `config.toml` se monta como `:ro`
- **Healthcheck**: Comprueba el portal cada 5 minutos. Si falla, marca el contenedor como `unhealthy`
- **Rotación de logs**: Configurado con `json-file` (10MB x 3)
- **Zona horaria**: Configurable con `TZ` (por defecto `America/Havana`)

## Usar imagen desde GHCR (sin Docker Hub)

En redes con bloqueo a Docker Hub:

```bash
docker compose -f docker-compose.yml -f deploy/docker-compose.server.yml pull
docker compose -f docker-compose.yml -f deploy/docker-compose.server.yml up -d
```

La imagen se publica automáticamente en GitHub Actions a `ghcr.io/<dueño>/nauta_monitor`.

## Comandos útiles

```bash
docker compose ps                    # Estado y health
docker compose logs -f               # Ver logs en tiempo real
docker compose restart              # Reiniciar
docker compose down                 # Parar
docker compose up -d --pull always   # Actualizar imagen
```
