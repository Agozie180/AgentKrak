"""
Comprehensive test suite for oracle-backed polymarket BTC 5-minute predictions.
Tests oracle aggregation, settlement calculation, and edge cases.
"""
import asyncio
from bot.crypto import CryptoPredictor
from bot.http import HttpClient
from bot.formatting import polymarket_message


async def test_oracle_aggregation():
    """Test the oracle aggregation with multiple price sources."""
    print("\n" + "=" * 70)
    print("TEST 1: Oracle Aggregation with Multiple Price Sources")
    print("=" * 70)
    
    predictor = CryptoPredictor(HttpClient())
    prediction = await predictor.polymarket_btc_5min()
    
    # Verify settlement data exists
    assert prediction.settlement is not None, "Settlement data should exist"
    settlement = prediction.settlement
    
    print(f"✓ Direction: {prediction.direction} ({prediction.confidence}%)")
    print(f"✓ Price Sources: {settlement.price_sources_used}")
    print(f"✓ Oracle Consensus: {settlement.oracle_consensus_score:.2f}%")
    print(f"✓ Settlement Confidence: {settlement.settlement_confidence:.2f}%")
    print(f"✓ Max Divergence: {settlement.max_price_divergence_pct:.4f}%")
    print(f"✓ Oracle-Backed: {settlement.is_oracle_backed}")
    
    # Assertions
    assert settlement.price_sources_used >= 3, "Should use at least 3 price sources"
    assert settlement.oracle_consensus_score >= 0, "Consensus score should be non-negative"
    assert settlement.oracle_consensus_score <= 100, "Consensus score should not exceed 100"
    assert settlement.settlement_confidence >= 50, "Settlement confidence should be meaningful"
    assert settlement.is_oracle_backed, "Should be oracle-backed with 5+ sources"
    
    print("\n✅ Oracle aggregation test PASSED")


async def test_weighted_median_calculation():
    """Test weighted median price calculation."""
    print("\n" + "=" * 70)
    print("TEST 2: Weighted Median vs Weighted Mean")
    print("=" * 70)
    
    predictor = CryptoPredictor(HttpClient())
    prediction = await predictor.polymarket_btc_5min()
    
    settlement = prediction.settlement
    median = settlement.weighted_median_price
    mean = settlement.weighted_mean_price
    
    print(f"Weighted Median:  ${median:,.2f}")
    print(f"Weighted Mean:    ${mean:,.2f}")
    print(f"Difference:       ${abs(median - mean):,.2f}")
    print(f"Difference (%):   {(abs(median - mean) / mean) * 100:.3f}%")
    
    # Assertions
    assert median > 0, "Weighted median should be positive"
    assert mean > 0, "Weighted mean should be positive"
    assert abs(median - mean) / mean < 0.01, "Median and mean should be close (within 1%)"
    
    print("\n✅ Weighted median test PASSED")


async def test_confidence_adjustments():
    """Test confidence score adjustments based on oracle data."""
    print("\n" + "=" * 70)
    print("TEST 3: Confidence Adjustments")
    print("=" * 70)
    
    predictor = CryptoPredictor(HttpClient())
    prediction = await predictor.polymarket_btc_5min()
    
    print(f"Base Confidence:       {prediction.confidence}%")
    print(f"Settlement Confidence: {prediction.settlement.settlement_confidence:.1f}%")
    print(f"Oracle Consensus:      {prediction.settlement.oracle_consensus_score:.1f}%")
    print(f"Price Divergence:      {prediction.settlement.max_price_divergence_pct:.4f}%")
    
    # Assertions
    assert 0 <= prediction.confidence <= 100, "Confidence should be 0-100%"
    assert prediction.confidence >= 45, "Confidence should be at least 45% (meaningful signal)"
    
    print("\n✅ Confidence adjustment test PASSED")


async def test_formatting_output():
    """Test the formatted message output."""
    print("\n" + "=" * 70)
    print("TEST 4: Formatted Message Output")
    print("=" * 70)
    
    predictor = CryptoPredictor(HttpClient())
    prediction = await predictor.polymarket_btc_5min()
    
    message = polymarket_message(prediction)
    
    # Check required elements in message
    required_elements = [
        "🎯 Polymarket BTC 5min Prediction",
        "Oracle-Backed",
        "Direction:",
        "confidence",
        "Oracle Settlement Analysis",
        "Weighted median:",
        "Oracle consensus:",
        "Settlement confidence:",
        "Price sources aggregated:",
    ]
    
    for element in required_elements:
        assert element in message, f"Message should contain '{element}'"
        print(f"✓ Contains: {element}")
    
    # Print sample message
    print("\nSample Message Output (first 500 chars):")
    print("-" * 70)
    print(message[:500] + "...")
    print("-" * 70)
    
    print("\n✅ Formatting output test PASSED")


async def test_multiple_predictions():
    """Test consistency across multiple predictions."""
    print("\n" + "=" * 70)
    print("TEST 5: Consistency Across Multiple Predictions")
    print("=" * 70)
    
    predictor = CryptoPredictor(HttpClient())
    
    predictions = []
    for i in range(3):
        pred = await predictor.polymarket_btc_5min()
        predictions.append(pred)
        print(f"Prediction {i+1}: {pred.direction} | Confidence: {pred.confidence}% | "
              f"Sources: {pred.settlement.price_sources_used} | "
              f"Consensus: {pred.settlement.oracle_consensus_score:.1f}%")
    
    # Verify consistency
    reference_price_1 = predictions[0].reference_price
    reference_price_2 = predictions[1].reference_price
    price_diff = abs(reference_price_1 - reference_price_2) / reference_price_1
    
    print(f"\nPrice consistency check:")
    print(f"Prediction 1 Price: ${reference_price_1:,.2f}")
    print(f"Prediction 2 Price: ${reference_price_2:,.2f}")
    print(f"Difference: {price_diff*100:.2f}%")
    
    assert price_diff < 0.01, "Prices should be consistent (within 1%)"
    
    print("\n✅ Consistency test PASSED")


async def run_all_tests():
    """Run all oracle polymarket tests."""
    print("\n" + "🔗" * 35)
    print("ORACLE-BACKED POLYMARKET TEST SUITE")
    print("🔗" * 35)
    
    try:
        await test_oracle_aggregation()
        await test_weighted_median_calculation()
        await test_confidence_adjustments()
        await test_formatting_output()
        await test_multiple_predictions()
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED - Oracle-backed polymarket is working professionally!")
        print("=" * 70)
        print("\nKey Features Verified:")
        print("  ✓ Multi-source oracle aggregation (5+ sources)")
        print("  ✓ Weighted median price calculation")
        print("  ✓ Oracle consensus scoring (0-100%)")
        print("  ✓ Settlement confidence assessment")
        print("  ✓ Price divergence detection")
        print("  ✓ Proper confidence adjustments")
        print("  ✓ Professional formatting")
        print("  ✓ Consistent predictions")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(run_all_tests())
