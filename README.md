# ⚡ AgentKrak — Autonomous Crypto Signal Agent
> Built for the Kraken CLI Build Competition / Agent Zero promotion

AgentKrak is a professional terminal trading agent that uses the Kraken CLI as its only market-data and paper-trading interface. It fetches live ticker, OHLC, order book, and WebSocket data; computes RSI, EMA, MACD, and Bollinger Bands; generates explainable BUY / SELL / HOLD decisions; and logs every signal and paper trade for review.

## Demo
Watch the demo on YouTube: https://youtu.be/VoOKGWCIZCk?si=ZuNaSUe578tiR1NF

## Features
- Kraken CLI native data pipeline: ticker, OHLC, order book, WebSocket stream, and paper mode all flow through `kraken`.
- Multi-confluence signal engine: RSI, EMA crossovers, MACD crossovers, Bollinger Bands, and spread quality.
- Confidence thresholding: BUY/SELL ideas below the active session minimum become `NO TRADE` and never reach paper execution.
- UTC session-aware thresholds: Asian, London, New York, and Off-session filters automatically raise or lower the minimum confirmation requirement.
- Risk-managed paper trading: 5% risk sizing plus stop-loss, take-profit, and risk/reward levels on every actionable signal.
- Rich live dashboard: polished terminal UI with live prices, signals, confidence, risk levels, errors, and paper PnL.
- Competition-ready packaging: Docker support, doctor command, tests, demo script, and judging alignment docs.

## Prerequisites
- Docker Desktop on Windows, or Linux/macOS with Kraken CLI installed.
- Python 3.10+ if running outside Docker.

Install Kraken CLI directly on Linux/macOS:

```bash
curl --proto '=https' --tlsv1.2 -LsSf \
  https://github.com/krakenfx/kraken-cli/releases/latest/download/kraken-cli-installer.sh | sh
```


## Windows Same-Folder Setup
If you are on Windows, build the Docker image once from this project folder:

```powershell
docker build -t agentkrak .
python main.py doctor
```

The repo includes `kraken.cmd`, a local wrapper that lets AgentKrak call the Kraken CLI through Docker. That means `python main.py doctor`, `python main.py signals`, `python main.py stream`, and `python main.py run` can work from this same folder without installing a native Windows `kraken.exe`. If `doctor` says the Kraken command is missing or times out, make sure Docker Desktop is running and that you are in the AgentKrak repo folder. On the first run, Docker may need a few extra seconds to start the Kraken CLI container.
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
python main.py run --pairs BTC/USD,ETH/USD,SOL/USD --interval 1h --capital 1000 --poll 60 --stop-loss 0.02 --take-profit 0.04
python main.py report
python -m pytest tests
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

Confidence is `conditions_met * 20`, capped at 100. AgentKrak automatically detects the current UTC trading session and applies that session's minimum confidence threshold before any paper trade can execute.

## Trading Sessions
AgentKrak uses session-aware confirmation filters:

- Asian session, 23:00-06:00 UTC: minimum confidence 65%; trending moves, cleaner signals.
- London session, 07:00-12:00 UTC: minimum confidence 72%; high volatility, false breaks possible.
- New York session, 13:00-21:00 UTC: minimum confidence 75%; highest volume, needs strong confirmation.
- Off session, 21:00-23:00 UTC plus transition gaps: minimum confidence 60%; low liquidity, trade carefully.

Every dashboard, report, doctor output, and logged signal includes the active session name and threshold. If a BUY or SELL setup exists but confidence is below the active session threshold, AgentKrak shows `NO TRADE` with a clear reason and refuses to execute the paper order. Advanced users can still override the session threshold with `--min-confidence`.

Actionable BUY signals include stop-loss below entry and take-profit above entry. Actionable SELL signals invert those levels. Defaults are 2% stop-loss and 4% take-profit, producing a 2:1 reward/risk profile that can be tuned with `--stop-loss` and `--take-profit`. HOLD rows show `-` for SL/TP because no trade should be placed; filtered BUY/SELL candidates can still show candidate risk levels while remaining blocked from paper trading.

## Reliability
Crypto APIs and CLI wrappers can be noisy under load, so AgentKrak wraps every Kraken CLI request with retries, timeouts, JSON validation, and Kraken error-payload detection. Failures are surfaced in the dashboard instead of crashing the live agent loop.

`python main.py stream` uses `kraken ws ticker` and prints clean price ticks only. WebSocket status, heartbeat, and subscription control messages are filtered out so the demo shows readable live market data.

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
