#!/usr/bin/env python3
"""
🔍 MÔ PHỎNG THỰC TẾ: Trade #139
Kiểm tra xem giá có thực sự đi xuống đạt target profit 10.24% hay không
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def simulate_trade_139_reality():
    """Mô phỏng trade #139 với dữ liệu nến thực tế"""
    print("🕯️ REALISTIC SIMULATION: Trade #139")
    print("=" * 60)
    
    # ===== THÔNG TIN TRADE =====
    print("📊 TRADE SETUP:")
    entry_time = "2025-06-20 22:00"
    original_exit_time = "2025-06-21 08:30"
    entry_price = 0.009937  # Từ optimization log
    target_exit_price = 0.008919  # Để đạt 10.24% profit
    original_exit_price = 0.009956
    
    print(f"   Entry: {entry_time} @ {entry_price:.6f} (SHORT)")
    print(f"   Original Exit: {original_exit_time} @ {original_exit_price:.6f}")
    print(f"   Target Exit (for 10.24%): {target_exit_price:.6f}")
    print()
    
    # ===== TÍNH TOÁN % TARGETS =====
    target_profit_pct = 10.24
    required_price_drop = entry_price * target_profit_pct / 100
    calculated_target = entry_price - required_price_drop
    
    print("🎯 TARGET CALCULATIONS:")
    print(f"   Entry Price: {entry_price:.6f}")
    print(f"   Required Drop: {required_price_drop:.6f} ({target_profit_pct}%)")
    print(f"   Target Price: {calculated_target:.6f}")
    print(f"   Log Target: {target_exit_price:.6f}")
    print(f"   Match: {'✅' if abs(calculated_target - target_exit_price) < 0.000001 else '❌'}")
    print()
    
    # ===== LOAD & ANALYZE CANDLE DATA =====
    try:
        print("📈 LOADING CANDLE DATA...")
        candles = pd.read_csv("data chart full info.csv")
        candles['time'] = pd.to_datetime(candles['time'])
        
        # Convert entry time with timezone matching
        if candles['time'].dt.tz is not None:
            entry_dt = pd.to_datetime(entry_time).tz_localize(candles['time'].dt.tz)
            original_exit_dt = pd.to_datetime(original_exit_time).tz_localize(candles['time'].dt.tz)
        else:
            entry_dt = pd.to_datetime(entry_time)
            original_exit_dt = pd.to_datetime(original_exit_time)
        
        print(f"   Total candles: {len(candles)}")
        print(f"   Date range: {candles['time'].min()} to {candles['time'].max()}")
        print(f"   Timezone: {candles['time'].dt.tz}")
        print()
        
        # ===== TÌM KHOẢNG THỜI GIAN TRADE =====
        print("🔍 FINDING TRADE PERIOD:")
        print(f"   Looking for entry: {entry_dt}")
        print(f"   Looking for exit: {original_exit_dt}")
        
        # Find closest entry candle
        time_diff = abs(candles['time'] - entry_dt)
        entry_idx = time_diff.idxmin()
        entry_candle = candles.loc[entry_idx]
        
        print(f"   Entry Candle: {entry_candle['time']} @ Open {entry_candle['open']:.6f}")
        
        # Find closest exit candle  
        time_diff = abs(candles['time'] - original_exit_dt)
        exit_idx = time_diff.idxmin()
        exit_candle = candles.loc[exit_idx]
        
        print(f"   Exit Candle: {exit_candle['time']} @ Close {exit_candle['close']:.6f}")
        
        # Make sure we have the right order
        if exit_idx < entry_idx:
            entry_idx, exit_idx = exit_idx, entry_idx
        
        # ===== PHÂN TÍCH GIÁ TRONG KHOẢNG TRADE =====
        print("\n🕯️ PRICE ANALYSIS DURING TRADE:")
        print("-" * 50)
        
        trade_candles = candles.loc[entry_idx:exit_idx].copy()
        print(f"   Analyzing {len(trade_candles)} candles")
        print(f"   Period: {trade_candles['time'].iloc[0]} to {trade_candles['time'].iloc[-1]}")
        print()
        
        # Tìm giá thấp nhất trong khoảng trade
        lowest_price = trade_candles['low'].min()
        lowest_idx = trade_candles['low'].idxmin()
        lowest_time = trade_candles.loc[lowest_idx, 'time']
        
        print("📉 LOWEST PRICE ANALYSIS:")
        print(f"   Lowest Price: {lowest_price:.6f}")
        print(f"   Time: {lowest_time}")
        print(f"   Target needed: {target_exit_price:.6f}")
        print(f"   Gap: {lowest_price - target_exit_price:.6f}")
        print()
        
        # Kiểm tra xem có đạt target không
        target_reached = lowest_price <= target_exit_price
        print(f"🎯 TARGET REACHABILITY:")
        print(f"   Target Price: {target_exit_price:.6f}")
        print(f"   Actual Lowest: {lowest_price:.6f}")
        print(f"   Target Reached: {'✅ YES' if target_reached else '❌ NO'}")
        
        if not target_reached:
            max_possible_profit = (entry_price - lowest_price) / entry_price * 100
            print(f"   Max Possible Profit: {max_possible_profit:.2f}%")
            print(f"   Claimed Profit: {target_profit_pct:.2f}%")
            print(f"   Difference: {target_profit_pct - max_possible_profit:.2f}%")
        
        print()
        
        # ===== CHI TIẾT 10 NẾN ĐẦU =====
        print("🔍 DETAILED CANDLE ANALYSIS (First 10 candles after entry):")
        print("-" * 70)
        
        for i in range(min(10, len(trade_candles))):
            candle = trade_candles.iloc[i]
            
            # Tính profit potential tại mỗi nến
            profit_at_low = (entry_price - candle['low']) / entry_price * 100
            profit_at_close = (entry_price - candle['close']) / entry_price * 100
            
            target_hit = "🎯" if candle['low'] <= target_exit_price else ""
            
            print(f"   {i+1:2d}. {candle['time']} {target_hit}")
            print(f"       O:{candle['open']:.6f} H:{candle['high']:.6f} L:{candle['low']:.6f} C:{candle['close']:.6f}")
            print(f"       Profit @ Low: {profit_at_low:+.2f}% | @ Close: {profit_at_close:+.2f}%")
            
            if candle['low'] <= target_exit_price:
                print(f"       🎯 TARGET REACHED! Can exit at {target_exit_price:.6f} for +{target_profit_pct:.2f}%")
                break
        
        print()
        
        # ===== KẾT LUẬN =====
        print("🎯 SIMULATION CONCLUSIONS:")
        print("=" * 40)
        
        if target_reached:
            print("✅ OPTIMIZATION TARGET IS REALISTIC:")
            print(f"   • Price did drop to {lowest_price:.6f}")
            print(f"   • Target {target_exit_price:.6f} was achievable")
            print(f"   • 10.24% profit was possible")
            print(f"   • Occurred at: {lowest_time}")
        else:
            print("❌ OPTIMIZATION TARGET IS UNREALISTIC:")
            print(f"   • Price only dropped to {lowest_price:.6f}")
            print(f"   • Target {target_exit_price:.6f} was NOT reached")
            print(f"   • 10.24% profit was NOT possible")
            print(f"   • Max achievable: {max_possible_profit:.2f}%")
            print("\n🚨 POTENTIAL ISSUE:")
            print("   Optimization log may contain calculation errors")
            print("   or use unrealistic price assumptions!")
        
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return
    
    print("\n💡 ANALYSIS COMPLETE!")

if __name__ == '__main__':
    simulate_trade_139_reality()
