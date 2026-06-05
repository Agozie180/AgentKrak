# AgentKrak Judging Alignment

Kraken's Agent Zero promotion evaluates submissions by innovation and originality, technical execution, use of Kraken CLI functionality, clarity of explanation, and practical usefulness or impact.

## Innovation And Originality
AgentKrak is not a thin wrapper around a ticker command. It is an autonomous market signal agent that combines live market data, multi-factor technical analysis, liquidity checks, paper execution, and audit logs in one terminal workflow.

## Technical Execution
- Typed, modular Python package under `agentkrak/`.
- Dedicated Kraken CLI subprocess layer with retries, timeout handling, malformed JSON handling, and clear user errors.
- Indicator module for RSI(14), EMA(9/21), MACD(12/26/9), and Bollinger Bands(20,2).
- Unit tests for BUY, SELL, HOLD, confidence math, and all-five-condition edge cases.
- Rich terminal UI for a polished demo experience.

## Kraken CLI Usage
The project uses Kraken CLI as the only market and paper-trading interface:
- `kraken ticker BTCUSD -o json`
- `kraken ohlc BTCUSD --interval 60 -o json`
- `kraken orderbook BTCUSD --count 10 -o json`
- `kraken ws ticker BTC/USD -o json`
- `kraken paper buy BTCUSD <amount> -o json`
- `kraken paper sell BTCUSD <amount> -o json`

## Clarity Of Explanation
Every generated signal includes the pair, price, RSI, BUY/SELL/HOLD action, confidence score, and the exact conditions that triggered. The README and demo script explain the agent in plain English for judges and viewers.

## Practical Usefulness And Impact
AgentKrak gives traders a safe paper-trading environment for testing rule-based market hypotheses without real funds. The CSV logs make every decision reviewable, which is useful for demos, strategy iteration, and open-source collaboration.
