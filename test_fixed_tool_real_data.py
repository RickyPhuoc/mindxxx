#!/usr/bin/env python3
"""
🧪 TEST TOOL GỐC THỰC TẾ sau khi sửa bug
So sánh kết quả tool gốc vs simulation thực chiến
"""

import sys
sys.path.append('.')
from backtest_gridsearch_slbe_ts_Version3 import simulate_trade
import pandas as pd

def test_fixed_tool_with_real_trade():
    """Test tool gốc sau sửa bug với trade thực tế"""
    
    print("🧪 TEST TOOL GỐC SAU SỬA BUG - REAL DATA")
    print("=" * 60)
    
    # Load candle data
    df = pd.read_csv("data chart full info.csv")
    
    # Create Trade #139 structure theo format tool gốc
    pair = {
        'num': 139,
        'entryDt': '2025-06-20T22:00:00+07:00',  # From simulation
        'exitDt': '2025-06-21T08:30:00+07:00',   # End time
        'entryPrice': 0.009937,
        'exitPrice': 0.008919,  # Original (will be recalculated)
        'side': 'SHORT'
    }
    
    print("📊 TEST PARAMETERS:")
    print(f"   SL: 4.41% | BE: 1.76% | TS: 7.12%/0.26%")
    print(f"   Entry: {pair['entryPrice']:.6f}")
    print(f"   Period: {pair['entryDt']} → {pair['exitDt']}")
    
    print(f"\n🔄 EXPECTED FROM SIMULATION:")
    print(f"   Exit Price: 0.009452")
    print(f"   Profit: 4.88%")
    print(f"   Exit Reason: SL_HIT at candle 6")
    
    # Run with original tool
    try:
        result = simulate_trade(
            pair=pair,
            df_candle=df,
            sl=4.41,
            be=1.76,
            ts_trig=7.12,
            ts_step=0.26
        )
        
        print(f"\n✅ TOOL GỐC KẾT QUẢ (sau sửa bug):")
        print(f"   Entry Price: {result['entryPrice']:.6f}")
        print(f"   Exit Price: {result['exitPrice']:.6f}")
        print(f"   PnL: {result['pnl']:.2f}%")
        print(f"   Exit Reason: {result['exitReason']}")
        
        # So sánh với simulation
        expected_exit = 0.009452
        expected_pnl = 4.88
        
        print(f"\n📊 SO SÁNH KẾT QUẢ:")
        print(f"   Expected Exit: {expected_exit:.6f}")
        print(f"   Tool Exit: {result['exitPrice']:.6f}")
        print(f"   Price Match: {abs(result['exitPrice'] - expected_exit) < 0.000001}")
        
        print(f"   Expected PnL: {expected_pnl:.2f}%")
        print(f"   Tool PnL: {result['pnl']:.2f}%")
        print(f"   PnL Match: {abs(result['pnl'] - expected_pnl) < 0.01}")
        
        # Reality check
        actual_min = 0.009434
        max_possible = (0.009937 - actual_min) / 0.009937 * 100
        
        print(f"\n🔍 REALITY CHECK:")
        print(f"   Actual Min: {actual_min:.6f}")
        print(f"   Max Possible: {max_possible:.2f}%")
        print(f"   Tool Result Realistic: {result['pnl'] <= max_possible + 0.1}")
        print(f"   Exit Price Reachable: {result['exitPrice'] >= actual_min}")
        
        # Final verdict
        if (abs(result['exitPrice'] - expected_exit) < 0.000001 and 
            abs(result['pnl'] - expected_pnl) < 0.01):
            print(f"\n🎉 PERFECT MATCH! BUG ĐÃ ĐƯỢC SỬA THÀNH CÔNG!")
        elif (result['pnl'] <= max_possible + 0.1 and 
              result['exitPrice'] >= actual_min):
            print(f"\n✅ REALISTIC RESULT! Tool đã hoạt động đúng")
        else:
            print(f"\n🚨 VẪN CÓ VẤN ĐỀ! Cần kiểm tra thêm")
        
    except Exception as e:
        print(f"🚨 ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_fixed_tool_with_real_trade()
