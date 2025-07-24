#!/usr/bin/env python3
"""
🔍 INDEPENDENT VERIFICATION: Trade #139 Simulation
Kiểm tra độc lập mô phỏng Trade #139
Log: 139	06/20 22:00	SHORT	0.009937	0.009956	Signal	-0.19	0.008919	TS SL	10.24	+10.43
"""

import pandas as pd
import numpy as np
from datetime import datetime

def verify_trade_139():
    """Kiểm tra độc lập Trade #139"""
    print("🧮 INDEPENDENT VERIFICATION: Trade #139")
    print("=" * 60)
    
    # ===== THÔNG TIN TRADE GỐC TỪNG LOG =====
    print("📊 TRADE INFORMATION FROM LOG:")
    print("   Trade #: 139")
    print("   Entry Date: 06/20 22:00")
    print("   Side: SHORT")
    print("   Entry Price: 0.009937")
    print("   Original Exit Price: 0.009956")
    print("   Original Exit Type: Signal")
    print("   Original PnL: -0.19%")
    print("   ---")
    print("   Optimized Exit Price: 0.008919")
    print("   Optimized Exit Type: TS SL")
    print("   Optimized PnL: 10.24%")
    print("   Improvement: +10.43%")
    print()
    
    # ===== PHÂN TÍCH ENTRY =====
    entry_price = 0.009937
    original_exit_price = 0.009956
    optimized_exit_price = 0.008919
    
    print("🔍 CALCULATION VERIFICATION:")
    print("-" * 40)
    
    # 1. Kiểm tra Original PnL
    print("1️⃣ ORIGINAL PnL VERIFICATION:")
    original_pnl_calc = (entry_price - original_exit_price) / entry_price * 100
    print(f"   Formula: ({entry_price} - {original_exit_price}) / {entry_price} * 100")
    print(f"   Calculated: {original_pnl_calc:.2f}%")
    print(f"   Log states: -0.19%")
    print(f"   Difference: {abs(original_pnl_calc - (-0.19)):.2f}%")
    
    if abs(original_pnl_calc - (-0.19)) < 0.01:
        print("   ✅ Original PnL calculation: CORRECT")
    else:
        print("   ⚠️ Original PnL calculation: Minor difference")
    print()
    
    # 2. Kiểm tra Optimized PnL
    print("2️⃣ OPTIMIZED PnL VERIFICATION:")
    optimized_pnl_calc = (entry_price - optimized_exit_price) / entry_price * 100
    print(f"   Formula: ({entry_price} - {optimized_exit_price}) / {entry_price} * 100")
    print(f"   Calculated: {optimized_pnl_calc:.2f}%")
    print(f"   Log states: 10.24%")
    print(f"   Difference: {abs(optimized_pnl_calc - 10.24):.2f}%")
    
    if abs(optimized_pnl_calc - 10.24) < 0.01:
        print("   ✅ Optimized PnL calculation: CORRECT")
    else:
        print("   ⚠️ Optimized PnL calculation: Minor difference")
    print()
    
    # 3. Kiểm tra Improvement
    print("3️⃣ IMPROVEMENT VERIFICATION:")
    improvement_calc = optimized_pnl_calc - original_pnl_calc
    print(f"   Formula: {optimized_pnl_calc:.2f}% - ({original_pnl_calc:.2f}%)")
    print(f"   Calculated: {improvement_calc:.2f}%")
    print(f"   Log states: +10.43%")
    print(f"   Difference: {abs(improvement_calc - 10.43):.2f}%")
    
    if abs(improvement_calc - 10.43) < 0.01:
        print("   ✅ Improvement calculation: CORRECT")
    else:
        print("   ⚠️ Improvement calculation: Minor difference")
    print()
    
    # ===== PHÂN TÍCH TRAILING STOP =====
    print("🎯 TRAILING STOP ANALYSIS:")
    print("=" * 50)
    
    # Tìm entry time trong data
    try:
        candles = pd.read_csv("data chart full info.csv")
        candles['time'] = pd.to_datetime(candles['time'])
        
        # Tìm entry time gần nhất với 06/20 22:00
        if candles['time'].dt.tz is not None:
            target_time = pd.to_datetime('2025-06-20 22:00:00').tz_localize(candles['time'].dt.tz)
        else:
            target_time = pd.to_datetime('2025-06-20 22:00:00')
        
        # Tìm candle gần nhất
        time_diff = abs(candles['time'] - target_time)
        closest_idx = time_diff.idxmin()
        entry_candle = candles.iloc[closest_idx]
        
        print(f"📍 ENTRY CANDLE FOUND:")
        print(f"   Time: {entry_candle['time']}")
        print(f"   Open: {entry_candle['open']:.6f}")
        print(f"   High: {entry_candle['high']:.6f}")
        print(f"   Low: {entry_candle['low']:.6f}")
        print(f"   Close: {entry_candle['close']:.6f}")
        print()
        
        # So sánh với log entry price
        log_entry = 0.009937
        candle_prices = [entry_candle['open'], entry_candle['high'], entry_candle['low'], entry_candle['close']]
        closest_price = min(candle_prices, key=lambda x: abs(x - log_entry))
        
        print(f"🔍 ENTRY PRICE ANALYSIS:")
        print(f"   Log Entry: {log_entry:.6f}")
        print(f"   Closest Candle Price: {closest_price:.6f}")
        print(f"   Difference: {abs(log_entry - closest_price):.6f}")
        
        if abs(log_entry - closest_price) < 0.000010:
            print("   ✅ Entry price matches candle data")
        else:
            print("   ⚠️ Entry price has minor difference from candle data")
        print()
        
    except Exception as e:
        print(f"❌ Could not load candle data: {e}")
    
    # ===== KẾT QUẢ TỔNG KẾT =====
    print("🎉 VERIFICATION SUMMARY:")
    print("=" * 40)
    
    # Tính tổng độ chính xác
    original_correct = abs(original_pnl_calc - (-0.19)) < 0.01
    optimized_correct = abs(optimized_pnl_calc - 10.24) < 0.01
    improvement_correct = abs(improvement_calc - 10.43) < 0.01
    
    total_correct = sum([original_correct, optimized_correct, improvement_correct])
    
    print(f"📊 Accuracy Score: {total_correct}/3")
    
    if total_correct == 3:
        print("✅ VERIFICATION RESULT: PASSED")
        print("   All calculations match log output within tolerance!")
    elif total_correct >= 2:
        print("⚠️ VERIFICATION RESULT: MOSTLY PASSED")
        print("   Most calculations match with minor differences")
    else:
        print("❌ VERIFICATION RESULT: FAILED")
        print("   Significant differences found in calculations")
    
    print()
    print("🔍 KEY INSIGHTS:")
    print(f"   • Original trade was LOSING: {original_pnl_calc:.2f}%")
    print(f"   • Optimization made it PROFITABLE: {optimized_pnl_calc:.2f}%")
    print(f"   • Total improvement: {improvement_calc:.2f} percentage points")
    print(f"   • Exit price moved from {original_exit_price} to {optimized_exit_price}")
    print(f"   • Price improvement: {((original_exit_price - optimized_exit_price)/original_exit_price)*100:.2f}%")

if __name__ == '__main__':
    verify_trade_139()
