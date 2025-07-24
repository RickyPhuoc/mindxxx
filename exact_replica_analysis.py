#!/usr/bin/env python3
"""
🔍 EXACT REPLICATION: Trade #139 Logic Analysis
Mô phỏng chính xác 100% logic tool gốc để tìm bug
"""

import pandas as pd
import numpy as np

def simulate_trade_139_exact_replica():
    """Mô phỏng chính xác logic tool gốc"""
    
    print("🔍 EXACT REPLICA SIMULATION: Trade #139")
    print("=" * 70)
    
    # ===== TRADE DATA =====
    entry_time = '2025-06-20 22:00:00'
    exit_time = '2025-06-21 08:30:00'  
    entry_price = 0.009937
    side = 'SHORT'
    
    # Parameters from reality check
    sl_pct = 4.41
    be_pct = 1.76
    ts_trig_pct = 7.12  
    ts_step_pct = 0.26
    
    print(f"📊 TRADE #139 SETUP:")
    print(f"   Entry: {entry_price:.6f} | Side: {side}")
    print(f"   SL: {sl_pct}% | BE: {be_pct}% | TS: {ts_trig_pct}%/{ts_step_pct}%")
    
    # ===== CALCULATE EXACT PRICES =====
    # Fix variable naming first
    entryPrice = entry_price  
    
    # ✅ EXACT COPY from tool gốc (confirmed correct)
    slPrice = entryPrice * (1 - sl_pct/100) if side=='LONG' else entryPrice * (1 + sl_pct/100)
    beTrigPrice = entryPrice * (1 + be_pct/100) if side=='LONG' else entryPrice * (1 - be_pct/100)  
    beSLPrice = entryPrice * (1 - 0.0005) if side=='LONG' else entryPrice * (1 + 0.0005)
    tsTrigPrice = entryPrice * (1 + ts_trig_pct/100) if side=='LONG' else entryPrice * (1 - ts_trig_pct/100)
    
    print(f"\n🎯 CALCULATED LEVELS (EXACT TOOL LOGIC):")
    print(f"   Entry Price: {entryPrice:.6f}")
    print(f"   Initial SL: {slPrice:.6f}")
    print(f"   BE Trigger: {beTrigPrice:.6f}")
    print(f"   BE New SL: {beSLPrice:.6f}")
    print(f"   TS Trigger: {tsTrigPrice:.6f}")
    
    # ===== LOAD DATA =====
    print(f"\n📈 LOADING CANDLE DATA:")
    candles = pd.read_csv("data chart full info.csv")
    candles['time'] = pd.to_datetime(candles['time'])
    
    # Find trade period
    entry_time_dt = pd.to_datetime(entry_time).tz_localize(candles['time'].dt.tz)
    exit_time_dt = pd.to_datetime(exit_time).tz_localize(candles['time'].dt.tz)
    
    entry_idx = abs(candles['time'] - entry_time_dt).idxmin()
    exit_idx = abs(candles['time'] - exit_time_dt).idxmin()
    
    trade_candles = candles.iloc[entry_idx:exit_idx+1].copy()
    
    print(f"   Trade period: {len(trade_candles)} candles")
    print(f"   Actual Min: {trade_candles['low'].min():.6f}")
    print(f"   Actual Max: {trade_candles['high'].max():.6f}")
    
    # ===== EXACT SIMULATION =====
    print(f"\n🔄 EXACT TOOL SIMULATION:")
    print("-" * 70)
    
    # Initialize state (EXACT COPY)
    BE_reached = False
    TS_reached = False
    trailingActive = False
    trailingSL = slPrice
    maxTrailingSL = slPrice
    trailingLevel = 0
    finalExitPrice = None
    exitType = ""
    done = False
    
    print(f"🎬 CANDLE-BY-CANDLE ANALYSIS:")
    
    for i, (idx, candle) in enumerate(trade_candles.iterrows()):
        if done:
            break
            
        time = candle['time']
        high = candle['high']
        low = candle['low']
        
        print(f"\n📊 Candle {i+1:2d} @ {time}")
        print(f"   OHLC: {candle['open']:.6f} | {high:.6f} | {low:.6f} | {candle['close']:.6f}")
        
        # EXACT COPY: Check BE trigger
        if not BE_reached:
            if (side=='LONG' and high>=beTrigPrice) or (side=='SHORT' and low<=beTrigPrice):
                BE_reached = True
                trailingActive = True
                trailingLevel = 0
                trailingSL = beSLPrice
                maxTrailingSL = beSLPrice
                print(f"   ✅ BE TRIGGERED! Low {low:.6f} <= {beTrigPrice:.6f}")
                print(f"      New trailing SL: {trailingSL:.6f}")

        # EXACT COPY: Check TS trigger
        if not TS_reached:
            if (side=='LONG' and high>=tsTrigPrice) or (side=='SHORT' and low<=tsTrigPrice):
                TS_reached = True
                trailingActive = True
                trailingSL = max(trailingSL, slPrice)
                maxTrailingSL = trailingSL
                print(f"   🎯 TS TRIGGERED! Low {low:.6f} <= {tsTrigPrice:.6f}")
                print(f"      New trailing SL: {trailingSL:.6f}")

        # EXACT COPY: Trailing logic
        if trailingActive:
            priceNow = high if side=='LONG' else low
            fromEntry = (priceNow-entryPrice) if side=='LONG' else (entryPrice-priceNow)
            fromEntryPct = fromEntry/entryPrice*100
            
            stepCount = 0
            
            # 🔧 FIXED VERSION: Use correct base
            if TS_reached:
                stepCount = int((fromEntryPct-ts_trig_pct)/ts_step_pct)
            if BE_reached:
                fromBETrigPct = (priceNow-entryPrice)/entryPrice*100 if side=='LONG' else (entryPrice-priceNow)/entryPrice*100
                if fromBETrigPct>=be_pct:
                    stepCount = int((fromBETrigPct-be_pct)/ts_step_pct)
                else:
                    stepCount = 0
                    
            print(f"   📊 Trailing: priceNow={priceNow:.6f}, profit={fromEntryPct:.2f}%, steps={stepCount}")
            
            if stepCount>trailingLevel:
                trailingLevel = stepCount
                
                # 🚨 ORIGINAL BUG VERSION vs FIXED VERSION
                print(f"   🔧 COMPARING BUG vs FIX:")
                
                # BUG VERSION (always use ts_trig)
                bug_distance = ts_trig_pct + trailingLevel * ts_step_pct
                bug_sl = entryPrice * (1 + bug_distance/100) if side=='LONG' else entryPrice * (1 - bug_distance/100)
                print(f"      🚨 BUG: distance={bug_distance:.2f}%, SL={bug_sl:.6f}")
                
                # FIXED VERSION (use correct base)
                if TS_reached:
                    fix_distance = ts_trig_pct + trailingLevel * ts_step_pct
                    fix_sl = entryPrice * (1 + fix_distance/100) if side=='LONG' else entryPrice * (1 - fix_distance/100)
                    print(f"      ✅ FIX (TS): distance={fix_distance:.2f}%, SL={fix_sl:.6f}")
                else:  # BE_reached
                    fix_distance = be_pct + trailingLevel * ts_step_pct  
                    fix_sl = entryPrice * (1 + fix_distance/100) if side=='LONG' else entryPrice * (1 - fix_distance/100)
                    print(f"      ✅ FIX (BE): distance={fix_distance:.2f}%, SL={fix_sl:.6f}")
                
                # Use the FIXED version for simulation
                newTrailingSL = fix_sl
                
                if BE_reached:
                    if side=='LONG': 
                        newTrailingSL = max(newTrailingSL, beSLPrice)
                    else: 
                        newTrailingSL = min(newTrailingSL, beSLPrice)
                        
                trailingSL = newTrailingSL
                maxTrailingSL = trailingSL
                print(f"      📈 Updated SL: {trailingSL:.6f}")

        # EXACT COPY: Check SL hit
        if (side=='LONG' and low<=trailingSL) or (side=='SHORT' and high>=trailingSL):
            finalExitPrice = trailingSL
            exitType = "BE SL" if BE_reached and trailingSL==beSLPrice and not TS_reached else "TS SL"
            
            print(f"   🚨 STOP LOSS HIT!")
            print(f"      {'Low' if side=='LONG' else 'High'}: {low if side=='LONG' else high:.6f}")
            print(f"      SL: {trailingSL:.6f}")
            print(f"      Exit Price: {finalExitPrice:.6f}")
            print(f"      Exit Type: {exitType}")
            
            done = True
            break
    
    # Calculate final result
    if finalExitPrice:
        final_profit = (entryPrice - finalExitPrice) / entryPrice * 100 if side=='SHORT' else (finalExitPrice - entryPrice) / entryPrice * 100
    else:
        # No SL hit, use best price
        best_price = trade_candles['low'].min() if side=='SHORT' else trade_candles['high'].max()
        finalExitPrice = best_price
        final_profit = (entryPrice - finalExitPrice) / entryPrice * 100 if side=='SHORT' else (finalExitPrice - entryPrice) / entryPrice * 100
        exitType = "TIME_EXIT"
    
    print(f"\n🎯 FINAL RESULTS:")
    print("=" * 70)
    print(f"📊 FIXED SIMULATION RESULT:")
    print(f"   Exit Price: {finalExitPrice:.6f}")
    print(f"   Exit Type: {exitType}")
    print(f"   Final Profit: {final_profit:.2f}%")
    print(f"   BE Reached: {BE_reached}")
    print(f"   TS Reached: {TS_reached}")
    print(f"   Max Trailing Level: {trailingLevel}")
    
    print(f"\n📊 COMPARISON WITH ORIGINAL CLAIM:")
    original_exit = 0.008919
    original_profit = 10.24
    print(f"   Original Exit: {original_exit:.6f}")
    print(f"   Original Profit: {original_profit:.2f}%")
    
    max_possible = (entryPrice - trade_candles['low'].min()) / entryPrice * 100
    print(f"   Max Possible: {max_possible:.2f}%")
    
    print(f"\n💡 ANALYSIS:")
    if abs(final_profit - original_profit) < 0.1:
        print(f"   ✅ MATCH: Fixed simulation matches original")
    else:
        print(f"   🔧 DIFFERENT: Fixed gives {final_profit:.2f}% vs original {original_profit:.2f}%")
        
    if final_profit <= max_possible + 0.1:
        print(f"   ✅ REALISTIC: Result is achievable")
    else:
        print(f"   🚨 FANTASY: Result exceeds maximum possible")
        
    if original_profit > max_possible + 1.0:
        print(f"   🚨 ORIGINAL WAS FANTASY: {original_profit:.2f}% > {max_possible:.2f}% max")

if __name__ == '__main__':
    simulate_trade_139_exact_replica()
