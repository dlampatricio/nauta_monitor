# Contribuir

¡Las contribuciones son bienvenidas!

## Formas de contribuir

- **Reportar bugs** - Abre un issue describiendo el problema
- **Sugerir mejoras** - Ideas para UX, comandos, o funcionalidades
- **Corregir errores** - Pull requests con fixes
- **Mejorar documentación** - Typos, aclaraciones, ejemplos
- **Añadir tests** - Mejorar cobertura

## Desarrollo local

```bash
git clone <repo> && cd nauta_monitor
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/macOS
pip install -e ".[dev]"
```

## Ejecutar tests

```bash
python -m pytest -v
```

## Estructura del proyecto

```
nauta_monitor/
├── cli.py        # Comandos y UI (Rich)
├── client.py     # Cliente del portal ETECSA
├── parser.py     # Parser HTML
├── config.py     # Configuración
├── display.py    # Renderizado
├── history.py    # Historial JSONL
├── speedtest.py  # LibreSpeed client
└── calc.py       # Cálculos
```

## Guía para PRs

1. Fork del repositorio
2. Crear rama: `git checkout -b feature/mi-mejora`
3. Hacer cambios con código claro
4. Añadir/actualizar tests si aplica
5. Ejecutar tests: `pytest`
6. Commit con mensaje descriptivo
7. Abrir Pull Request

## Estilo

- Código Python claro y legible
- Comentarios solo cuando necesario
- Mensajes al usuario en español
- Mantener compatibilidad con Python 3.9+
- Seguir patrones existentes del proyecto
