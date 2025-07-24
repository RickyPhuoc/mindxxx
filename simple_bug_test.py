#!/usr/bin/env python3
"""
🧪 SIMPLE TEST - Chỉ test 1 trade cụ thể
"""

import sys
sys.path.append('.')
from backtest_gridsearch_slbe_ts_Version3 import simulate_trade
import pandas as pd

def test_fixed_bug_simple():
    """Test đơn giản với trade data cứng"""
    
    print("🧪 SIMPLE TEST SAU KHI SỬA BUG")
    print("=" * 50)
    
    # Load candle data
    df = pd.read_csv("data chart full info.csv")
    print(f"📊 Loaded {len(df)} candles")
    
    # Create real trade data based on found candle
    pair = {
        'num': 139,
        'entryDt': '2024-05-14T01:00:00+07:00',  # From grep search line 6422
        'exitDt': '2024-05-14T05:00:00+07:00',   # 4 hours later
        'entryPrice': 0.009937,  # Low price from that candle
        'exitPrice': 0.009434,  # Will be recalculated
        'side': 'SHORT'
    }
    
    print(f"🎯 TESTING PARAMETERS:")
    print(f"   SL: 4.41% | BE: 1.76% | TS: 7.12%/0.26%")
    
    # Run simulation
    try:
        result = simulate_trade(
            pair=pair,
            df_candle=df,
            sl=4.41,
            be=1.76,
            ts_trig=7.12,
            ts_step=0.26
        )
        
        print(f"\n✅ SIMULATION SUCCESS:")
        print(f"   Entry Price: {result['entryPrice']:.6f}")
        print(f"   Exit Price: {result['exitPrice']:.6f}")
        print(f"   PnL: {result['pnl']:.2f}%")
        print(f"   Exit Reason: {result['exitReason']}")
        
        # Compare với kỳ vọng
        print(f"\n📊 SO SÁNH:")
        print(f"   Expected PnL: 4.88%")
        print(f"   Actual PnL: {result['pnl']:.2f}%")
        
        if abs(result['pnl'] - 4.88) < 0.1:
            print(f"   ✅ BUG FIXED!")
        else:
            print(f"   ❓ Different result")
            
        # Reality check
        actual_min = 0.009434
        if result['exitPrice'] >= actual_min:
            print(f"   ✅ Exit price reachable: {result['exitPrice']:.6f} >= {actual_min:.6f}")
        else:
            print(f"   🚨 Exit price unreachable: {result['exitPrice']:.6f} < {actual_min:.6f}")
        
    except Exception as e:
        print(f"🚨 ERROR: {e}")
        print("   Checking simulation function...")

if __name__ == '__main__':
    test_fixed_bug_simple()
