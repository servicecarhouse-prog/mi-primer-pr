# Trading bot (modo simulado / paper trading)

Bot educativo de trading algorítmico. Usa datos públicos de mercado
(API pública de Binance, sin necesidad de clave ni cuenta) para tomar
decisiones de compra/venta con una estrategia simple:

- **Entrada:** cruce de medias móviles (SMA rápida por encima de la lenta).
- **Salida:** lo que ocurra primero entre:
  - **Take-profit:** el precio sube un `take_profit_pct` % desde la entrada.
  - **Trailing stop:** el precio cae un `trailing_stop_pct` % desde el máximo
    alcanzado desde la entrada (protege ganancias a medida que el precio sube).

## ⚠️ Importante

Este bot **no está conectado a ningún broker, exchange ni cuenta real**.
Todas las operaciones son simuladas contra un balance virtual en memoria.
No usa, pide ni acepta claves de API de trading. Es solo para aprender y
probar la estrategia antes de considerar (con mucha cautela) operar con
dinero real en una plataforma regulada.

## Instalación

```bash
cd trading_bot
pip install -r requirements.txt
```

## Uso

**Backtest** sobre datos históricos:

```bash
python bot.py backtest --symbol BTCUSDT --interval 1h --limit 500
```

**Paper trading** en vivo (bucle sobre precio actual, sin dinero real):

```bash
python bot.py paper --symbol BTCUSDT --interval 1m --iterations 60 --sleep 5
```

## Parámetros configurables

| Flag | Descripción | Default |
|---|---|---|
| `--symbol` | Par a operar (formato Binance, ej. `BTCUSDT`) | `BTCUSDT` |
| `--interval` | Intervalo de las velas (`1m`, `5m`, `1h`, `1d`, ...) | `1h` |
| `--initial-balance` | Balance virtual inicial en USD | `1000.0` |
| `--fast-window` | Ventana de la SMA rápida | `10` |
| `--slow-window` | Ventana de la SMA lenta | `30` |
| `--take-profit-pct` | % de ganancia para cerrar | `10.0` |
| `--trailing-stop-pct` | % de caída desde el máximo para cerrar | `5.0` |
| `--iterations` | (paper) número de iteraciones del bucle | `30` |
| `--sleep` | (paper) segundos entre cada comprobación de precio | `5.0` |

## Siguientes pasos (si algún día se quiere operar con dinero real)

1. Verificar que la plataforma/broker esté regulada por el organismo
   correspondiente en tu país (CNMV, SEC, FINRA, etc.).
2. Confirmar que expone una API de trading documentada.
3. Generar claves de API con permisos **solo de trading, nunca de retiro**.
4. Empezar con capital mínimo y límites de riesgo estrictos.
