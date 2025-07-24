#!/usr/bin/env python3
"""
🔍 DEEP ANALYSIS: Trade #139
Kiểm tra toàn diện với cả tradelist và candle data
Mô phỏng từng nến để tìm sai sót
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def deep_analyze_trade_139():
    """Phân tích sâu Trade #139 với cả hai nguồn data"""
    print("🔬 DEEP COMPREHENSIVE ANALYSIS: Trade #139")
    print("=" * 70)
    
    # ===== LOAD CẢ HAI NGUỒN DATA =====
    print("📊 LOADING ALL DATA SOURCES...")
    
    try:
        # Load candle data
        candles = pd.read_csv("data chart full info.csv")
        candles['time'] = pd.to_datetime(candles['time'])
        print(f"✅ Candle data loaded: {len(candles)} records")
        
        # Load tradelist data
        tradelist = pd.read_csv("tradelist-fullinfo.csv")
        print(f"✅ Tradelist loaded: {len(tradelist)} records")
        
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return
    
    # ===== TÌM TRADE #139 TRONG TRADELIST =====
    print("\n🔍 FINDING TRADE #139 IN TRADELIST:")
    print("-" * 50)
    
    # Search for trade 139
    trade_139_rows = tradelist[tradelist['Trade #'] == 139]
    
    if len(trade_139_rows) == 0:
        print("❌ Trade #139 not found in tradelist!")
        return
    
    print(f"Found {len(trade_139_rows)} entries for Trade #139:")
    for idx, row in trade_139_rows.iterrows():
        print(f"   Row {idx}: {row['Type']} | {row['Signal']} | {row['Date/Time']} | {row['Price USDT']:.6f} | PnL: {row['P&L %']}")
    
    # Separate entry and exit data
    entry_row = trade_139_rows[trade_139_rows['Type'].str.contains('Entry', na=False)]
    exit_row = trade_139_rows[trade_139_rows['Type'].str.contains('Exit', na=False)]
    
    if len(entry_row) == 0 or len(exit_row) == 0:
        print("❌ Could not find both entry and exit for Trade #139")
        return
    
    entry_data = entry_row.iloc[0]
    exit_data = exit_row.iloc[0]
    
    print(f"\n📋 TRADE #139 DETAILS:")
    print(f"   Entry: {entry_data['Type']} | {entry_data['Date/Time']} | {entry_data['Price USDT']:.6f}")
    print(f"   Exit: {exit_data['Type']} | {exit_data['Date/Time']} | {exit_data['Price USDT']:.6f}")
    print(f"   PnL: {exit_data['P&L %']}")
    print(f"   Run-up: {exit_data['Run-up %']}")
    print(f"   Drawdown: {exit_data['Drawdown %']}")
    
    # ===== PARSE THỜI GIAN =====
    entry_time_str = str(entry_data['Date/Time'])
    exit_time_str = str(exit_data['Date/Time'])
    
    print(f"\n🕐 TIME PARSING:")
    print(f"   Raw Entry: '{entry_time_str}'")
    print(f"   Raw Exit: '{exit_time_str}'")
    
    # Parse entry time - handle different formats
    try:
        if '/' in entry_time_str:
            # Format: 6/20/2025 22:00
            entry_dt = pd.to_datetime(entry_time_str, format='%m/%d/%Y %H:%M')
        else:
            entry_dt = pd.to_datetime(entry_time_str)
        
        if '/' in exit_time_str:
            # Format: 6/21/2025 8:30  
            exit_dt = pd.to_datetime(exit_time_str, format='%m/%d/%Y %H:%M')
        else:
            exit_dt = pd.to_datetime(exit_time_str)
        
        # Convert to match candle timezone
        if candles['time'].dt.tz is not None:
            entry_dt = entry_dt.tz_localize(candles['time'].dt.tz)
            exit_dt = exit_dt.tz_localize(candles['time'].dt.tz)
        
        print(f"   Parsed Entry: {entry_dt}")
        print(f"   Parsed Exit: {exit_dt}")
        
    except Exception as e:
        print(f"❌ Time parsing error: {e}")
        return
    
    # ===== TÌM CANDLES TƯƠNG ỨNG =====
    print(f"\n🕯️ FINDING CORRESPONDING CANDLES:")
    print("-" * 50)
    
    # Find entry candle
    entry_time_diff = abs(candles['time'] - entry_dt)
    entry_idx = entry_time_diff.idxmin()
    entry_candle = candles.iloc[entry_idx]
    
    print(f"📍 ENTRY CANDLE:")
    print(f"   Time: {entry_candle['time']}")
    print(f"   Open: {entry_candle['open']:.6f}")
    print(f"   High: {entry_candle['high']:.6f}")  
    print(f"   Low: {entry_candle['low']:.6f}")
    print(f"   Close: {entry_candle['close']:.6f}")
    print(f"   Tradelist Entry: {entry_data['Price USDT']:.6f}")
    print(f"   Match with Open: {'✅' if abs(entry_candle['open'] - entry_data['Price USDT']) < 0.000001 else '❌'}")
    
    # Find exit candle
    exit_time_diff = abs(candles['time'] - exit_dt)
    exit_idx = exit_time_diff.idxmin()
    exit_candle = candles.iloc[exit_idx]
    
    print(f"\n📍 EXIT CANDLE:")
    print(f"   Time: {exit_candle['time']}")
    print(f"   Open: {exit_candle['open']:.6f}")
    print(f"   High: {exit_candle['high']:.6f}")
    print(f"   Low: {exit_candle['low']:.6f}") 
    print(f"   Close: {exit_candle['close']:.6f}")
    print(f"   Tradelist Exit: {exit_data['Price USDT']:.6f}")
    print(f"   Match with Close: {'✅' if abs(exit_candle['close'] - exit_data['Price USDT']) < 0.000001 else '❌'}")
    
    # ===== MÔ PHỎNG TỪNG NẾN =====
    print(f"\n🎯 CANDLE-BY-CANDLE SIMULATION:")
    print("=" * 70)
    
    # Get trade period candles
    trade_candles = candles.iloc[entry_idx:exit_idx+1].copy()
    
    entry_price = float(entry_data['Price USDT'])
    print(f"📊 ANALYZING {len(trade_candles)} CANDLES")
    print(f"📍 Entry Price: {entry_price:.6f} (SHORT position)")
    print(f"📅 Period: {trade_candles.iloc[0]['time']} → {trade_candles.iloc[-1]['time']}")
    print()
    
    # Track best possible exit
    best_profit = -999
    best_exit_price = 0
    best_exit_time = None
    
    # Optimization targets
    optimization_target_price = 0.008919
    optimization_target_profit = 10.24
    
    print(f"🎯 OPTIMIZATION CLAIMS:")
    print(f"   Target Exit Price: {optimization_target_price:.6f}")
    print(f"   Target Profit: {optimization_target_profit:.2f}%")
    print()
    
    print(f"📈 DETAILED CANDLE ANALYSIS:")
    print("-" * 70)
    
    target_reached = False
    target_reach_time = None
    
    for i, (idx, candle) in enumerate(trade_candles.iterrows()):
        # Calculate profits at each price level
        profit_at_open = (entry_price - candle['open']) / entry_price * 100
        profit_at_high = (entry_price - candle['high']) / entry_price * 100  
        profit_at_low = (entry_price - candle['low']) / entry_price * 100
        profit_at_close = (entry_price - candle['close']) / entry_price * 100
        
        # Check if optimization target was hit
        target_hit_this_candle = candle['low'] <= optimization_target_price
        if target_hit_this_candle and not target_reached:
            target_reached = True
            target_reach_time = candle['time']
            print(f"🎯🎯🎯 OPTIMIZATION TARGET HIT! 🎯🎯🎯")
        
        # Track best profit
        best_candle_profit = max(profit_at_open, profit_at_high, profit_at_low, profit_at_close)
        if best_candle_profit > best_profit:
            best_profit = best_candle_profit
            best_exit_price = candle['low'] if profit_at_low == best_candle_profit else (
                candle['high'] if profit_at_high == best_candle_profit else (
                candle['open'] if profit_at_open == best_candle_profit else candle['close']
                )
            )
            best_exit_time = candle['time']
        
        status = "🎯" if target_hit_this_candle else ""
        
        print(f"{i+1:2d}. {candle['time']} {status}")
        print(f"    OHLC: {candle['open']:.6f} | {candle['high']:.6f} | {candle['low']:.6f} | {candle['close']:.6f}")
        print(f"    Profit: O:{profit_at_open:+.2f}% H:{profit_at_high:+.2f}% L:{profit_at_low:+.2f}% C:{profit_at_close:+.2f}%")
        
        if target_hit_this_candle:
            actual_profit_at_target = (entry_price - optimization_target_price) / entry_price * 100
            print(f"    🎯 Target {optimization_target_price:.6f} HIT! Profit: {actual_profit_at_target:.2f}%")
        
        print()
    
    # ===== PHÂN TÍCH KẾT QUẢ =====
    print(f"🎯 SIMULATION RESULTS:")
    print("=" * 50)
    
    print(f"💰 BEST POSSIBLE PERFORMANCE:")
    print(f"   Best Exit Price: {best_exit_price:.6f}")
    print(f"   Best Exit Time: {best_exit_time}")
    print(f"   Best Profit: {best_profit:.2f}%")
    print()
    
    print(f"🎯 OPTIMIZATION TARGET ANALYSIS:")
    print(f"   Claimed Target: {optimization_target_price:.6f}")
    print(f"   Claimed Profit: {optimization_target_profit:.2f}%")
    print(f"   Target Reached: {'✅ YES' if target_reached else '❌ NO'}")
    
    if target_reached:
        actual_profit_at_target = (entry_price - optimization_target_price) / entry_price * 100
        print(f"   Target Hit Time: {target_reach_time}")
        print(f"   Actual profit at target: {actual_profit_at_target:.2f}%")
        print(f"   Matches claimed: {'✅' if abs(actual_profit_at_target - optimization_target_profit) < 0.1 else '❌'}")
    else:
        shortage = optimization_target_price - best_exit_price  
        print(f"   Price shortage: {shortage:.6f}")
        print(f"   Profit gap: {optimization_target_profit - best_profit:.2f}%")
    
    print()
    
    # ===== TRADELIST VALIDATION =====
    print(f"📋 TRADELIST VALIDATION:")
    print("-" * 30)
    
    actual_exit_price = float(exit_data['Price USDT'])
    actual_pnl = exit_data['P&L %'].replace('%', '') if isinstance(exit_data['P&L %'], str) else exit_data['P&L %']
    actual_pnl = float(actual_pnl)
    calculated_pnl = (entry_price - actual_exit_price) / entry_price * 100
    
    print(f"   Actual Exit: {actual_exit_price:.6f}")
    print(f"   Reported PnL: {actual_pnl:.2f}%")
    print(f"   Calculated PnL: {calculated_pnl:.2f}%")
    print(f"   Match: {'✅' if abs(actual_pnl - calculated_pnl) < 0.01 else '❌'}")
    
    # ===== KẾT LUẬN CUỐI CÙNG =====
    print(f"\n🚨 FINAL CONCLUSIONS:")
    print("=" * 40)
    
    if target_reached:
        print("✅ OPTIMIZATION TARGET IS ACHIEVABLE:")
        print(f"   • Price did reach {optimization_target_price:.6f}")
        print(f"   • {optimization_target_profit:.2f}% profit was possible")
        print(f"   • Target hit at: {target_reach_time}")
        print("   • Optimization calculations appear CORRECT")
    else:
        print("❌ OPTIMIZATION TARGET IS IMPOSSIBLE:")
        print(f"   • Price never reached {optimization_target_price:.6f}")
        print(f"   • Best possible was only {best_profit:.2f}%")
        print(f"   • {optimization_target_profit:.2f}% profit was IMPOSSIBLE")
        print("   • 🚨 OPTIMIZATION LOG CONTAINS ERRORS!")
    
    print(f"\n💡 RECOMMENDATION:")
    if target_reached:
        print("   ✅ Optimization tool appears to be working correctly")
        print("   ✅ The claimed 10.24% profit was indeed achievable")
    else:
        print("   🔧 FIX REQUIRED: Check optimization algorithm for price calculation bugs")
        print("   🔍 INVESTIGATE: How does optimizer determine exit prices?")
        print("   🚨 URGENT: Optimization claims are not supported by actual price data!")

if __name__ == '__main__':
    deep_analyze_trade_139()
