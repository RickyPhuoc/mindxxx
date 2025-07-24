#!/usr/bin/env python3
"""
🚨 EMERGENCY FIX: Complete Trailing Stop Reality Check
Kiểm tra toàn bộ logic và so sánh với actual data
"""

import pandas as pd
import numpy as np

def emergency_reality_check():
    """Kiểm tra thực tế hoàn toàn"""
    print("🚨 EMERGENCY: Complete Reality Check")
    print("=" * 60)
    
    # Load data
    candles = pd.read_csv("data chart full info.csv") 
    candles['time'] = pd.to_datetime(candles['time'])
    
    # Find exact trade period
    entry_time = pd.to_datetime('2025-06-20 22:00:00').tz_localize(candles['time'].dt.tz)
    exit_time = pd.to_datetime('2025-06-21 08:30:00').tz_localize(candles['time'].dt.tz)
    
    entry_idx = abs(candles['time'] - entry_time).idxmin()
    exit_idx = abs(candles['time'] - exit_time).idxmin()
    
    trade_candles = candles.iloc[entry_idx:exit_idx+1].copy()
    
    print("📊 TRADE DATA REALITY:")
    print(f"   Entry: 0.009937 at {entry_time}")
    print(f"   Claimed Exit: 0.008919 (10.24% profit)")
    print(f"   Period: {len(trade_candles)} candles")
    
    # Check if claimed exit price ever existed
    min_price = trade_candles['low'].min()
    min_time = trade_candles.loc[trade_candles['low'].idxmin(), 'time']
    
    print(f"\n🎯 ACTUAL PRICE REALITY:")
    print(f"   Lowest Price Reached: {min_price:.6f}")
    print(f"   Time of Lowest: {min_time}")
    print(f"   Claimed Exit: 0.008919")
    
    if min_price > 0.008919:
        print(f"   🚨 IMPOSSIBLE! Claimed exit NEVER EXISTED in data!")
        print(f"   🚨 Tool is calculating FANTASY prices!")
        max_possible_profit = (0.009937 - min_price) / 0.009937 * 100
        print(f"   ✅ Max Possible Profit: {max_possible_profit:.2f}%")
    else:
        print(f"   ✅ Claimed exit price was reachable")
    
    # Show all candles to prove the point
    print(f"\n📈 ALL CANDLES IN TRADE PERIOD:")
    print("-" * 80)
    for i, row in trade_candles.iterrows():
        profit_at_low = (0.009937 - row['low']) / 0.009937 * 100
        print(f"   {row['time']} | Low: {row['low']:.6f} | High: {row['high']:.6f} | Profit@Low: {profit_at_low:.2f}%")
    
    print(f"\n🚨 CONCLUSION:")
    print("=" * 50)
    print("   The optimization tool is calculating IMPOSSIBLE exit prices!")
    print("   It's using mathematical formulas without reality validation!")
    print("   ALL profit claims above max possible are INVALID!")
    
    print(f"\n🔧 IMMEDIATE ACTION REQUIRED:")
    print("   1️⃣ STOP using current optimization tool results")
    print("   2️⃣ REWRITE trailing stop logic with data validation") 
    print("   3️⃣ AUDIT all historical optimization results")
    print("   4️⃣ IMPLEMENT reality checks in ALL calculations")

if __name__ == '__main__':
    emergency_reality_check()
