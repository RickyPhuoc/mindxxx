#!/usr/bin/env python3
"""
🔬 INDEPENDENT SIMULATION: Trade #139 with New Parameters
Mô phỏng độc lập Trade #139 với parameters từ tool mới
"""

import pandas as pd
import numpy as np

def simulate_trade_139_with_new_params():
    """Mô phỏng Trade #139 với parameters mới"""
    
    print("🔬 INDEPENDENT SIMULATION: Trade #139")
    print("=" * 60)
    
    # ===== TRADE #139 DATA =====
    print("📊 TRADE #139 ORIGINAL DATA:")
    entry_time = '2025-06-20 22:00:00'
    exit_time = '2025-06-21 08:30:00'
    entry_price = 0.009937
    side = 'SHORT'
    
    # Original result to compare
    original_exit = 0.008919
    original_profit = 10.24
    
    print(f"   Entry Time: {entry_time}")
    print(f"   Entry Price: {entry_price:.6f}")
    print(f"   Side: {side}")
    print(f"   Original Exit: {original_exit:.6f}")
    print(f"   Original Profit: {original_profit:.2f}%")
    print()
    
    # ===== NEW TOOL PARAMETERS =====
    print("🆕 NEW TOOL PARAMETERS:")
    sl_pct = 4.41
    be_pct = 1.76  
    ts_trig_pct = 7.12
    ts_step_pct = 0.26
    
    print(f"   SL: {sl_pct:.2f}%")
    print(f"   BE: {be_pct:.2f}%")
    print(f"   TS Trigger: {ts_trig_pct:.2f}%")
    print(f"   TS Step: {ts_step_pct:.2f}%")
    print()
    
    # ===== CALCULATE PRICE LEVELS =====
    print("🎯 CALCULATED PRICE LEVELS:")
    sl_price = entry_price * (1 + sl_pct/100)  # SHORT: SL above entry (loss when price goes up)
    be_trigger = entry_price * (1 - be_pct/100)  # SHORT: BE trigger below entry (profit zone)
    
    # 🔧 CORRECTED BE LOGIC: BE SL đảm bảo lợi nhuận +0.05%
    # LONG: BE SL = entry + 0.05% (cao hơn entry để có lãi khi exit)
    # SHORT: BE SL = entry - 0.05% (thấp hơn entry để có lãi khi exit)
    be_sl = entry_price * (1 - 0.0005) if side == 'SHORT' else entry_price * (1 + 0.0005)
    
    ts_trigger = entry_price * (1 - ts_trig_pct/100)  # SHORT: TS trigger below entry (big profit zone)
    
    print(f"🚨 CORRECTED BE LOGIC:")
    print(f"   Entry: {entry_price:.6f}")
    print(f"   Initial SL: {sl_price:.6f} (ABOVE entry - cuts loss when price rises)")
    print(f"   BE Trigger: {be_trigger:.6f} (BELOW entry - profit threshold)")
    print(f"   BE SL: {be_sl:.6f} ({'BELOW' if side=='SHORT' else 'ABOVE'} entry - secures +0.05% profit)")
    print(f"   TS Trigger: {ts_trigger:.6f} (FAR BELOW entry - big profit threshold)")
    
    print(f"   Initial SL: {sl_price:.6f}")
    print(f"   BE Trigger: {be_trigger:.6f}")
    print(f"   BE New SL: {be_sl:.6f}")
    print(f"   TS Trigger: {ts_trigger:.6f}")
    print()
    
    # ===== LOAD CANDLE DATA =====
    print("📈 LOADING CANDLE DATA:")
    try:
        candles = pd.read_csv("data chart full info.csv")
        candles['time'] = pd.to_datetime(candles['time'])
        
        # Find trade period
        entry_time_dt = pd.to_datetime(entry_time).tz_localize(candles['time'].dt.tz)
        exit_time_dt = pd.to_datetime(exit_time).tz_localize(candles['time'].dt.tz)
        
        entry_idx = abs(candles['time'] - entry_time_dt).idxmin()
        exit_idx = abs(candles['time'] - exit_time_dt).idxmin()
        
        trade_candles = candles.iloc[entry_idx:exit_idx+1].copy()
        
        print(f"   Period: {len(trade_candles)} candles")
        print(f"   From: {trade_candles.iloc[0]['time']}")
        print(f"   To: {trade_candles.iloc[-1]['time']}")
        
        actual_min = trade_candles['low'].min()
        actual_max = trade_candles['high'].max()
        print(f"   Actual Min: {actual_min:.6f}")
        print(f"   Actual Max: {actual_max:.6f}")
        print()
        
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return
    
    # ===== STEP-BY-STEP SIMULATION =====
    print("🔄 STEP-BY-STEP SIMULATION:")
    print("-" * 60)
    
    # Initialize state
    be_reached = False
    ts_reached = False
    trailing_active = False
    current_sl = sl_price
    trailing_level = 0
    max_favorable_price = entry_price
    exit_triggered = False
    final_exit_price = None
    final_exit_time = None
    exit_reason = ""
    
    print("🎬 CANDLE-BY-CANDLE ANALYSIS:")
    
    for i, (idx, candle) in enumerate(trade_candles.iterrows()):
        time = candle['time']
        high = candle['high']
        low = candle['low']
        
        print(f"\n📊 Candle {i+1:2d} @ {time}")
        print(f"   OHLC: {candle['open']:.6f} | {high:.6f} | {low:.6f} | {candle['close']:.6f}")
        
        # Track max favorable movement (for SHORT, lower is better)
        if low < max_favorable_price:
            max_favorable_price = low
            current_profit = (entry_price - low) / entry_price * 100
            print(f"   💰 New Best Price: {low:.6f} (Profit: {current_profit:.2f}%)")
        
        # Check SL hit first (most important)
        if high >= current_sl:
            exit_triggered = True
            final_exit_price = current_sl
            final_exit_time = time
            exit_reason = "SL_HIT"
            final_profit = (entry_price - final_exit_price) / entry_price * 100
            print(f"   🚨 STOP LOSS HIT!")
            print(f"      High: {high:.6f} >= SL: {current_sl:.6f}")
            print(f"      Exit Price: {final_exit_price:.6f}")
            print(f"      Final Profit: {final_profit:.2f}%")
            break
        
        # Check BE trigger
        if not be_reached and low <= be_trigger:
            be_reached = True
            trailing_active = True
            current_sl = be_sl
            print(f"   ✅ BREAKEVEN TRIGGERED!")
            print(f"      Low: {low:.6f} <= BE Trigger: {be_trigger:.6f}")
            print(f"      New SL: {current_sl:.6f}")
        
        # Check TS trigger
        if not ts_reached and low <= ts_trigger:
            ts_reached = True
            trailing_active = True
            print(f"   ✅ TRAILING STOP TRIGGERED!")
            print(f"      Low: {low:.6f} <= TS Trigger: {ts_trigger:.6f}")
        
        # Update trailing stop if active - 🔧 FIXED: ONLY when TS triggered
        if trailing_active and ts_reached and current_profit > ts_trig_pct:
            # Only do trailing when TS actually triggered
            steps = int((current_profit - ts_trig_pct) / ts_step_pct)
            if steps > trailing_level:
                trailing_level = steps
                new_distance = ts_trig_pct + (steps * ts_step_pct)
                
                # Calculate new trailing SL
                if side == 'SHORT':
                    new_sl = entry_price * (1 - new_distance / 100)  # Move down for SHORT to lock profit
                else:
                    new_sl = entry_price * (1 + new_distance / 100)  # Move up for LONG to lock profit
                
                # Update SL if beneficial
                if (side == 'SHORT' and new_sl > current_sl) or (side == 'LONG' and new_sl < current_sl):
                    old_sl = current_sl
                    current_sl = new_sl
                    print(f"   📈 TRAILING UPDATE!")
                    print(f"      Steps: {steps} | Distance: {new_distance:.2f}%")
                    print(f"      Old SL: {old_sl:.6f} -> New SL: {current_sl:.6f}")
        
        # � SIMPLIFIED: When BE triggered but TS not, just keep BE SL
        elif be_reached and not ts_reached:
            # No trailing, just keep BE protection
            pass
    
    # If no SL hit, use best available price
    if not exit_triggered:
        final_exit_price = max_favorable_price
        final_exit_time = trade_candles.iloc[-1]['time']
        exit_reason = "TIME_EXIT"
        final_profit = (entry_price - final_exit_price) / entry_price * 100
        
        print(f"\n⏰ TIME EXIT (No SL Hit):")
        print(f"   Best Price: {final_exit_price:.6f}")
        print(f"   Exit Time: {final_exit_time}")
        print(f"   Final Profit: {final_profit:.2f}%")
    
    # ===== FINAL COMPARISON =====
    print(f"\n🎯 FINAL RESULTS COMPARISON:")
    print("=" * 60)
    print(f"📊 SIMULATION WITH NEW PARAMETERS:")
    print(f"   Parameters: SL={sl_pct}% BE={be_pct}% TS={ts_trig_pct}%/{ts_step_pct}%")
    print(f"   Exit Price: {final_exit_price:.6f}")
    print(f"   Exit Time: {final_exit_time}")
    print(f"   Exit Reason: {exit_reason}")
    print(f"   Final Profit: {final_profit:.2f}%")
    print(f"   BE Reached: {be_reached}")
    print(f"   TS Reached: {ts_reached}")
    print(f"   Trailing Level: {trailing_level}")
    
    print(f"\n📊 ORIGINAL TOOL RESULT:")
    print(f"   Exit Price: {original_exit:.6f}")
    print(f"   Profit: {original_profit:.2f}%")
    
    print(f"\n🔍 COMPARISON ANALYSIS:")
    price_diff = abs(final_exit_price - original_exit)
    profit_diff = abs(final_profit - original_profit)
    
    print(f"   Price Difference: {price_diff:.6f}")
    print(f"   Profit Difference: {profit_diff:.2f}%")
    
    # Reality validation
    max_possible_profit = (entry_price - actual_min) / entry_price * 100
    print(f"   Max Possible Profit: {max_possible_profit:.2f}%")
    
    # Conclusions
    print(f"\n💡 CONCLUSIONS:")
    if final_profit <= max_possible_profit + 0.01:
        print(f"   ✅ REALISTIC: Simulation result is achievable")
    else:
        print(f"   🚨 UNREALISTIC: Simulation exceeds max possible")
    
    if original_profit > max_possible_profit + 0.5:
        print(f"   🚨 ORIGINAL IS FANTASY: {original_profit:.2f}% > {max_possible_profit:.2f}% max")
    else:
        print(f"   ✅ Original might be realistic")
    
    if profit_diff < 1.0:
        print(f"   ✅ CLOSE MATCH: New params produce similar results")
    else:
        print(f"   ⚠️ SIGNIFICANT DIFFERENCE: {profit_diff:.2f}% gap")
    
    print(f"\n🎯 VERDICT:")
    if final_profit <= max_possible_profit and final_exit_price >= actual_min:
        print(f"   ✅ NEW SIMULATION: REALISTIC and ACHIEVABLE")
    else:
        print(f"   🚨 NEW SIMULATION: Has issues")
    
    if original_profit > max_possible_profit + 1.0:
        print(f"   🚨 ORIGINAL RESULT: CONFIRMED FANTASY")
    else:
        print(f"   ✅ ORIGINAL RESULT: Might be valid")

if __name__ == '__main__':
    simulate_trade_139_with_new_params()
