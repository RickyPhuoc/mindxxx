#!/usr/bin/env python3
"""
🧪 TEST TOOL GỐC ĐÃ SỬA: Verify logic candle-by-candle đã fix
"""

import pandas as pd
from backtest_gridsearch_slbe_ts_Version3 import simulate_trade, load_trade_csv, load_candle_csv, get_trade_pairs

def test_fixed_tool():
    print("🧪 TESTING FIXED TOOL GỐC với Trade #139")
    print("=" * 50)
    
    # Load candle data
    candles = load_candle_csv('data chart full info.csv')
    
    # Define Trade #139 manually
    trade139 = {
        'num': 139,
        'entryDt': pd.to_datetime('2025-06-20 22:00:00'),
        'exitDt': pd.to_datetime('2025-06-21 08:30:00'),
        'side': 'SHORT',
        'entryPrice': 0.009937,
        'exitPrice': 0.009919,  # original bug exit for comparison
    }
    
    print(f"📊 Trade #139: {trade139['side']} @ {trade139['entryPrice']:.6f}")
    print(f"   Original Exit: {trade139['exitPrice']:.6f}")
    print(f"   Original P&L: {(trade139['exitPrice']-trade139['entryPrice'])/trade139['entryPrice']*100:.2f}%")
    
    # Test với parameters từ optimization
    print("🔧 Testing với parameters: SL=4.41% BE=1.76% TS=7.12%/0.26%")
    result, log = simulate_trade(trade139, candles, 4.41, 1.76, 7.12, 0.26)
    
    if result:
        print(f"✅ FIXED TOOL RESULT:")
        print(f"   Exit Price: {result['exitPrice']:.6f}")
        print(f"   Exit Type: {result['exitType']}")
        print(f"   Final Profit: {result['pnlPct']:.2f}%")
        
        print()
        print("🔍 COMPARISON:")
        print(f"   Original (BUG): +10.24% @ 0.008919 (FANTASY)")
        print(f"   Fixed Tool: {result['pnlPct']:.2f}% @ {result['exitPrice']:.6f}")
        print(f"   Debug Sim: +0.05% @ 0.009932")
        
        # Validation
        if abs(result['pnlPct'] - 0.05) < 0.01:
            print("   ✅ PERFECT MATCH: Tool gốc đã hoạt động đúng!")
        else:
            print(f"   ⚠️ Gap: {abs(result['pnlPct'] - 0.05):.3f}% difference")
        
        # Reality check
        candles_period = candles[
            (candles['time'] >= pd.to_datetime('2025-06-20 22:00:00').tz_localize(candles['time'].dt.tz)) &
            (candles['time'] <= pd.to_datetime('2025-06-21 08:30:00').tz_localize(candles['time'].dt.tz))
        ]
        max_possible = (trade139['entryPrice'] - candles_period['low'].min()) / trade139['entryPrice'] * 100
        
        if result['pnlPct'] <= max_possible + 0.1:
            print(f"   ✅ REALISTIC: {result['pnlPct']:.2f}% ≤ {max_possible:.2f}% max possible")
        else:
            print(f"   ❌ UNREALISTIC: {result['pnlPct']:.2f}% > {max_possible:.2f}% max possible")
    else:
        print("❌ SIMULATION FAILED")
        if log:
            for l in log:
                print(f"   Log: {l}")

if __name__ == '__main__':
    test_fixed_tool()
