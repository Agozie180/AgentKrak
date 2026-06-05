# ⚡ AgentKrak — Autonomous Crypto Signal Agent
> Built for the Kraken CLI Build Competition / Agent Zero promotion

AgentKrak is a professional terminal trading agent that uses the Kraken CLI as its only market-data and paper-trading interface. It fetches live ticker, OHLC, order book, and WebSocket data; computes RSI, EMA, MACD, and Bollinger Bands; generates explainable BUY / SELL / HOLD decisions; and logs every signal and paper trade for review.

## Demo
Watch the demo on X or YouTube: [link]

## Features
- Kraken CLI native data pipeline: ticker, OHLC, order book, WebSocket stream, and paper mode all flow through `kraken`.
- Multi-confluence signal engine: RSI, EMA crossovers, MACD crossovers, Bollinger Bands, and spread quality.
- Rich live dashboard: polished terminal UI with live prices, signals, confidence, errors, and paper PnL.
- Paper trading simulation: 5% risk sizing, CSV trade logs, paper account auto-init retry.
- Competition-ready packaging: Docker support, doctor command, tests, demo script, and judging alignment docs.

## Prerequisites
- Docker Desktop on Windows, or Linux/macOS with Kraken CLI installed.
- Python 3.10+ if running outside Docker.

Install Kraken CLI directly on Linux/macOS:

```bash
curl --proto '=https' --tlsv1.2 -LsSf \
  https://github.com/krakenfx/kraken-cli/releases/latest/download/kraken-cli-installer.sh | sh
```

## Docker Quick Start
This is the recommended Windows path because Kraken CLI runs cleanly inside Ubuntu:

```powershell
docker build -t agentkrak .
docker run --rm -it -v ${PWD}:/workspace agentkrak bash
```

Inside the container:

```bash
kraken ticker BTCUSD -o json
python3 main.py doctor
python3 main.py signals
python3 main.py stream --duration 30
python3 main.py run --poll 60
python3 main.py report
python3 -m pytest tests
```

## Local Python Usage
```bash
pip install -r requirements.txt
python main.py doctor
python main.py signals
python main.py stream --duration 60
python main.py run --pairs BTC/USD,ETH/USD,SOL/USD --interval 1h --capital 1000 --poll 60
python main.py report
```

`pandas-ta` is listed as an optional competition dependency but skipped by default because it is unavailable in some package indexes and can fail on newer Python versions. AgentKrak computes the required RSI, EMA, MACD, and Bollinger Band indicators locally, so the app remains fully functional.

## Signal Engine
BUY requires three or more bullish conditions:

- RSI(14) < 45 and rising
- EMA(9) crosses above EMA(21)
- MACD crosses above signal
- Close is at or below the lower Bollinger Band
- Bid/ask spread is below 0.15%

SELL requires three or more bearish conditions:

- RSI(14) > 60 and falling
- EMA(9) crosses below EMA(21)
- MACD crosses below signal
- Close is at or above the upper Bollinger Band
- Bid/ask spread is below 0.15%

Confidence is `conditions_met * 20`, capped at 100.

## Project Structure
```text
agentkrak/
  main.py          Click commands and agent loop
  fetcher.py       Kraken CLI subprocess integration
  indicators.py    RSI, EMA, MACD, Bollinger Bands
  signals.py       BUY / SELL / HOLD engine
  reporter.py      Rich terminal dashboard
  logger.py        signals.log CSV writer
  paper_trader.py  Kraken paper mode simulation
  config.py        Settings
tests/
  test_fetcher.py
  test_paper_trader.py
  test_signals.py
  fake_kraken.py
```

## Submission Notes
- [DEMO.md](DEMO.md) gives the short video flow.
- [JUDGING.md](JUDGING.md) maps AgentKrak to Kraken's judging criteria.
- `python main.py doctor` proves local readiness before recording.

## License
MIT
