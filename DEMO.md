# AgentKrak Demo Script

This is the short-video flow for the Kraken Agent Zero promotion. Keep it under two minutes and show the terminal clearly.

## Hook
AgentKrak is an autonomous market signal agent powered by the Kraken CLI. It turns live Kraken market data into transparent BUY, SELL, or HOLD decisions, then paper-trades them with auditable logs.

## Shot List
1. Show the project name and repo structure.
2. Run `python main.py doctor` to prove the local Kraken CLI health check.
3. Run `python main.py signals` to show BTC/USD, ETH/USD, and SOL/USD signal generation.
4. Run `python main.py stream --duration 30` to show clean live WebSocket price ticks through Kraken CLI.
5. Run `python main.py run --poll 60` and show the Rich dashboard updating.
6. Open `signals.log` and `trades.log` to show auditability.
7. Close with the judging pitch: CLI-native, explainable, useful, and safe paper trading.

## Exact Commands
```bash
pip install -r requirements.txt
kraken ticker BTCUSD -o json
python main.py doctor
python main.py signals
python main.py stream --duration 30
python main.py run --poll 60
python main.py report
```

## Docker Demo On Windows
```powershell
docker build -t agentkrak .
docker run --rm -it -v ${PWD}:/workspace agentkrak bash
```

Then inside Ubuntu:

```bash
kraken ticker BTCUSD -o json
python3 main.py doctor
python3 main.py signals
```

## Demo Narration
AgentKrak uses Kraken CLI subprocess calls for ticker, OHLC, order book, WebSocket ticker streaming via `kraken ws ticker`, and paper trading. It computes RSI, EMA crossovers, MACD, Bollinger Bands, and bid/ask spread quality, then only emits BUY or SELL when confidence clears the active UTC trading-session threshold. Every signal includes confidence and the exact conditions that fired, so the agent is explainable instead of a black box.

## Local Fallback
If you are recording before Kraken CLI is available on your machine, use the test shim only for UI rehearsal:

```powershell
$env:KRAKEN_COMMAND='.\.venv\Scripts\python.exe tests\fake_kraken.py'
python main.py signals
python main.py run --poll 0 --cycles 2
```

Do not submit the fallback output as the real Kraken CLI proof. The final video should include `kraken ticker BTCUSD -o json` or `python main.py doctor` passing against the real CLI.
