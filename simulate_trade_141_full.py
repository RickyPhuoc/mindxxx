#!/usr/bin/env python3
"""
🔍 COMPREHENSIVE TRADE #141 SIMULATION
Mô phỏng đầy đủ Trade #141 với tất cả candle từ entry đến exit
"""

import pandas as pd
import numpy as np
from datetime import datetime
import re

def load_trade_data():
    """Load tradelist data"""
    df = pd.read_csv('tradelist-fullinfo.csv')
    trade_141 = df[df['Trade #'] == 141].copy()
    return trade_141

def load_candle_data():
    """Load candle data for simulation period"""
    df = pd.read_csv('data chart full info.csv')
    
    # Convert time column
    df['time'] = pd.to_datetime(df['time'])
    
    # Filter for simulation period (6/30 10:30 to 7/2 8:30)
    start_time = pd.to_datetime('2025-06-30 10:30:00+07:00')
    end_time = pd.to_datetime('2025-07-02 08:30:00+07:00')
    
    simulation_candles = df[(df['time'] >= start_time) & (df['time'] <= end_time)].copy()
    return simulation_candles

def simulate_full_trade_141():
    """Mô phỏng đầy đủ Trade #141 với BE + TS logic"""
    print("🚀 COMPREHENSIVE TRADE #141 SIMULATION")
    print("=" * 60)
    
    # Load data
    trade_data = load_trade_data()
    candle_data = load_candle_data()
    
    if len(trade_data) == 0:
        print("❌ No trade data found for Trade #141")
        return
    
    if len(candle_data) == 0:
        print("❌ No candle data found for simulation period")
        return
    
    # Trade info
    entry_trade = trade_data[trade_data['Type'] == 'Entry short'].iloc[0]
    exit_trade = trade_data[trade_data['Type'] == 'Exit short'].iloc[0]
    
    print("📊 TRADE DATA LOADED:")
    print(f"   Entry: {entry_trade['Date/Time']} @ {entry_trade['Price USDT']}")
    print(f"   Exit: {exit_trade['Date/Time']} @ {exit_trade['Price USDT']}")
    print(f"   Original PnL: {exit_trade['P&L %']}")
    print(f"   Candles in period: {len(candle_data)}")
    print()
    
    # Simulation parameters
    SL_PERCENT = 4.41
    BE_PERCENT = 1.76
    TS_TRIG_PERCENT = 7.12
    TS_STEP_PERCENT = 0.26
    
    print("🎯 SIMULATION PARAMETERS:")
    print(f"   SL: {SL_PERCENT}%")
    print(f"   BE: {BE_PERCENT}%") 
    print(f"   TS Trigger: {TS_TRIG_PERCENT}%")
    print(f"   TS Step: {TS_STEP_PERCENT}%")
    print()
    
    # Start simulation
    entry_price = float(candle_data.iloc[0]['close'])  # Use close of entry candle
    side = 'SHORT'
    
    print(f"🚀 SIMULATION START:")
    print(f"   Entry Price: {entry_price:.8f}")
    print(f"   Side: {side}")
    print()
    
    # Calculate key levels for SHORT
    sl_price = entry_price * (1 + SL_PERCENT/100)
    be_trigger_price = entry_price * (1 - BE_PERCENT/100)
    ts_trigger_price = entry_price * (1 - TS_TRIG_PERCENT/100)
    
    print(f"📏 KEY LEVELS (SHORT):")
    print(f"   SL Price: {sl_price:.8f} (+{SL_PERCENT}%)")
    print(f"   BE Trigger: {be_trigger_price:.8f} (-{BE_PERCENT}%)")
    print(f"   TS Trigger: {ts_trigger_price:.8f} (-{TS_TRIG_PERCENT}%)")
    print()
    
    # Simulation state
    current_sl = sl_price
    be_activated = False
    ts_activated = False
    max_favorable_price = entry_price  # For SHORT, track lowest price
    exit_price = None
    exit_type = 'Signal'  # Default
    
    print("🔄 CANDLE-BY-CANDLE SIMULATION:")
    print("-" * 50)
    
    for i, (idx, candle) in enumerate(candle_data.iterrows()):
        high = float(candle['high'])
        low = float(candle['low'])
        close = float(candle['close'])
        time_str = candle['time'].strftime('%m/%d %H:%M')
        
        print(f"Candle {i+1:2d} ({time_str}): H={high:.6f} L={low:.6f} C={close:.6f}")
        
        # For SHORT: Track lowest price as most favorable
        if low < max_favorable_price:
            max_favorable_price = low
            print(f"   💰 New Max Profit: {max_favorable_price:.8f}")
        
        # Check SL hit (SHORT: SL triggers when price goes UP)
        if high >= current_sl:
            exit_price = min(current_sl * 1.001, high)  # Slippage
            exit_type = 'SL'
            print(f"   🛑 SL HIT at {exit_price:.8f}")
            break
        
        # Check BE activation (SHORT: BE when price goes DOWN enough)
        if not be_activated and low <= be_trigger_price:
            be_activated = True
            current_sl = entry_price  # Move SL to breakeven
            print(f"   🎯 BE ACTIVATED! SL moved to {current_sl:.8f}")
        
        # Check TS activation (SHORT: TS when price goes DOWN enough)
        if not ts_activated and low <= ts_trigger_price:
            ts_activated = True
            print(f"   🎯 TS ACTIVATED! Max profit tracking started")
        
        # Update TS if activated (SHORT: TS moves UP as price moves DOWN)
        if ts_activated:
            # TS exit level = max_favorable_price + TS_STEP%
            ts_exit_level = max_favorable_price * (1 + TS_STEP_PERCENT/100)
            
            # Check if TS should trigger (price moves UP from max favorable)
            if high >= ts_exit_level:
                exit_price = min(ts_exit_level * 1.001, high)
                exit_type = 'TS SL'
                print(f"   📈 TS TRIGGERED! Exit at {exit_price:.8f}")
                break
        
        print()
    
    # If no exit triggered, use original exit
    if exit_price is None:
        exit_price = float(candle_data.iloc[-1]['open'])  # Use open of final candle
        exit_type = 'Signal'
    
    # Calculate final PnL
    pnl_pct = (entry_price - exit_price) / entry_price * 100  # SHORT formula
    
    print("🎯 SIMULATION RESULTS:")
    print("=" * 30)
    print(f"Entry Price: {entry_price:.8f}")
    print(f"Exit Price: {exit_price:.8f}")
    print(f"Exit Type: {exit_type}")
    print(f"PnL: {pnl_pct:.2f}%")
    print(f"Max Favorable: {max_favorable_price:.8f}")
    print(f"BE Activated: {be_activated}")
    print(f"TS Activated: {ts_activated}")
    print()
    
    # Compare with log
    log_exit_price = 0.009200
    log_pnl = 8.42
    log_type = 'TS SL'
    
    print("📋 LOG COMPARISON:")
    print("=" * 20)
    print(f"Log Exit Price: {log_exit_price:.6f}")
    print(f"Sim Exit Price: {exit_price:.6f}")
    print(f"Price Diff: {abs(exit_price - log_exit_price):.6f}")
    print()
    print(f"Log PnL: {log_pnl:.2f}%")
    print(f"Sim PnL: {pnl_pct:.2f}%")
    print(f"PnL Diff: {abs(pnl_pct - log_pnl):.2f}%")
    print()
    print(f"Log Type: {log_type}")
    print(f"Sim Type: {exit_type}")
    print()
    
    # Verification
    price_tolerance = 0.0001  # 0.01%
    pnl_tolerance = 0.5       # 0.5%
    
    price_match = abs(exit_price - log_exit_price) <= price_tolerance
    pnl_match = abs(pnl_pct - log_pnl) <= pnl_tolerance
    type_match = exit_type == log_type
    
    print("✅ VERIFICATION RESULTS:")
    print("=" * 25)
    print(f"Price Match: {'✅ PASS' if price_match else '❌ FAIL'}")
    print(f"PnL Match: {'✅ PASS' if pnl_match else '❌ FAIL'}")
    print(f"Type Match: {'✅ PASS' if type_match else '❌ FAIL'}")
    print()
    
    if price_match and pnl_match and type_match:
        print("🎉 OVERALL VERIFICATION: ✅ PASSED")
        print("   Tool calculation is CORRECT!")
    else:
        print("⚠️ OVERALL VERIFICATION: ❌ PARTIAL/FAILED")
        if not price_match:
            print("   - Exit price calculation may have precision differences")
        if not pnl_match:
            print("   - PnL calculation may have minor discrepancies")
        if not type_match:
            print("   - Exit type classification differs")

if __name__ == '__main__':
    simulate_full_trade_141()
