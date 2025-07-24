#!/usr/bin/env python3
"""
🔍 CORRECTED VERIFICATION: Trade #139 
Sử dụng data chính xác từ tradelist
"""

import pandas as pd
import numpy as np
from datetime import datetime

def verify_trade_139_corrected():
    """Kiểm tra Trade #139 với data chính xác"""
    print("🧮 CORRECTED VERIFICATION: Trade #139")
    print("=" * 60)
    
    # ===== DATA CHÍNH XÁC TỪ TRADELIST =====
    print("📊 ACTUAL TRADE DATA FROM TRADELIST:")
    print("   Trade #: 139")
    print("   Entry: 6/20/2025 22:00 @ 0.0099367 (SHORT)")  
    print("   Exit: 6/21/2025 8:30 @ 0.0099555 (Signal)")
    print("   Original PnL: -0.19% (LOSS)")
    print("   Run-up: 5.05%")
    print("   Drawdown: -1.42%")
    print()
    
    # ===== DATA TỪ LOG OPTIMIZATION =====
    print("📊 OPTIMIZATION LOG DATA:")
    print("   Entry: 06/20 22:00 @ 0.009937")
    print("   Original Exit: 0.009956 → PnL: -0.19%")
    print("   Optimized Exit: 0.008919 → PnL: 10.24%")
    print("   Improvement: +10.43%")
    print()
    
    # ===== PHÂN TÍCH SỰ KHÁC BIỆT =====
    tradelist_entry = 0.0099367 
    tradelist_exit = 0.0099555
    
    log_entry = 0.009937
    log_original_exit = 0.009956
    log_optimized_exit = 0.008919
    
    print("🔍 PRICE COMPARISON:")
    print("-" * 40)
    print("Entry Price:")
    print(f"   Tradelist: {tradelist_entry:.6f}")
    print(f"   Log:       {log_entry:.6f}")
    print(f"   Difference: {abs(tradelist_entry - log_entry):.6f}")
    print()
    
    print("Original Exit Price:")
    print(f"   Tradelist: {tradelist_exit:.6f}")
    print(f"   Log:       {log_original_exit:.6f}")
    print(f"   Difference: {abs(tradelist_exit - log_original_exit):.6f}")
    print()
    
    # ===== TÍNH TOÁN PnL =====
    print("💰 PnL CALCULATIONS:")
    print("-" * 40)
    
    # Tradelist PnL
    tradelist_pnl = (tradelist_entry - tradelist_exit) / tradelist_entry * 100
    print(f"1️⃣ TRADELIST PnL:")
    print(f"   Formula: ({tradelist_entry} - {tradelist_exit}) / {tradelist_entry} * 100")
    print(f"   Result: {tradelist_pnl:.2f}%")
    print(f"   Matches reported -0.19%: {'✅' if abs(tradelist_pnl - (-0.19)) < 0.01 else '❌'}")
    print()
    
    # Log original PnL  
    log_original_pnl = (log_entry - log_original_exit) / log_entry * 100
    print(f"2️⃣ LOG ORIGINAL PnL:")
    print(f"   Formula: ({log_entry} - {log_original_exit}) / {log_entry} * 100")
    print(f"   Result: {log_original_pnl:.2f}%")
    print(f"   Matches reported -0.19%: {'✅' if abs(log_original_pnl - (-0.19)) < 0.01 else '❌'}")
    print()
    
    # Log optimized PnL
    log_optimized_pnl = (log_entry - log_optimized_exit) / log_entry * 100
    print(f"3️⃣ LOG OPTIMIZED PnL:")
    print(f"   Formula: ({log_entry} - {log_optimized_exit}) / {log_entry} * 100")
    print(f"   Result: {log_optimized_pnl:.2f}%")
    print(f"   Matches reported 10.24%: {'✅' if abs(log_optimized_pnl - 10.24) < 0.01 else '❌'}")
    print()
    
    # Improvement
    improvement = log_optimized_pnl - log_original_pnl
    print(f"4️⃣ IMPROVEMENT:")
    print(f"   Calculated: {improvement:.2f} percentage points")
    print(f"   Reported: +10.43%")
    print(f"   Match: {'✅' if abs(improvement - 10.43) < 0.01 else '❌'}")
    print()
    
    # ===== TÌM ENTRY TRONG DATA =====
    print("🔍 SEARCHING FOR ENTRY IN CANDLE DATA:")
    print("-" * 50)
    
    try:
        # Try to find in BTC data first
        candles = pd.read_csv("data chart full info.csv")
        candles['time'] = pd.to_datetime(candles['time'])
        
        # Search for entry time
        if candles['time'].dt.tz is not None:
            target_time = pd.to_datetime('2025-06-20 22:00:00').tz_localize(candles['time'].dt.tz)
        else:
            target_time = pd.to_datetime('2025-06-20 22:00:00')
        
        # Find closest candle
        time_diff = abs(candles['time'] - target_time)
        closest_idx = time_diff.idxmin()
        entry_candle = candles.iloc[closest_idx]
        
        print(f"📍 FOUND ENTRY CANDLE:")
        print(f"   Time: {entry_candle['time']}")
        print(f"   Open: {entry_candle['open']:.6f}")
        print(f"   High: {entry_candle['high']:.6f}")
        print(f"   Low: {entry_candle['low']:.6f}")
        print(f"   Close: {entry_candle['close']:.6f}")
        print()
        
        # Compare with both entry prices
        candle_prices = [entry_candle['open'], entry_candle['high'], entry_candle['low'], entry_candle['close']]
        
        print("📊 PRICE MATCHING:")
        for price_type, price in zip(['Open', 'High', 'Low', 'Close'], candle_prices):
            tradelist_diff = abs(price - tradelist_entry)
            log_diff = abs(price - log_entry)
            print(f"   {price_type}: {price:.6f}")
            print(f"     vs Tradelist ({tradelist_entry:.6f}): diff {tradelist_diff:.6f}")
            print(f"     vs Log ({log_entry:.6f}): diff {log_diff:.6f}")
        
    except Exception as e:
        print(f"❌ Could not load candle data: {e}")
    
    # ===== KẾT LUẬN =====
    print("\n🎯 CONCLUSIONS:")
    print("=" * 40)
    print("1️⃣ DATA CONSISTENCY:")
    print("   • Tradelist và Log có entry price khác nhau (0.0099367 vs 0.009937)")
    print("   • Cả hai đều cho PnL gốc là -0.19% (thua lỗ)")
    print("   • Log optimization cho thấy có thể biến thành +10.24% lãi")
    print()
    
    print("2️⃣ OPTIMIZATION POTENTIAL:")
    print(f"   • Từ thua lỗ -0.19% → lãi +10.24%")
    print(f"   • Cải thiện: +10.43 percentage points")
    print(f"   • Exit price improvement: từ ~0.00996 xuống 0.008919")
    print()
    
    print("3️⃣ VERIFICATION STATUS:")
    calculations_correct = (
        abs(log_original_pnl - (-0.19)) < 0.01 and
        abs(log_optimized_pnl - 10.24) < 0.01 and
        abs(improvement - 10.43) < 0.01
    )
    
    if calculations_correct:
        print("   ✅ All optimization calculations are CORRECT")
        print("   ✅ Tool successfully transforms losing trade to profitable")
    else:
        print("   ⚠️ Some discrepancies found in calculations")
    
    print("\n💡 KEY INSIGHT:")
    print("   Trade #139 demonstrates the power of optimization:")
    print("   • Original strategy: LOSING trade (-0.19%)")
    print("   • Optimized strategy: PROFITABLE trade (+10.24%)")
    print("   • Total transformation: +10.43 percentage points!")

if __name__ == '__main__':
    verify_trade_139_corrected()
