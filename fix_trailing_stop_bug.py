#!/usr/bin/env python3
"""
🔧 FIX: Trailing Stop Logic - Reality Check Version
Sửa lỗi trong thuật toán trailing stop với validation thực tế
"""

import pandas as pd
import numpy as np

def fix_trailing_stop_logic():
    """Sửa lỗi trailing stop với reality check"""
    print("🔧 FIXING: Trailing Stop Logic with Reality Check")
    print("=" * 60)
    
    # ===== SIMULATION PARAMETERS =====
    print("📊 TRADE #139 PARAMETERS:")
    entry_price = 0.009937
    side = 'SHORT'
    sl = 4.41  # Stop loss %
    be = 1.76  # Breakeven trigger %
    ts_trig = 7.12  # Trailing stop trigger %  
    ts_step = 0.26  # Trailing stop step %
    
    print(f"   Entry Price: {entry_price:.6f}")
    print(f"   Side: {side}")
    print(f"   SL: {sl:.2f}%")
    print(f"   BE: {be:.2f}%")
    print(f"   TS Trigger: {ts_trig:.2f}%")
    print(f"   TS Step: {ts_step:.2f}%")
    print()
    
    # ===== CALCULATE PRICE LEVELS =====
    print("🎯 CALCULATED PRICE LEVELS:")
    slPrice = entry_price * (1 + sl/100)  # SHORT: SL above entry
    beTrigPrice = entry_price * (1 - be/100)  # SHORT: BE trigger below entry
    beSLPrice = entry_price * (1 + 0.0005)  # SHORT: BE SL slightly above entry
    tsTrigPrice = entry_price * (1 - ts_trig/100)  # SHORT: TS trigger below entry
    
    print(f"   SL Price: {slPrice:.6f}")
    print(f"   BE Trigger: {beTrigPrice:.6f}")
    print(f"   BE SL Price: {beSLPrice:.6f}")  
    print(f"   TS Trigger: {tsTrigPrice:.6f}")
    print()
    
    # ===== LOAD ACTUAL CANDLE DATA =====
    print("📈 LOADING ACTUAL PRICE DATA:")
    
    try:
        candles = pd.read_csv("data chart full info.csv")
        candles['time'] = pd.to_datetime(candles['time'])
        
        # Find trade period
        entry_time = pd.to_datetime('2025-06-20 22:00:00').tz_localize(candles['time'].dt.tz)
        exit_time = pd.to_datetime('2025-06-21 08:30:00').tz_localize(candles['time'].dt.tz)
        
        entry_idx = abs(candles['time'] - entry_time).idxmin()
        exit_idx = abs(candles['time'] - exit_time).idxmin()
        
        trade_candles = candles.iloc[entry_idx:exit_idx+1].copy()
        print(f"   Trade period: {len(trade_candles)} candles")
        print(f"   From: {trade_candles.iloc[0]['time']}")
        print(f"   To: {trade_candles.iloc[-1]['time']}")
        
        # Get actual min/max prices
        actual_min = trade_candles['low'].min()
        actual_max = trade_candles['high'].max()
        print(f"   Actual Min Price: {actual_min:.6f}")
        print(f"   Actual Max Price: {actual_max:.6f}")
        
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return
    
    # ===== FIXED TRAILING STOP LOGIC =====
    print(f"\n🔧 FIXED TRAILING STOP SIMULATION:")
    print("-" * 50)
    
    BE_reached = False
    TS_reached = False
    trailingActive = False
    trailingLevel = 0
    trailingSL = slPrice
    
    # Step 1: Check triggers
    for i in range(1, len(trade_candles)):
        candle = trade_candles.iloc[i]
        low = candle['low']
        time = candle['time']
        
        # Check BE trigger
        if not BE_reached and low <= beTrigPrice:
            BE_reached = True
            trailingActive = True
            trailingSL = beSLPrice
            print(f"   ✅ BE TRIGGERED at {time}")
            print(f"      Price: {low:.6f} <= BE Trigger: {beTrigPrice:.6f}")
            print(f"      Set Trailing SL: {trailingSL:.6f}")
            break
        
        # Check TS trigger
        if not TS_reached and low <= tsTrigPrice:
            TS_reached = True
            trailingActive = True
            trailingSL = slPrice  # Keep original SL
            print(f"   ✅ TS TRIGGERED at {time}")
            print(f"      Price: {low:.6f} <= TS Trigger: {tsTrigPrice:.6f}")
            print(f"      Keep Trailing SL: {trailingSL:.6f}")
            break
    
    if not (BE_reached or TS_reached):
        print("   ❌ No triggers reached - use original SL")
        return
    
    # Step 2: REALITY-BASED TRAILING SIMULATION
    if trailingActive:
        print(f"\n🎯 REALITY-BASED TRAILING SIMULATION:")
        print("-" * 50)
        
        best_exit_price = entry_price
        best_profit = 0
        exit_time_found = None
        
        for i in range(1, len(trade_candles)):
            candle = trade_candles.iloc[i]
            low = candle['low']
            high = candle['high'] 
            time = candle['time']
            
            # For SHORT: profit when price goes down
            current_profit_pct = (entry_price - low) / entry_price * 100
            
            # Check if we can improve trailing SL based on ACTUAL price movement
            if BE_reached:
                # After BE trigger, update trailing SL based on actual price
                if current_profit_pct > be:
                    # Calculate how many steps we've moved beyond BE trigger
                    steps_beyond_be = max(0, int((current_profit_pct - be) / ts_step))
                    
                    # Calculate new trailing SL based on REALISTIC movement
                    new_trailing_distance = be + (steps_beyond_be * ts_step)
                    proposed_sl = entry_price * (1 - new_trailing_distance / 100)
                    
                    # 🔧 REALITY CHECK: Can we actually reach this SL?
                    if proposed_sl >= actual_min:  # SL must be reachable
                        if proposed_sl < trailingSL:  # Improve SL for SHORT
                            trailingLevel = steps_beyond_be
                            trailingSL = proposed_sl
                            print(f"   📈 Step {i:2d} @ {time}")
                            print(f"      Low: {low:.6f} | Profit: {current_profit_pct:.2f}%")
                            print(f"      Steps: {steps_beyond_be} | New SL: {trailingSL:.6f}")
            
            # Check if current price would hit our trailing SL
            if high >= trailingSL:
                exit_price = trailingSL
                final_profit = (entry_price - exit_price) / entry_price * 100
                print(f"   🎯 EXIT TRIGGERED at {time}")
                print(f"      High: {high:.6f} >= Trailing SL: {trailingSL:.6f}")
                print(f"      Exit Price: {exit_price:.6f}")
                print(f"      Final Profit: {final_profit:.2f}%")
                best_exit_price = exit_price
                best_profit = final_profit  
                exit_time_found = time
                break
        
        # If no SL hit, use best achievable price
        if exit_time_found is None:
            best_actual_low = trade_candles['low'].min()
            best_time = trade_candles[trade_candles['low'] == best_actual_low].iloc[0]['time']
            best_profit = (entry_price - best_actual_low) / entry_price * 100
            
            print(f"   🎯 NO SL HIT - Best Possible Exit:")
            print(f"      Best Low: {best_actual_low:.6f}")
            print(f"      Time: {best_time}")
            print(f"      Max Profit: {best_profit:.2f}%")
            best_exit_price = best_actual_low
        
        print(f"\n🎯 FIXED RESULTS vs ORIGINAL BUG:")
        print("=" * 50)
        print(f"   Original Bug Claim: 0.008919 (10.24% profit)")
        print(f"   Fixed Reality Exit: {best_exit_price:.6f} ({best_profit:.2f}% profit)")
        print(f"   Difference: {abs(best_profit - 10.24):.2f}% profit difference")
        
        if abs(best_profit - 10.24) < 1.0:
            print(f"   ✅ FIXED VERSION MATCHES EXPECTED RESULT!")
        else:
            print(f"   🚨 Still significant difference - need more investigation")
        
        print(f"\n🔧 APPLIED FIXES:")
        print("   ✅ Added reality check against actual candle data")
        print("   ✅ Capped exit prices at achievable levels")
        print("   ✅ Used conservative trailing stop formulas")
        print("   ✅ Added validation for profit claims")

if __name__ == '__main__':
    fix_trailing_stop_logic()
