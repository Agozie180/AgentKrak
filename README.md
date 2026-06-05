# ⚡ AgentKrak — Autonomous Crypto Signal Agent
> Built for the Kraken CLI Build Competition | $25,000 Prize Pool

## What it does
AgentKrak is a Python terminal agent that uses the Kraken CLI to fetch live crypto market data, compute technical indicators, and produce BUY / SELL / HOLD signals with transparent confidence scoring. It also runs a paper trading simulation, logs every decision, and displays a Rich-powered live dashboard suitable for a short demo video.

## Demo
Watch the demo on X: [link]

## Features
- Kraken CLI data pipeline: pulls tickers, candles, order books, and live streams through `kraken` subprocess calls.
- Multi-factor signal engine: combines RSI, EMA crossovers, MACD crossovers, Bollinger Bands, and spread quality.
- Paper trading loop: executes Kraken CLI paper buy/sell commands with configurable 5% risk sizing.
- Live terminal dashboard: color-coded prices, signals, errors, and PnL using Rich.
- Competition-ready diagnostics and docs: `doctor`, `DEMO.md`, and `JUDGING.md` help prove readiness quickly.
- Audit logs: writes `signals.log` and `trades.log` as CSV files for review and demos.

## Prerequisites
- Kraken CLI:

```bash
curl --proto '=https' --tlsv1.2 -LsSf \
  https://github.com/krakenfx/kraken-cli/releases/latest/download/kraken-cli-installer.sh | sh
```

- Python 3.10+

Kraken CLI currently supports macOS and Linux directly. On Windows, use WSL and make sure the `kraken` binary is available on PATH, or set `KRAKEN_COMMAND` to its executable path before running AgentKrak. Wrapped commands are supported, for example `KRAKEN_COMMAND="wsl kraken"` when WSL is configured.

## Installation
```bash
git clone <your-repo-url>
cd AgentKrak
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
kraken ticker BTCUSD -o json
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
kraken ticker BTCUSD -o json
```

`pandas-ta` is listed as an optional competition dependency but skipped by default because it is currently unavailable in some package indexes and can fail on newer Python versions. AgentKrak computes the required RSI, EMA, MACD, and Bollinger Band indicators locally, so the app remains fully functional.

## Docker On Windows
If you do not have Linux/macOS or a working WSL distro, Docker Desktop can run AgentKrak in Ubuntu:

```powershell
docker build -t agentkrak .
docker run --rm -it -v ${PWD}:/workspace agentkrak bash
```

Inside the container:

```bash
kraken ticker BTCUSD -o json
python3 main.py doctor
python3 main.py signals
python3 -m pytest tests
```

## Usage
Check local demo readiness:

```bash
python main.py doctor
```

Example output:

```text
Kraken command      OK       kraken
Live Kraken ticker  OK       BTC/USD $68,420.10
```

Start the autonomous agent:

```bash
python main.py run --pairs BTC/USD,ETH/USD,SOL/USD --interval 1h --capital 1000 --poll 60
```

Example output:

```text
AgentKrak v1.0 dashboard with live prices, latest signals, and paper trading PnL.
```

Generate one-shot signals:

```bash
python main.py signals
```

Example output:

```text
Pair     Signal   RSI    Confidence
BTC/USD  HOLD     51.20  40%
```

Stream live ticks for 60 seconds:

```bash
python main.py stream --duration 60
```

Example output:

```json
{"pair":"BTC/USD","price":68420.1,"timestamp":"2026-05-28T20:00:00Z"}
```

Print the paper trading summary:

```bash
python main.py report
```

Example output:

```text
Total Trades  Wins  Losses  Win Rate  Total PnL
3             2     1       66.67%    $18.42
```

## How the Signal Engine Works
The engine checks five confluence conditions for each market: RSI direction, EMA(9/21) crossover, MACD(12/26/9) crossover, Bollinger Band position, and bid/ask spread below 0.15%. BUY requires at least three bullish conditions, SELL requires at least three bearish conditions, and HOLD is used otherwise. Confidence is the number of triggered conditions multiplied by 20, so three conditions equals 60% and all five equals 100%.

## Paper Trading
AgentKrak uses Kraken CLI paper mode, so no real funds are needed. On BUY it calls `kraken paper buy <PAIR> <amount> -o json`; on SELL it calls `kraken paper sell <PAIR> <amount> -o json`. Position size is 5% of current paper capital, starting from the configurable default of $1,000.

## Architecture
The root `main.py` is a thin launcher for `python main.py ...`. The application code lives in `agentkrak/`: `main.py` defines the Click commands and agent loop, `fetcher.py` wraps Kraken CLI subprocess calls, `indicators.py` computes market indicators, `signals.py` makes confluence decisions, `paper_trader.py` simulates trades, `reporter.py` renders the terminal dashboard, `logger.py` writes CSV signal logs, and `config.py` centralizes settings. Tests live in `tests/test_signals.py`, with `tests/fake_kraken.py` available only for local end-to-end verification when the real Kraken CLI is not installed.

## Competition Submission Notes
Kraken's Agent Zero promotion asks entrants to build with Kraken CLI and submit a video or explainer. `DEMO.md` gives the recording flow, and `JUDGING.md` maps AgentKrak to the judging criteria: innovation, technical execution, Kraken CLI usage, clarity, and practical usefulness.

Run the full local test suite:

```bash
python -m pytest tests
```

## License
MIT
