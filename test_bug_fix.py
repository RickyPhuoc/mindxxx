#!/usr/bin/env python3
"""
🧪 TEST BUG FIX - Kiểm tra tool gốc sau khi sửa
"""

import sys
sys.path.append('.')
from backtest_gridsearch_slbe_ts_Version3 import simulate_trade
import pandas as pd

def test_fixed_tool():
    """Test tool gốc sau khi sửa bug"""
    
    print("🧪 TEST TOOL GỐC SAU KHI SỬA BUG")
    print("=" * 50)
    
    # Load data
    df = pd.read_csv("data chart full info.csv")
    
    # Trade #139 data structure (find actual trade data)
    # Find Trade #139 from tradelist
    trades_df = pd.read_csv("tradelist-fullinfo.csv")
    trade_139 = trades_df[trades_df['num'] == 139].iloc[0]
    
    print(f"📊 FOUND TRADE #139:")
    print(f"   Entry DT: {trade_139['entryDt']}")
    print(f"   Exit DT: {trade_139['exitDt']}")  
    print(f"   Entry Price: {trade_139['entryPrice']:.6f}")
    print(f"   Exit Price: {trade_139['exitPrice']:.6f}")
    print(f"   PnL: {trade_139['pnl']:.2f}%")
    
    # Create pair dict for simulate_trade
    pair = {
        'num': 139,
        'entryDt': trade_139['entryDt'],
        'exitDt': trade_139['exitDt'],
        'entryPrice': trade_139['entryPrice'],
        'exitPrice': trade_139['exitPrice'],
        'side': trade_139['side']
    }
    
    # Test parameters from reality check optimizer  
    params = {
        'sl': 4.41,        # From reality check optimizer  
        'be': 1.76,        # From reality check optimizer
        'ts_trig': 7.12,   # From reality check optimizer  
        'ts_step': 0.26    # From reality check optimizer
    }
    
    print(f"📊 TESTING TRADE #139 WITH OPTIMIZED PARAMETERS:")
    print(f"   SL: {params['sl']:.2f}%")
    print(f"   BE: {params['be']:.2f}%") 
    print(f"   TS Trigger: {params['ts_trig']:.2f}%")
    print(f"   TS Step: {params['ts_step']:.2f}%")
    
    # Run simulation with correct parameters
    result = simulate_trade(
        pair=pair,
        df_candle=df,
        sl=params['sl'],
        be=params['be'],
        ts_trig=params['ts_trig'],
        ts_step=params['ts_step']
    )
    
    print(f"\n📈 KẾT QUẢ SAU SỬA BUG:")
    print(f"   Entry Price: {result['entryPrice']:.6f}")
    print(f"   Exit Price: {result['exitPrice']:.6f}")
    print(f"   PnL: {result['pnl']:.2f}%")
    print(f"   Exit Reason: {result['exitReason']}")
    
    # Reality check với actual data
    entry_price = 0.009937
    actual_min = 0.009434
    
    print(f"\n🔍 REALITY CHECK:")
    print(f"   Expected Entry: {entry_price:.6f}")
    print(f"   Actual Entry: {result['entryPrice']:.6f}")
    print(f"   Match: {abs(result['entryPrice'] - entry_price) < 0.000001}")
    
    print(f"\n   Exit Price: {result['exitPrice']:.6f}")
    print(f"   Actual Min: {actual_min:.6f}")
    print(f"   Reachable: {result['exitPrice'] >= actual_min}")
    
    if result['exitPrice'] >= actual_min:
        print(f"   ✅ FIXED: Exit price is reachable!")
    else:
        print(f"   🚨 STILL BROKEN: Exit price is unreachable!")
        
    # So sánh với kỳ vọng
    expected_pnl = 4.88  # From diagnosis
    print(f"\n📊 SO SÁNH KỲ VỌNG:")
    print(f"   Expected PnL: {expected_pnl:.2f}%")
    print(f"   Actual PnL: {result['pnl']:.2f}%")
    print(f"   Difference: {abs(result['pnl'] - expected_pnl):.2f}%")
    
    if abs(result['pnl'] - expected_pnl) < 0.1:
        print(f"   ✅ PERFECT MATCH!")
    else:
        print(f"   ⚠️ Still some difference")

if __name__ == '__main__':
    test_fixed_tool()
