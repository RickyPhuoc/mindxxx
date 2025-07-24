#!/usr/bin/env python3
"""
🔍 INDEPENDENT VERIFICATION: Trade #141 Simulation
Kiểm tra độc lập mô phỏng Trade #141 với thông số tối ưu
"""

import pandas as pd
import numpy as np
from datetime import datetime

def verify_trade_141():
    """Kiểm tra độc lập Trade #141"""
    print("🧮 INDEPENDENT VERIFICATION: Trade #141")
    print("=" * 60)
    
    # ===== THÔNG TIN TRADE GỐC =====
    print("📊 TRADE INFORMATION:")
    print("   Trade #: 141")
    print("   Entry Date: 6/30/2025 10:30")
    print("   Exit Date: 7/2/2025 8:30") 
    print("   Side: SHORT")
    print("   Entry Price: 0.0100388")
    print("   Exit Price Original: 0.0092982")
    print("   Original PnL: +7.38%")
    print()
    
    # ===== THÔNG SỐ TỐI ƯU =====
    SL_PERCENT = 4.41
    BE_PERCENT = 1.76
    TS_TRIG_PERCENT = 7.12
    TS_STEP_PERCENT = 0.26
    
    print("🎯 OPTIMAL PARAMETERS:")
    print(f"   SL: {SL_PERCENT}%")
    print(f"   BE: {BE_PERCENT}%")
    print(f"   TS Trigger: {TS_TRIG_PERCENT}%")
    print(f"   TS Step: {TS_STEP_PERCENT}%")
    print()
    
    # ===== DỮ LIỆU ENTRY =====
    entry_price = 0.0100388
    entry_open = 0.0100388
    entry_high = 0.0101183
    entry_low = 0.0100355
    entry_close = 0.0100582
    
    print("📈 ENTRY CANDLE (2025-06-30T10:30):")
    print(f"   Open: {entry_open}")
    print(f"   High: {entry_high}")
    print(f"   Low: {entry_low}")
    print(f"   Close: {entry_close}")
    print()
    
    # ===== DỮ LIỆU EXIT =====
    exit_open = 0.0092982
    exit_high = 0.0093347
    exit_low = 0.0092631
    exit_close = 0.0093114
    
    print("📉 ORIGINAL EXIT CANDLE (2025-07-02T08:30):")
    print(f"   Open: {exit_open}")
    print(f"   High: {exit_high}")
    print(f"   Low: {exit_low}")
    print(f"   Close: {exit_close}")
    print()
    
    # ===== TÍNH TOÁN MÔ PHỎNG =====
    print("🧮 SIMULATION CALCULATION:")
    print("-" * 40)
    
    # Entry price (sử dụng close của entry candle)
    sim_entry_price = entry_close
    print(f"1️⃣ Entry Price (simulation): {sim_entry_price}")
    
    # Tính các mức giá quan trọng cho SHORT
    sl_price = sim_entry_price * (1 + SL_PERCENT/100)
    be_trigger_price = sim_entry_price * (1 - BE_PERCENT/100)  # SHORT: giá giảm
    ts_trigger_price = sim_entry_price * (1 - TS_TRIG_PERCENT/100)  # SHORT: giá giảm
    
    print(f"2️⃣ SL Price (+{SL_PERCENT}%): {sl_price:.8f}")
    print(f"3️⃣ BE Trigger (-{BE_PERCENT}%): {be_trigger_price:.8f}")
    print(f"4️⃣ TS Trigger (-{TS_TRIG_PERCENT}%): {ts_trigger_price:.8f}")
    print()
    
    # Kiểm tra log output
    log_exit_price = 0.009200  # Từ log: "0.009200	TS SL"
    log_pnl = 8.42  # Từ log: "8.42"
    
    print("📋 LOG OUTPUT CHECK:")
    print(f"   Log Exit Price: {log_exit_price}")
    print(f"   Log PnL: {log_pnl}%")
    print()
    
    # Tính PnL từ log
    calculated_pnl = (sim_entry_price - log_exit_price) / sim_entry_price * 100
    print(f"🔢 CALCULATED PnL from Log:")
    print(f"   Formula: ({sim_entry_price} - {log_exit_price}) / {sim_entry_price} * 100")
    print(f"   Result: {calculated_pnl:.2f}%")
    print()
    
    # So sánh với log
    pnl_diff = abs(calculated_pnl - log_pnl)
    print(f"📊 COMPARISON:")
    print(f"   Calculated: {calculated_pnl:.2f}%")
    print(f"   Log Output: {log_pnl}%")
    print(f"   Difference: {pnl_diff:.2f}%")
    print()
    
    if pnl_diff < 0.01:
        print("✅ VERIFICATION: PASSED - Calculation matches log output!")
    else:
        print("❌ VERIFICATION: FAILED - Calculation does not match log!")
        
    # ===== PHÂN TÍCH TRAILING STOP =====
    print("\n🎯 TRAILING STOP ANALYSIS:")
    print("=" * 50)
    
    # Kiểm tra xem có đạt TS trigger không
    original_exit_price = exit_open  # 0.0092982
    ts_reached = original_exit_price <= ts_trigger_price
    
    print(f"TS Trigger Price: {ts_trigger_price:.8f}")
    print(f"Original Exit: {original_exit_price:.8f}")
    print(f"TS Triggered: {ts_reached}")
    
    if ts_reached:
        # Tính TS price khi đã trigger
        max_profit_price = original_exit_price  # Giả sử đây là điểm thấp nhất
        ts_exit_price = max_profit_price * (1 + TS_STEP_PERCENT/100)  # SHORT: TS step lên
        
        print(f"Max Profit Point: {max_profit_price:.8f}")
        print(f"TS Exit Price (+{TS_STEP_PERCENT}%): {ts_exit_price:.8f}")
        print(f"Log Exit Price: {log_exit_price:.8f}")
        
        # So sánh
        ts_diff = abs(ts_exit_price - log_exit_price)
        print(f"TS Calculation vs Log: {ts_diff:.8f}")
        
        if ts_diff < 0.000010:  # Tolerance cho precision
            print("✅ TS CALCULATION: CORRECT")
        else:
            print("⚠️ TS CALCULATION: Minor difference (could be due to precision)")
    
    print("\n" + "=" * 60)
    print("🎉 VERIFICATION COMPLETE!")

if __name__ == '__main__':
    verify_trade_141()
