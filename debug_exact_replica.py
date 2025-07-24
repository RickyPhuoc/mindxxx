#!/usr/bin/env python3
"""
🔍 EXACT CODE REPLICA: Debug Trade #139
Copy chính xác logic từ backtest_gridsearch_slbe_ts_Version3.py
"""

import pandas as pd
import numpy as np

def find_candle_idx(target_dt, df_candle):
    """Tìm index của candle gần nhất với thời gian target"""
    if df_candle.empty:
        return -1
    
    # Convert target to datetime if needed
    if isinstance(target_dt, str):
        target_dt = pd.to_datetime(target_dt)
    
    # Ensure timezone consistency
    if hasattr(df_candle['time'].iloc[0], 'tz') and df_candle['time'].iloc[0].tz is not None:
        if target_dt.tz is None:
            target_dt = target_dt.tz_localize(df_candle['time'].iloc[0].tz)
    
    # Find closest match
    time_diffs = abs(df_candle['time'] - target_dt)
    return time_diffs.idxmin()

def simulate_trade_exact_copy(pair, df_candle, sl, be, ts_trig, ts_step):
    """Copy chính xác từ code gốc"""
    log = []
    
    print(f"🔍 EXACT SIMULATION Trade #{pair['num']}:")
    print(f"   Entry DT: {pair['entryDt']}")
    print(f"   Exit DT: {pair['exitDt']}")
    
    entryIdx = find_candle_idx(pair['entryDt'], df_candle)
    exitIdx = find_candle_idx(pair['exitDt'], df_candle)
    
    print(f"   Entry Index: {entryIdx}")
    print(f"   Exit Index: {exitIdx}")
    
    if entryIdx==-1 or exitIdx==-1 or exitIdx <= entryIdx:
        log.append(f"TradeNum {pair['num']}: Không khớp nến hoặc exit <= entry")
        return None, log
        
    prices = df_candle.iloc[entryIdx:exitIdx+1].copy()
    print(f"   Price candles: {len(prices)}")
    
    # EXACT COPY FROM ORIGINAL CODE
    entryPrice = prices.iloc[0]['open']
    exitPrice = prices.iloc[-1]['close']
    
    side = pair['side']
    slPrice = entryPrice*(1-sl/100) if side=='LONG' else entryPrice*(1+sl/100)
    beTrigPrice = entryPrice*(1+be/100) if side=='LONG' else entryPrice*(1-be/100)
    beSLPrice = entryPrice*(1-0.0005) if side=='LONG' else entryPrice*(1+0.0005)
    tsTrigPrice = entryPrice*(1+ts_trig/100) if side=='LONG' else entryPrice*(1-ts_trig/100)

    print(f"   Entry Price: {entryPrice:.6f}")
    print(f"   Side: {side}")
    print(f"   SL Price: {slPrice:.6f}")
    print(f"   BE Trig: {beTrigPrice:.6f}")
    print(f"   BE SL: {beSLPrice:.6f}")
    print(f"   TS Trig: {tsTrigPrice:.6f}")

    BE_reached = False
    TS_reached = False
    trailingActive = False
    trailingLevel = 0
    trailingSL = slPrice
    maxTrailingSL = slPrice
    finalExitIdx = exitIdx
    finalExitPrice = exitPrice
    finalExitDt = prices.iloc[-1]['time']
    exitType = "EXIT"
    done = False

    print(f"\n📈 CANDLE-BY-CANDLE SIMULATION:")
    print("-" * 60)
    
    for i in range(1, len(prices)):
        candle = prices.iloc[i]
        high = candle['high']
        low = candle['low']
        nowDt = candle['time']
        
        print(f"Candle {i:2d}: {nowDt}")
        print(f"  OHLC: {candle['open']:.6f} {high:.6f} {low:.6f} {candle['close']:.6f}")

        # EXACT COPY: Check initial SL hit
        if not BE_reached and not TS_reached:
            if (side=='LONG' and low<=slPrice) or (side=='SHORT' and high>=slPrice):
                finalExitIdx = entryIdx+i
                finalExitPrice = slPrice
                finalExitDt = nowDt
                exitType = "SL"
                done=True
                print(f"  🛑 INITIAL SL HIT! Exit: {finalExitPrice:.6f}")
                break

        # EXACT COPY: Check BE trigger
        if not BE_reached:
            if (side=='LONG' and high>=beTrigPrice) or (side=='SHORT' and low<=beTrigPrice):
                BE_reached = True
                trailingActive = True
                trailingLevel = 0
                trailingSL = beSLPrice
                maxTrailingSL = beSLPrice
                print(f"  ✅ BE TRIGGERED! Low {low:.6f} <= {beTrigPrice:.6f}")
                print(f"     New trailing SL: {trailingSL:.6f}")

        # EXACT COPY: Check TS trigger
        if not TS_reached:
            if (side=='LONG' and high>=tsTrigPrice) or (side=='SHORT' and low<=tsTrigPrice):
                TS_reached = True
                trailingActive = True
                trailingSL = max(trailingSL, slPrice)
                maxTrailingSL = trailingSL
                print(f"  🎯 TS TRIGGERED! Low {low:.6f} <= {tsTrigPrice:.6f}")
                print(f"     New trailing SL: {trailingSL:.6f}")

        # EXACT COPY: Trailing logic
        if trailingActive:
            priceNow = high if side=='LONG' else low
            fromEntry = (priceNow-entryPrice) if side=='LONG' else (entryPrice-priceNow)
            fromEntryPct = fromEntry/entryPrice*100
            
            stepCount = 0
            if TS_reached:
                stepCount = int((fromEntryPct-ts_trig)/ts_step)
            if BE_reached:
                fromBETrigPct = (priceNow-entryPrice)/entryPrice*100 if side=='LONG' else (entryPrice-priceNow)/entryPrice*100
                if fromBETrigPct>=be:
                    stepCount = int((fromBETrigPct-be)/ts_step)
                else:
                    stepCount = 0
                    
            print(f"  📊 Trailing: priceNow={priceNow:.6f}, fromEntry={fromEntryPct:.2f}%, steps={stepCount}")
            
            if stepCount>trailingLevel:
                trailingLevel = stepCount
                # 🚨 THIS IS THE CRITICAL LINE 🚨
                newTrailingSL = (entryPrice*(1+(ts_trig+trailingLevel*ts_step)/100)) if side=='LONG' else (entryPrice*(1-(ts_trig+trailingLevel*ts_step)/100))
                if BE_reached:
                    if side=='LONG': 
                        newTrailingSL = max(newTrailingSL, beSLPrice)
                    else: 
                        newTrailingSL = min(newTrailingSL, beSLPrice)
                trailingSL = newTrailingSL
                maxTrailingSL = trailingSL
                
                print(f"  🔄 TRAILING UPDATE: Level {trailingLevel}")
                print(f"     Formula: {entryPrice:.6f} * (1 - ({ts_trig:.2f} + {trailingLevel} * {ts_step:.2f})/100)")
                print(f"     Calculation: {entryPrice:.6f} * (1 - {(ts_trig+trailingLevel*ts_step):.2f}/100)")
                print(f"     Result: {entryPrice:.6f} * {(1-(ts_trig+trailingLevel*ts_step)/100):.6f} = {newTrailingSL:.6f}")
                
                if newTrailingSL <= 0.008919:
                    print(f"     🎯 TARGET REACHED! {newTrailingSL:.6f} <= 0.008919")
                    
            # Check trailing SL hit
            if (side=='LONG' and low<=trailingSL) or (side=='SHORT' and high>=trailingSL):
                finalExitIdx = entryIdx+i
                finalExitPrice = trailingSL
                finalExitDt = nowDt
                exitType = "BE SL" if BE_reached and trailingSL==beSLPrice and not TS_reached else "TS SL"
                done=True
                print(f"  🛑 TRAILING SL HIT! Exit: {finalExitPrice:.6f}")
                break
        
        print()

    # Calculate final PnL
    pnl = (finalExitPrice-entryPrice) if side=='LONG' else (entryPrice-finalExitPrice)
    pnlPct = pnl/entryPrice*100 if entryPrice!=0 else 0
    
    print(f"🎯 FINAL RESULTS:")
    print(f"   Final Exit Price: {finalExitPrice:.6f}")
    print(f"   Final PnL: {pnlPct:.2f}%")
    print(f"   Exit Type: {exitType}")
    print(f"   Max Trailing Level: {trailingLevel}")
    
    return {
        'num': pair['num'],
        'side': side,
        'entryPrice': entryPrice,
        'exitPrice': finalExitPrice,
        'pnlPct': pnlPct,
        'exitType': exitType,
        'maxTrailingLevel': trailingLevel
    }, log

