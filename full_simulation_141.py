#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 FULL SIMULATION WITH DETAILED LOGGING
========================================
Mô phỏng chi tiết tất cả candles để tìm exit chính xác
"""

import pandas as pd
from datetime import datetime

def full_simulation_trade_141():
    print("🔍 FULL SIMULATION TRADE #141")
    print("=" * 50)
    
    # LOAD DATA
    try:
        candles = pd.read_csv("data chart full info.csv")
        print(f"📊 Loaded {len(candles)} candles")
    except Exception as e:
        print(f"❌ Error loading candles: {e}")
        return
    
    # TRADE PARAMETERS
    entryPrice = 0.0100388
    side = 'SHORT'
    sl = 4.41  # %
    be = 1.76  # %
    ts_trig = 7.12  # %
    ts_step = 0.26  # %
    
    # Convert datetime
    candles['time'] = pd.to_datetime(candles['time'])
    
    # Get time range
    if candles['time'].dt.tz is not None:
        entry_time = pd.to_datetime('2025-06-30 10:30:00').tz_localize(candles['time'].dt.tz)
        exit_time = pd.to_datetime('2025-07-02 08:30:00').tz_localize(candles['time'].dt.tz)
    else:
        entry_time = pd.to_datetime('2025-06-30 10:30:00')
        exit_time = pd.to_datetime('2025-07-02 08:30:00')
    
    # Get relevant candles
    mask = (candles['time'] >= entry_time) & (candles['time'] <= exit_time)
    prices = candles[mask].copy().reset_index(drop=True)
    
    print(f"🎯 SIMULATION: {len(prices)} candles from {entry_time} to {exit_time}")
    
    # CALCULATE LEVELS
    slPrice = entryPrice * (1 + sl/100) if sl > 0 else None
    beTriggerPrice = entryPrice * (1 - be/100) if be > 0 else entryPrice
    tsTriggerPrice = entryPrice * (1 - ts_trig/100) if ts_trig > 0 else None
    
    # STATE VARIABLES
    current_sl = slPrice
    trailing_active = False
    highest_profit = 0
    BE_reached = False
    TS_reached = False
    
    print(f"📏 INITIAL LEVELS:")
    print(f"   Entry: {entryPrice:.6f}")
    print(f"   SL: {slPrice:.6f} (+{sl:.2f}%)")
    print(f"   BE Trigger: {beTriggerPrice:.6f} (-{be:.2f}%)")
    print(f"   TS Trigger: {tsTriggerPrice:.6f} (-{ts_trig:.2f}%)")
    print()
    
    # DETAILED SIMULATION
    for i in range(len(prices)):
        candle = prices.iloc[i]
        high = float(candle['high'])
        low = float(candle['low'])
        close = float(candle['close'])
        candle_time = candle['time']
        
        print(f"Candle {i+1:2d} ({candle_time.strftime('%m/%d %H:%M')}): H={high:.6f} L={low:.6f} C={close:.6f}")
        
        # CHECK SL HIT (HIGHEST PRIORITY)
        if current_sl is not None and high >= current_sl:
            exit_price = min(current_sl, high)
            exit_type = "TS SL" if trailing_active else ("BE SL" if BE_reached else "SL")
            pnl_pct = (entryPrice - exit_price) / entryPrice * 100
            
            print(f"   🛑 {exit_type} HIT: exit @ {exit_price:.6f} (PnL: {pnl_pct:.2f}%)")
            print(f"   📍 Exit time: {candle_time}")
            return exit_price, exit_type, pnl_pct, candle_time
        
        # CHECK BE TRIGGER
        if not BE_reached and beTriggerPrice is not None:
            if (be > 0 and low <= beTriggerPrice) or (be == 0 and low < entryPrice):
                BE_reached = True
                if not trailing_active:
                    current_sl = entryPrice  # Breakeven
                print(f"   🎯 BE TRIGGERED @ {low:.6f} (SL -> BE: {entryPrice:.6f})")
        
        # CHECK TS TRIGGER
        if not TS_reached and tsTriggerPrice is not None:
            if ts_trig > 0 and low <= tsTriggerPrice:
                TS_reached = True
                trailing_active = True
                current_sl = min(current_sl or float('inf'), entryPrice)
                print(f"   📈 TS TRIGGERED @ {low:.6f} (Trailing activated)")
        
        # UPDATE TRAILING SL
        if trailing_active and ts_step > 0:
            current_price = low
            profit = entryPrice - current_price
            profit_pct = profit / entryPrice * 100
            
            if profit_pct > highest_profit:
                old_highest = highest_profit
                highest_profit = profit_pct
                
                if profit_pct >= ts_trig:
                    trailing_steps = int((profit_pct - ts_trig) / ts_step)
                    new_sl_pct = ts_trig + trailing_steps * ts_step
                    new_trailing_sl = entryPrice * (1 - new_sl_pct / 100)
                    
                    if current_sl is None or new_trailing_sl < current_sl:
                        old_sl = current_sl
                        current_sl = new_trailing_sl
                        print(f"   📉 Trailing SL: {old_sl:.6f} -> {current_sl:.6f}")
                        print(f"       Profit: {old_highest:.2f}% -> {profit_pct:.2f}% (steps: {trailing_steps})")
        
        # LOG CURRENT STATE
        profit_current = (entryPrice - low) / entryPrice * 100 if low < entryPrice else 0
        sl_display = f"{current_sl:.6f}" if current_sl is not None else "None"
        print(f"   💡 State: SL={sl_display}, profit={profit_current:.2f}%, trailing={trailing_active}")
        print()
    
    # Should not reach here if TS works correctly
    exit_price = float(prices.iloc[-1]['close'])
    exit_type = "Signal"
    pnl_pct = (entryPrice - exit_price) / entryPrice * 100
    exit_time = prices.iloc[-1]['time']
    
    print(f"⚠️ UNEXPECTED: Normal signal exit @ {exit_price:.6f} (PnL: {pnl_pct:.2f}%)")
    return exit_price, exit_type, pnl_pct, exit_time

if __name__ == "__main__":
    result = full_simulation_trade_141()
    if result:
        exit_price, exit_type, pnl_pct, exit_time = result
        
        print()
        print("🎯 FINAL COMPARISON:")
        print("=" * 30)
        print(f"LOG: Exit @ 0.009200, PnL: 8.42%, Type: TS SL")
        print(f"SIM: Exit @ {exit_price:.6f}, PnL: {pnl_pct:.2f}%, Type: {exit_type}")
        print(f"DIFF: Price: {abs(0.009200 - exit_price):.6f}, PnL: {abs(8.42 - pnl_pct):.2f}%")
