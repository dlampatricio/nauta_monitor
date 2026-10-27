# Instalación

## Requisitos

- Python 3.9 o superior
- Conexión a la **red Nauta** de ETECSA (el monitor debe ejecutarse desde esa red)
- Acceso a `https://secure.etecsa.net:8443`

## Instalación local

=== "Windows (PowerShell/CMD)"

    ```bash
    git clone <repo>
    cd nauta_monitor
    python -m venv .venv
    .venv\Scripts\activate
    pip install -e .
    ```

=== "Linux / macOS"

    ```bash
    git clone <repo>
    cd nauta_monitor
    python -m venv .venv
    source .venv/bin/activate
    pip install -e .
    ```

## Instalación con Docker (recomendado para 24/7)

Ver [Docker](docker.md) para despliegue completo con `docker compose`.

## Siguiente paso

Después de instalar, configura el monitor con el asistente interactivo:

```bash
nauta-monitor init
nauta-monitor doctor
```