def debug_trade_139():
    """Debug Trade #139 với code copy chính xác"""
    print("🔬 EXACT CODE REPLICA DEBUG: Trade #139")
    print("=" * 60)
    
    # Load data
    try:
        candles = pd.read_csv("data chart full info.csv")
        candles['time'] = pd.to_datetime(candles['time'])
        print(f"✅ Loaded {len(candles)} candles")
        
        tradelist = pd.read_csv("tradelist-fullinfo.csv")
        trade_139 = tradelist[tradelist['Trade #'] == 139]
        entry_row = trade_139[trade_139['Type'].str.contains('Entry')].iloc[0]
        exit_row = trade_139[trade_139['Type'].str.contains('Exit')].iloc[0]
        
        print(f"✅ Found Trade #139 data")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Create trade pair object
    pair = {
        'num': 139,
        'side': 'SHORT',
        'entryDt': entry_row['Date/Time'],
        'exitDt': exit_row['Date/Time'],
        'entryPrice': entry_row['Price USDT'],
        'exitPrice': exit_row['Price USDT']
    }
    
    # Optimization parameters  
    sl = 4.41
    be = 1.76
    ts_trig = 7.12
    ts_step = 0.26
    
    print(f"📊 RUNNING EXACT SIMULATION:")
    print(f"   Parameters: SL={sl}%, BE={be}%, TS={ts_trig}%/{ts_step}%")
    print()
    
    # Run simulation
    result, logs = simulate_trade_exact_copy(pair, candles, sl, be, ts_trig, ts_step)
    
    if result:
        print(f"\n🎯 OPTIMIZATION COMPARISON:")
        print(f"   Actual result: {result['pnlPct']:.2f}%")
        print(f"   Claimed result: 10.24%")
        print(f"   Match: {'✅' if abs(result['pnlPct'] - 10.24) < 0.1 else '❌'}")
        
        if result['exitPrice'] <= 0.008919:
            print(f"   🎯 Exit price {result['exitPrice']:.6f} DOES reach target!")
        else:
            print(f"   ❌ Exit price {result['exitPrice']:.6f} does NOT reach 0.008919")

if __name__ == '__main__':
    debug_trade_139()
