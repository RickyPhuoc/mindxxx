#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 EXACT REPLICATION OF TRADE #141 LOGIC
========================================
Sử dụng chính xác logic từ backtest_realistic_engine.py
"""

import pandas as pd
from datetime import datetime

def debug_trade_141():
    print("🔍 EXACT REPLICATION OF TRADE #141")
    print("=" * 50)
    
    # LOAD DATA - Trade 141 uses "data chart full info.csv" not BOME
    try:
        candles = pd.read_csv("data chart full info.csv")
        print(f"📊 Loaded {len(candles)} candles from data chart full info.csv")
    except Exception as e:
        print(f"❌ Error loading candles: {e}")
        return
    
    # TRADE PARAMETERS (exact from log)
    entryPrice = 0.0100388  # CORRECTED: This matches the data chart full info.csv
    side = 'SHORT'
    sl = 4.41  # %
    be = 1.76  # %
    ts_trig = 7.12  # %
    ts_step = 0.26  # %
    
    # Convert datetime strings (handle timezone)
    candles['time'] = pd.to_datetime(candles['time'])
    
    # FIND ENTRY AND EXIT CANDLES (use timezone-aware if needed)
    if candles['time'].dt.tz is not None:
        entry_time = pd.to_datetime('2025-06-30 10:30:00').tz_localize(candles['time'].dt.tz)
        exit_time = pd.to_datetime('2025-07-02 08:30:00').tz_localize(candles['time'].dt.tz)
    else:
        entry_time = pd.to_datetime('2025-06-30 10:30:00')
        exit_time = pd.to_datetime('2025-07-02 08:30:00')
    
    # Get relevant candles
    mask = (candles['time'] >= entry_time) & (candles['time'] <= exit_time)
    prices = candles[mask].copy().reset_index(drop=True)
    
    if len(prices) == 0:
        print("❌ No candles found in time range")
        return
    
    print(f"🎯 TRADE SETUP:")
    print(f"   Entry: {entry_time} @ {entryPrice}")
    print(f"   Side: {side}")
    print(f"   SL: {sl}%, BE: {be}%, TS: {ts_trig}%/{ts_step}%")
    print(f"   Candles: {len(prices)}")
    
    # CALCULATE LEVELS (exact logic from engine)
    slPrice = entryPrice * (1 + sl/100) if sl > 0 else None
    
    # BE logic
    if be > 0:
        BE_reached = False
        beTriggerPrice = entryPrice * (1 - be/100)  # SHORT: trigger at lower price
        beSLPrice = entryPrice  # Move SL to breakeven
    elif be == 0:
        BE_reached = False
        beTriggerPrice = entryPrice
        beSLPrice = entryPrice
    else:
        BE_reached = False
        beTriggerPrice = None
        beSLPrice = None
    
    # TS logic
    if ts_trig > 0:
        TS_reached = False
        tsTriggerPrice = entryPrice * (1 - ts_trig/100)  # SHORT: trigger at lower price
    else:
        TS_reached = False
        tsTriggerPrice = None
    
    # STATE VARIABLES (exact from engine)
    current_sl = slPrice
    trailing_active = False
    highest_profit = 0
    
    print(f"📏 LEVELS:")
    print(f"   SL: {slPrice:.8f} (+{sl:.2f}%)")
    print(f"   BE Trigger: {beTriggerPrice:.8f} (-{be:.2f}%)")
    print(f"   TS Trigger: {tsTriggerPrice:.8f} (-{ts_trig:.2f}%)")
    print()
    
    # LOG FOR COMPARISON
    log = []
    
    # SCAN CANDLES (exact logic from engine)
    for i in range(len(prices)):
        candle = prices.iloc[i]
        high = float(candle['high'])
        low = float(candle['low'])
        close = float(candle['close'])
        candle_time = candle['time']
        
        if i == 0:
            start_price = entryPrice
        else:
            start_price = float(candle['open'])
        
        print(f"Candle {i+1:2d} ({candle_time.strftime('%m/%d %H:%M')}): H={high:.6f} L={low:.6f} C={close:.6f}")
        
        # 1. CHECK SL HIT FIRST
        if current_sl is not None:
            if side == 'SHORT' and high >= current_sl:
                exit_price = min(current_sl, high)
                exit_type = "TS SL" if trailing_active else ("BE SL" if BE_reached else "SL")
                pnl_pct = (entryPrice - exit_price) / entryPrice * 100
                
                print(f"   🛑 {exit_type} HIT: {exit_price:.6f} (PnL: {pnl_pct:.2f}%)")
                return exit_price, exit_type, pnl_pct, candle_time
        
        # 2. CHECK BE TRIGGER
        if not BE_reached and beTriggerPrice is not None:
            if be > 0 and low <= beTriggerPrice:
                BE_reached = True
                if not trailing_active:
                    current_sl = beSLPrice
                print(f"   🎯 BE TRIGGERED: {low:.6f} (SL -> {beSLPrice:.6f})")
            elif be == 0 and low < entryPrice:
                BE_reached = True
                if not trailing_active:
                    current_sl = beSLPrice
                print(f"   🎯 BE TRIGGERED (immediate): {low:.6f}")
        
        # 3. CHECK TS TRIGGER  
        if not TS_reached and tsTriggerPrice is not None:
            if ts_trig > 0 and low <= tsTriggerPrice:
                TS_reached = True
                trailing_active = True
                current_sl = min(current_sl or float('inf'), entryPrice)
                print(f"   📈 TS TRIGGERED: {low:.6f} (Trailing active)")
        
        # 4. UPDATE TRAILING SL
        if trailing_active and ts_step > 0:
            current_price = low  # For SHORT, use lowest for max profit
            profit = entryPrice - current_price
            profit_pct = profit / entryPrice * 100
            
            if profit_pct > highest_profit:
                highest_profit = profit_pct
                
                if profit_pct >= ts_trig:
                    trailing_steps = int((profit_pct - ts_trig) / ts_step)
                    new_sl_pct = ts_trig + trailing_steps * ts_step
                    new_trailing_sl = entryPrice * (1 - new_sl_pct / 100)
                    
                    if current_sl is None or new_trailing_sl < current_sl:
                        current_sl = new_trailing_sl
                        print(f"   📉 Trailing SL updated: {current_sl:.6f} (profit: {profit_pct:.2f}%, steps: {trailing_steps})")
    
    # Continue even if no SL hit to see full path
    print(f"   💡 End of candle - SL: {current_sl:.6f if current_sl else 'None'}, trailing: {trailing_active}")
    
    # Normal exit (this should not happen if TS works correctly)
    exit_price = float(prices.iloc[-1]['close'])
    exit_type = "Signal"  
    pnl_pct = (entryPrice - exit_price) / entryPrice * 100
    exit_time = prices.iloc[-1]['time']
    
    print(f"   ✅ Normal exit: {exit_price:.6f} (PnL: {pnl_pct:.2f}%)")
    return exit_price, exit_type, pnl_pct, exit_time

if __name__ == "__main__":
    result = debug_trade_141()
    if result:
        exit_price, exit_type, pnl_pct, exit_time = result
        
        print()
        print("🎯 FINAL RESULTS:")
        print("=" * 30)
        print(f"Exit Price: {exit_price:.6f}")
        print(f"Exit Type: {exit_type}")
        print(f"PnL: {pnl_pct:.2f}%")
        print(f"Exit Time: {exit_time}")
        
        print()
        print("📋 COMPARISON WITH LOG:")
        print("=" * 30)
        print(f"Log Exit: 0.009200")
        print(f"Sim Exit: {exit_price:.6f}")
        print(f"Diff: {abs(0.009200 - exit_price):.6f}")
        print()
        print(f"Log PnL: 8.42%")
        print(f"Sim PnL: {pnl_pct:.2f}%") 
        print(f"Diff: {abs(8.42 - pnl_pct):.2f}%")
