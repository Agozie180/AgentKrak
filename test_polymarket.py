import asyncio
from bot.crypto import CryptoPredictor
from bot.http import HttpClient
from bot.formatting import polymarket_message

async def test():
    print('Testing enhanced polymarket BTC 5min prediction with oracle aggregation...\n')
    predictor = CryptoPredictor(HttpClient())
    prediction = await predictor.polymarket_btc_5min()
    
    print('📊 Prediction Result:')
    print(f'Direction: {prediction.direction}')
    print(f'Confidence: {prediction.confidence}%')
    print(f'Reference Price: ${prediction.reference_price:,.2f}')
    print(f'\n🔗 Oracle Settlement:')
    if prediction.settlement:
        s = prediction.settlement
        print(f'  ✓ Weighted Median: ${s.weighted_median_price:,.2f}')
        print(f'  ✓ Weighted Mean: ${s.weighted_mean_price:,.2f}')
        print(f'  ✓ Oracle Consensus: {s.oracle_consensus_score:.1f}%')
        print(f'  ✓ Max Price Divergence: {s.max_price_divergence_pct:.3f}%')
        print(f'  ✓ Settlement Confidence: {s.settlement_confidence:.0f}%')
        print(f'  ✓ Sources Used: {s.price_sources_used}')
        print(f'  ✓ Oracle-Backed: {s.is_oracle_backed}')
    
    print(f'\n📈 Analysis Reasons:')
    for i, reason in enumerate(prediction.reasons, 1):
        print(f'  {i}. {reason}')
    
    print(f'\n📲 Formatted Message:')
    print('─' * 60)
    print(polymarket_message(prediction))
    print('─' * 60)

asyncio.run(test())
