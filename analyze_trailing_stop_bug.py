#!/usr/bin/env python3
"""
🔍 BUG ANALYSIS: Trailing Stop Logic Error
Phân tích lỗi trong thuật toán trailing stop của optimization tool
"""

import pandas as pd
import numpy as np

def analyze_trailing_stop_bug():
    """Phân tích bug trong logic trailing stop"""
    print("🐛 BUG ANALYSIS: Trailing Stop Logic Error")
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
        
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return
    
    # ===== SIMULATE TRAILING STOP LOGIC =====
    print(f"\n🔍 SIMULATING TRAILING STOP LOGIC:")
    print("-" * 50)
    
    BE_reached = False
    TS_reached = False
    trailingActive = False
    trailingLevel = 0
    trailingSL = slPrice
    maxTrailingSL = slPrice
    
    print("🎯 CHECKING FOR TRIGGERS:")
    
    for i in range(1, len(trade_candles)):
        candle = trade_candles.iloc[i]
        high = candle['high']
        low = candle['low']
        time = candle['time']
        
        # For SHORT position, we care about LOW prices (favorable movement)
        priceNow = low  # Best price in favor of SHORT
        
        # Check BE trigger
        if not BE_reached and low <= beTrigPrice:
            BE_reached = True
            trailingActive = True
            trailingLevel = 0
            trailingSL = beSLPrice
            maxTrailingSL = beSLPrice
            print(f"   ✅ BE TRIGGERED at {time}")
            print(f"      Low: {low:.6f} <= BE Trigger: {beTrigPrice:.6f}")
            print(f"      New Trailing SL: {trailingSL:.6f}")
            break
        
        # Check TS trigger
        if not TS_reached and low <= tsTrigPrice:
            TS_reached = True
            trailingActive = True
            trailingSL = max(trailingSL, slPrice)
            maxTrailingSL = trailingSL
            print(f"   ✅ TS TRIGGERED at {time}")
            print(f"      Low: {low:.6f} <= TS Trigger: {tsTrigPrice:.6f}")
            print(f"      New Trailing SL: {trailingSL:.6f}")
            break
    
    if not BE_reached and not TS_reached:
        print("   ❌ Neither BE nor TS was triggered")
        print("   ❌ No trailing stop should be active")
        print()
        
        # Find best exit price
        best_low = trade_candles['low'].min()
        best_time = trade_candles[trade_candles['low'] == best_low].iloc[0]['time']
        best_profit = (entry_price - best_low) / entry_price * 100
        
        print(f"💰 BEST POSSIBLE EXIT:")
        print(f"   Best Low: {best_low:.6f}")
        print(f"   Time: {best_time}")
        print(f"   Profit: {best_profit:.2f}%")
        print()
        
        return
    
    # ===== SIMULATE TRAILING LOGIC =====
    if trailingActive:
        print(f"\n🔄 TRAILING STOP SIMULATION:")
        print("-" * 40)
        
        max_trailing_reached = 0
        best_trailing_exit = entry_price
        
        for i in range(1, len(trade_candles)):
            candle = trade_candles.iloc[i]
            high = candle['high']
            low = candle['low']
            time = candle['time']
            
            priceNow = low  # For SHORT, favorable movement is downward
            
            # Calculate distance from entry
            fromEntry = entry_price - priceNow  # Profit for SHORT
            fromEntryPct = fromEntry / entry_price * 100
            
            # Calculate step count
            stepCount = 0
            if TS_reached:
                stepCount = int((fromEntryPct - ts_trig) / ts_step)
                
            if BE_reached:
                fromBETrigPct = (entry_price - priceNow) / entry_price * 100
                if fromBETrigPct >= be:
                    stepCount = int((fromBETrigPct - be) / ts_step)
                else:
                    stepCount = 0
            
            # Update trailing level
            if stepCount > trailingLevel:
                trailingLevel = stepCount
                
                # 🚨 HERE IS THE POTENTIAL BUG! 🚨
                # Calculate new trailing SL
                if TS_reached:
                    # This formula might be wrong for SHORT positions
                    newTrailingSL = entry_price * (1 - (ts_trig + trailingLevel * ts_step) / 100)
                else:
                    newTrailingSL = entry_price * (1 - (be + trailingLevel * ts_step) / 100)
                
                if BE_reached:
                    newTrailingSL = min(newTrailingSL, beSLPrice)  # For SHORT: use min
                
                trailingSL = newTrailingSL
                max_trailing_reached = max(max_trailing_reached, trailingLevel)
                
                print(f"   Step {i:2d} @ {time}")
                print(f"      Low: {low:.6f}")
                print(f"      Profit: {fromEntryPct:.2f}%")
                print(f"      Step Count: {stepCount}")
                print(f"      Trailing Level: {trailingLevel}")
                print(f"      New Trailing SL: {newTrailingSL:.6f}")
                
                # Check if this creates unrealistic exit price
                if newTrailingSL < 0.008919:
                    print(f"      🚨 UNREALISTIC! This SL is too low!")
                    
                best_trailing_exit = newTrailingSL
        
        print(f"\n🎯 FINAL TRAILING RESULTS:")
        print(f"   Max Trailing Level: {max_trailing_reached}")
        print(f"   Best Trailing Exit: {best_trailing_exit:.6f}")
        
        if best_trailing_exit <= 0.008919:
            final_profit = (entry_price - best_trailing_exit) / entry_price * 100
            print(f"   Final Profit: {final_profit:.2f}%")
            print(f"   🎯 This explains the 10.24% claim!")
        else:
            print(f"   🚨 Exit price doesn't match optimization claim of 0.008919")
    
    # ===== BUG ANALYSIS =====
    print(f"\n🐛 BUG ANALYSIS:")
    print("=" * 40)
    
    print("POTENTIAL ISSUES FOUND:")
    print("1️⃣ TRAILING STOP FORMULA:")
    print("   Code uses: entry_price * (1 - (ts_trig + level * ts_step) / 100)")
    print("   This can create unrealistically low exit prices")
    print()
    
    print("2️⃣ STEP CALCULATION:")
    print("   stepCount = int((fromEntryPct - ts_trig) / ts_step)")
    print("   This integer division can create large jumps")
    print()
    
    print("3️⃣ PRICE VALIDATION:")
    print("   No check if calculated exit price is reachable in actual data")
    print("   Tool assumes price can reach any calculated level")
    print()
    
    print("🔧 RECOMMENDED FIXES:")
    print("   ✅ Add price validation against actual candle data")
    print("   ✅ Cap exit prices at actual achievable levels")
    print("   ✅ Use more conservative trailing stop formulas")
    print("   ✅ Add reality checks for profit claims")

if __name__ == '__main__':
    analyze_trailing_stop_bug()
