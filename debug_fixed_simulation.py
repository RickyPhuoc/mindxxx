#!/usr/bin/env python3
"""
🔧 DEBUG VERSION: Test logic mô phỏng đã sửa cho Trade #139
Kiểm tra xem việc sửa thứ tự candle-by-candle có hoạt động đúng không
"""

import pandas as pd

def debug_simulate_trade_139():
    """Debug simulation Trade #139 với logic đã sửa"""
    
    print("🔧 DEBUG SIMULATION: Trade #139 với logic đã sửa")
    print("=" * 60)
    
    # Load data
    candles = pd.read_csv("data chart full info.csv")
    candles['time'] = pd.to_datetime(candles['time'])
    
    # Trade #139 data
    entry_time = '2025-06-20 22:00:00'
    exit_time = '2025-06-21 08:30:00'
    entry_price = 0.009937
    side = 'SHORT'
    
    # Parameters tối ưu
    sl_pct = 4.41
    be_pct = 1.76  
    ts_trig_pct = 7.12
    ts_step_pct = 0.26
    
    print(f"📊 TRADE INFO:")
    print(f"   Entry: {entry_price:.6f} {side} @ {entry_time}")
    print(f"   Parameters: SL={sl_pct}% BE={be_pct}% TS={ts_trig_pct}%/{ts_step_pct}%")
    print()
    
    # Calculate price levels
    sl_price = entry_price * (1 + sl_pct/100)  # SHORT: SL above entry
    be_trigger = entry_price * (1 - be_pct/100)  # SHORT: BE trigger below entry
    be_sl = entry_price * (1 - 0.0005)  # SHORT: BE SL below entry for +0.05% profit
    ts_trigger = entry_price * (1 - ts_trig_pct/100)  # SHORT: TS trigger below entry
    
    print(f"🎯 CALCULATED LEVELS:")
    print(f"   Initial SL: {sl_price:.6f} (loss protection)")
    print(f"   BE Trigger: {be_trigger:.6f} (profit threshold)")  
    print(f"   BE SL: {be_sl:.6f} (locks +0.05% profit)")
    print(f"   TS Trigger: {ts_trigger:.6f} (big profit threshold)")
    print()
    
    # Get trade candles
    entry_time_dt = pd.to_datetime(entry_time)
    exit_time_dt = pd.to_datetime(exit_time)
    
    # Handle timezone
    if candles['time'].dt.tz is not None:
        if entry_time_dt.tz is None:
            entry_time_dt = entry_time_dt.tz_localize(candles['time'].dt.tz)
        if exit_time_dt.tz is None:
            exit_time_dt = exit_time_dt.tz_localize(candles['time'].dt.tz)
    
    entry_idx = abs(candles['time'] - entry_time_dt).idxmin()
    exit_idx = abs(candles['time'] - exit_time_dt).idxmin()
    
    trade_candles = candles.iloc[entry_idx:exit_idx+1].copy()
    
    print(f"📈 CANDLE DATA:")
    print(f"   Period: {len(trade_candles)} candles")
    print(f"   Actual Min: {trade_candles['low'].min():.6f}")
    print(f"   Actual Max: {trade_candles['high'].max():.6f}")
    print()
    
    # 🔧 SIMULATION WITH FIXED LOGIC
    print("🔄 SIMULATION WITH FIXED CANDLE-BY-CANDLE LOGIC:")
    print("-" * 60)
    
    # Initialize state
    be_reached = False
    ts_reached = False
    trailing_active = False
    current_sl = sl_price  # Start with initial SL
    trailing_level = 0
    exit_triggered = False
    final_exit_price = None
    final_exit_time = None
    exit_reason = ""
    
    for i, (idx, candle) in enumerate(trade_candles.iterrows()):
        if i == 0:  # Skip entry candle
            continue
            
        time = candle['time']
        high = candle['high']
        low = candle['low']
        
        print(f"\n📊 Candle {i:2d} @ {time}")
        print(f"   OHLC: {candle['open']:.6f} | {high:.6f} | {low:.6f} | {candle['close']:.6f}")
        print(f"   Current SL: {current_sl:.6f}")
        
        # 🚨 STEP 1: CHECK SL HIT FIRST with CURRENT SL
        if high >= current_sl:  # SHORT: exit when price goes up to SL
            exit_triggered = True
            final_exit_price = current_sl
            final_exit_time = time
            
            if trailing_active:
                if be_reached and current_sl == be_sl and not ts_reached:
                    exit_reason = "BE_SL_HIT"
                else:
                    exit_reason = "TS_SL_HIT"
            else:
                exit_reason = "INITIAL_SL_HIT"
                
            profit = (entry_price - final_exit_price) / entry_price * 100
            print(f"   🚨 STOP LOSS HIT!")
            print(f"      High: {high:.6f} >= SL: {current_sl:.6f}")
            print(f"      Exit Reason: {exit_reason}")
            print(f"      Final Profit: {profit:.2f}%")
            break
        
        # 🔧 STEP 2: ONLY AFTER confirming no SL hit, check triggers for NEXT candle
        sl_updated = False
        
        # Check BE trigger
        if not be_reached and low <= be_trigger:
            be_reached = True
            trailing_active = True
            print(f"   ✅ BE TRIGGERED!")
            print(f"      Low: {low:.6f} <= BE Trigger: {be_trigger:.6f}")
            print(f"      SL will update to BE SL: {be_sl:.6f} for NEXT candle")
            # Don't update SL immediately - wait for next candle
            
        # Check TS trigger  
        if not ts_reached and low <= ts_trigger:
            ts_reached = True
            trailing_active = True
            print(f"   ✅ TS TRIGGERED!")
            print(f"      Low: {low:.6f} <= TS Trigger: {ts_trigger:.6f}")
            print(f"      Trailing will activate for NEXT candle")
        
        # 🔧 STEP 3: Update SL for NEXT candle (based on triggers from PREVIOUS candles)
        if be_reached and not sl_updated:
            old_sl = current_sl
            current_sl = be_sl
            print(f"   📈 SL UPDATED for next candle:")
            print(f"      {old_sl:.6f} → {current_sl:.6f} (BE protection)")
            sl_updated = True
            
        # For TS trailing (simplified for now)
        if ts_reached and trailing_active:
            current_profit = (entry_price - low) / entry_price * 100
            if current_profit > ts_trig_pct:
                steps = int((current_profit - ts_trig_pct) / ts_step_pct)
                if steps > trailing_level:
                    trailing_level = steps
                    new_distance = ts_trig_pct + (steps * ts_step_pct)
                    new_sl = entry_price * (1 - new_distance / 100)
                    
                    if new_sl > current_sl:  # Only if beneficial for SHORT
                        old_sl = current_sl
                        current_sl = new_sl
                        print(f"   📈 TRAILING UPDATE:")
                        print(f"      Steps: {steps} | Distance: {new_distance:.2f}%")
                        print(f"      {old_sl:.6f} → {current_sl:.6f}")
    
    # Final result
    if not exit_triggered:
        final_exit_price = trade_candles.iloc[-1]['close']
        final_exit_time = trade_candles.iloc[-1]['time']
        exit_reason = "TIME_EXIT"
        profit = (entry_price - final_exit_price) / entry_price * 100
        
        print(f"\n⏰ TIME EXIT:")
        print(f"   Exit Price: {final_exit_price:.6f}")
        print(f"   Final Profit: {profit:.2f}%")
    else:
        profit = (entry_price - final_exit_price) / entry_price * 100
    
    print(f"\n🎯 FINAL RESULT:")
    print("=" * 60)
    print(f"📊 FIXED SIMULATION RESULT:")
    print(f"   Exit Price: {final_exit_price:.6f}")
    print(f"   Exit Time: {final_exit_time}")
    print(f"   Exit Reason: {exit_reason}")
    print(f"   Final Profit: {profit:.2f}%")
    print(f"   BE Reached: {be_reached}")
    print(f"   TS Reached: {ts_reached}")
    
    print(f"\n🔍 COMPARISON:")
    print(f"   Original Tool (BUG): +10.24% @ 0.008919 (FANTASY)")
    print(f"   Fixed Logic: {profit:.2f}% @ {final_exit_price:.6f}")
    print(f"   Independent Sim: +0.05% @ 0.009932")
    
    # Validation
    max_possible = (entry_price - trade_candles['low'].min()) / entry_price * 100
    print(f"   Max Possible: {max_possible:.2f}%")
    
    if abs(profit - 0.05) < 0.01:
        print("   ✅ PERFECT MATCH với independent simulation!")
    elif profit <= max_possible + 0.1:
        print("   ✅ REALISTIC RESULT within possible range")
    else:
        print("   ❌ Still has issues - needs more debugging")

if __name__ == '__main__':
    debug_simulate_trade_139()
