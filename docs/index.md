# nauta-monitor

Monitor sencillo y claro para tu cuenta **Nauta Hogar**. Consulta el saldo en CUP, calcula las horas de servicio restantes, estima cuándo se te acabará y mide la velocidad real contra el servidor LibreSpeed de ETECSA.

## Características

- **Panel en vivo**: Vista limpia con saldo, horas restantes, consumo y velocidad.
- **Cálculo inteligente**: Horas restantes según tu tarifa (`cup/h`) y proyección basada en tu consumo real.
- **Gráfico semanal**: Consumo de los últimos 7 días con barras visuales.
- **Alertas**: Aviso cuando queden pocas horas, con comando opcional.
- **Modo logs**: Funciona sin TTY (ideal para Docker/systemd).
- **Historial**: Guarda muestras en `history.jsonl` para calcular tendencias.
- **Diagnóstico integrado**: Comandos `init` y `doctor` para ponerlo en marcha rápido.

## Inicio rápido

```bash
# Instalar
git clone <repo> && cd nauta_monitor
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -e .

# Configurar
nauta-monitor init
nauta-monitor doctor

# Usar
nauta-monitor  # Panel en vivo
nauta-monitor status  # Consulta única
```

## ¿Necesitas ayuda?

- [Instalación](installation.md) - Pasos detallados
- [Configuración](configuration.md) - Archivo `config.toml`, variables de entorno
- [Uso](usage.md) - Comandos, panel, modo logs
- [Solución de problemas](troubleshooting.md) - Errores comunes
- [Preguntas frecuentes](faq.md)
