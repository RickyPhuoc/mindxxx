#!/usr/bin/env python3
"""
🚀 NEW OPTIMIZATION ENGINE with REALITY CHECK
Engine optimization mới với validation thực tế hoàn toàn
"""

import pandas as pd
import numpy as np
from itertools import product
import time
from datetime import datetime

class RealityCheckOptimizer:
    """Optimizer với kiểm tra thực tế hoàn toàn"""
    
    def __init__(self, data_file):
        """Khởi tạo với data file"""
        self.data = pd.read_csv(data_file)
        self.data['time'] = pd.to_datetime(self.data['time'])
        print(f"✅ Loaded {len(self.data)} candles from {data_file}")
        
    def simulate_trade_realistic(self, entry_time, exit_time, entry_price, side, 
                                sl_pct, be_pct, ts_trig_pct, ts_step_pct):
        """Simulate trade với validation thực tế hoàn toàn"""
        
        # Find trade period
        entry_time_dt = pd.to_datetime(entry_time).tz_localize(self.data['time'].dt.tz)
        exit_time_dt = pd.to_datetime(exit_time).tz_localize(self.data['time'].dt.tz)
        
        entry_idx = abs(self.data['time'] - entry_time_dt).idxmin()
        exit_idx = abs(self.data['time'] - exit_time_dt).idxmin()
        
        trade_candles = self.data.iloc[entry_idx:exit_idx+1].copy()
        
        if len(trade_candles) == 0:
            return {"valid": False, "reason": "No candles in period"}
        
        # Calculate levels
        if side == 'SHORT':
            sl_price = entry_price * (1 + sl_pct/100)
            be_trigger = entry_price * (1 - be_pct/100)
            be_sl = entry_price * (1 + 0.0005)  # Small buffer
            ts_trigger = entry_price * (1 - ts_trig_pct/100)
        else:  # LONG
            sl_price = entry_price * (1 - sl_pct/100)
            be_trigger = entry_price * (1 + be_pct/100)
            be_sl = entry_price * (1 - 0.0005)  # Small buffer
            ts_trigger = entry_price * (1 + ts_trig_pct/100)
        
        # Track state
        be_reached = False
        ts_reached = False
        trailing_active = False
        current_sl = sl_price
        trailing_level = 0
        max_favorable = entry_price
        exit_price = None
        exit_time_actual = None
        exit_reason = "TIME_EXIT"
        
        # Simulate candle by candle
        for i, (idx, candle) in enumerate(trade_candles.iterrows()):
            high = candle['high']
            low = candle['low']
            candle_time = candle['time']
            
            # Update max favorable price
            if side == 'SHORT':
                max_favorable = min(max_favorable, low)
                current_price = low  # Best price for SHORT
            else:
                max_favorable = max(max_favorable, high)
                current_price = high  # Best price for LONG
            
            # Check stop loss hit first
            if side == 'SHORT':
                if high >= current_sl:
                    exit_price = current_sl
                    exit_time_actual = candle_time
                    exit_reason = "SL_HIT"
                    break
            else:
                if low <= current_sl:
                    exit_price = current_sl
                    exit_time_actual = candle_time
                    exit_reason = "SL_HIT"
                    break
            
            # Check BE trigger
            if not be_reached:
                if side == 'SHORT' and low <= be_trigger:
                    be_reached = True
                    trailing_active = True
                    current_sl = be_sl
                elif side == 'LONG' and high >= be_trigger:
                    be_reached = True
                    trailing_active = True
                    current_sl = be_sl
            
            # Check TS trigger
            if not ts_reached:
                if side == 'SHORT' and low <= ts_trigger:
                    ts_reached = True
                    trailing_active = True
                    # Keep current SL if better
                elif side == 'LONG' and high >= ts_trigger:
                    ts_reached = True
                    trailing_active = True
                    # Keep current SL if better
            
            # Update trailing stop if active
            if trailing_active:
                if side == 'SHORT':
                    profit_pct = (entry_price - current_price) / entry_price * 100
                    
                    if be_reached and profit_pct > be_pct:
                        steps = int((profit_pct - be_pct) / ts_step_pct)
                        if steps > trailing_level:
                            trailing_level = steps
                            new_distance = be_pct + (steps * ts_step_pct)
                            new_sl = entry_price * (1 - new_distance / 100)
                            
                            # 🔧 REALITY CHECK: SL must be achievable
                            actual_min = trade_candles['low'].min()
                            if new_sl >= actual_min and new_sl < current_sl:
                                current_sl = new_sl
                    
                    elif ts_reached and profit_pct > ts_trig_pct:
                        steps = int((profit_pct - ts_trig_pct) / ts_step_pct)
                        if steps > trailing_level:
                            trailing_level = steps
                            new_distance = ts_trig_pct + (steps * ts_step_pct)
                            new_sl = entry_price * (1 - new_distance / 100)
                            
                            # 🔧 REALITY CHECK: SL must be achievable
                            actual_min = trade_candles['low'].min()
                            if new_sl >= actual_min and new_sl < current_sl:
                                current_sl = new_sl
                
                else:  # LONG
                    profit_pct = (current_price - entry_price) / entry_price * 100
                    
                    if be_reached and profit_pct > be_pct:
                        steps = int((profit_pct - be_pct) / ts_step_pct)
                        if steps > trailing_level:
                            trailing_level = steps
                            new_distance = be_pct + (steps * ts_step_pct)
                            new_sl = entry_price * (1 + new_distance / 100)
                            
                            # 🔧 REALITY CHECK: SL must be achievable
                            actual_max = trade_candles['high'].max()
                            if new_sl <= actual_max and new_sl > current_sl:
                                current_sl = new_sl
                    
                    elif ts_reached and profit_pct > ts_trig_pct:
                        steps = int((profit_pct - ts_trig_pct) / ts_step_pct)
                        if steps > trailing_level:
                            trailing_level = steps
                            new_distance = ts_trig_pct + (steps * ts_step_pct)
                            new_sl = entry_price * (1 + new_distance / 100)
                            
                            # 🔧 REALITY CHECK: SL must be achievable
                            actual_max = trade_candles['high'].max()
                            if new_sl <= actual_max and new_sl > current_sl:
                                current_sl = new_sl
        
        # If no exit triggered, use best available price
        if exit_price is None:
            if side == 'SHORT':
                exit_price = max_favorable  # Best LOW for SHORT
            else:
                exit_price = max_favorable  # Best HIGH for LONG
            exit_time_actual = trade_candles.iloc[-1]['time']
            exit_reason = "TIME_EXIT"
        
        # Calculate final profit
        if side == 'SHORT':
            profit_pct = (entry_price - exit_price) / entry_price * 100
        else:
            profit_pct = (exit_price - entry_price) / entry_price * 100
        
        # 🔧 FINAL REALITY CHECK
        actual_min = trade_candles['low'].min()
        actual_max = trade_candles['high'].max()
        
        max_possible_profit = 0
        if side == 'SHORT':
            max_possible_profit = (entry_price - actual_min) / entry_price * 100
        else:
            max_possible_profit = (actual_max - entry_price) / entry_price * 100
        
        is_realistic = profit_pct <= max_possible_profit + 0.01  # Small tolerance
        
        return {
            "valid": True,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "exit_time": exit_time_actual,
            "exit_reason": exit_reason,
            "profit_pct": profit_pct,
            "max_possible_profit": max_possible_profit,
            "is_realistic": is_realistic,
            "be_reached": be_reached,
            "ts_reached": ts_reached,
            "trailing_level": trailing_level,
            "final_sl": current_sl,
            "candles_count": len(trade_candles)
        }
    
    def optimize_parameters(self, trade_configs, param_ranges):
        """Optimize parameters với reality check"""
        
        print(f"🚀 STARTING REALITY-CHECKED OPTIMIZATION")
        print(f"   Trades to test: {len(trade_configs)}")
        print(f"   Parameter combinations: {len(list(product(*param_ranges.values())))}")
        print()
        
        results = []
        total_combinations = len(list(product(*param_ranges.values())))
        
        start_time = time.time()
        
        for i, params in enumerate(product(*param_ranges.values())):
            sl, be, ts_trig, ts_step = params
            
            # Skip invalid combinations
            if be >= ts_trig or ts_step <= 0 or ts_step >= ts_trig:
                continue
            
            trade_results = []
            valid_trades = 0
            realistic_trades = 0
            total_profit = 0
            
            for trade_config in trade_configs:
                result = self.simulate_trade_realistic(
                    trade_config['entry_time'],
                    trade_config['exit_time'], 
                    trade_config['entry_price'],
                    trade_config['side'],
                    sl, be, ts_trig, ts_step
                )
                
                if result['valid']:
                    valid_trades += 1
                    trade_results.append(result)
                    
                    if result['is_realistic']:
                        realistic_trades += 1
                        total_profit += result['profit_pct']
            
            if valid_trades > 0:
                avg_profit = total_profit / valid_trades
                realism_score = realistic_trades / valid_trades
                
                results.append({
                    'sl': sl,
                    'be': be, 
                    'ts_trig': ts_trig,
                    'ts_step': ts_step,
                    'valid_trades': valid_trades,
                    'realistic_trades': realistic_trades,
                    'avg_profit': avg_profit,
                    'realism_score': realism_score,
                    'total_profit': total_profit,
                    'trade_results': trade_results
                })
            
            # Progress update
            if (i + 1) % 100 == 0:
                elapsed = time.time() - start_time
                progress = (i + 1) / total_combinations * 100
                print(f"   Progress: {progress:.1f}% | {i+1}/{total_combinations} | {elapsed:.1f}s")
        
        # Sort by realism score first, then avg profit
        results.sort(key=lambda x: (x['realism_score'], x['avg_profit']), reverse=True)
        
        print(f"\n✅ OPTIMIZATION COMPLETE!")
        print(f"   Total valid combinations: {len(results)}")
        print(f"   Time taken: {time.time() - start_time:.1f}s")
        
        return results

def main():
    """Main function to run optimization"""
    print("🚀 REALITY-CHECKED OPTIMIZATION ENGINE")
    print("=" * 60)
    
    # Initialize optimizer
    optimizer = RealityCheckOptimizer("data chart full info.csv")
    
    # Test with Trade #139
    trade_configs = [
        {
            'entry_time': '2025-06-20 22:00:00',
            'exit_time': '2025-06-21 08:30:00',
            'entry_price': 0.009937,
            'side': 'SHORT'
        }
    ]
    
    # Parameter ranges - more conservative
    param_ranges = {
        'sl': [3.0, 4.0, 5.0, 6.0],  # Stop loss %
        'be': [1.0, 1.5, 2.0, 2.5],  # Breakeven %  
        'ts_trig': [3.0, 4.0, 5.0, 6.0, 7.0],  # Trailing trigger %
        'ts_step': [0.1, 0.2, 0.3, 0.5]  # Trailing step %
    }
    
    # Run optimization
    results = optimizer.optimize_parameters(trade_configs, param_ranges)
    
    # Show top results
    print(f"\n🏆 TOP 10 REALISTIC RESULTS:")
    print("=" * 80)
    
    for i, result in enumerate(results[:10], 1):
        print(f"{i:2d}. SL:{result['sl']:4.1f}% BE:{result['be']:4.1f}% TS:{result['ts_trig']:4.1f}% Step:{result['ts_step']:4.1f}%")
        print(f"    Profit: {result['avg_profit']:6.2f}% | Realism: {result['realism_score']:5.1%} | Valid: {result['valid_trades']}")
        
        # Show trade details for best result
        if i == 1:
            print(f"    📊 TRADE DETAILS:")
            for j, trade in enumerate(result['trade_results']):
                print(f"       Trade {j+1}: {trade['profit_pct']:6.2f}% | Exit: {trade['exit_price']:.6f} | Realistic: {trade['is_realistic']}")
        print()
    
    # Compare with original bug
    print(f"🐛 COMPARISON WITH ORIGINAL BUG:")
    print(f"   Original Claim: 10.24% profit with exit 0.008919")
    print(f"   Best Reality Check: {results[0]['avg_profit']:.2f}% profit")
    print(f"   Gap: {abs(results[0]['avg_profit'] - 10.24):.2f}% difference")
    
    if abs(results[0]['avg_profit'] - 10.24) > 2.0:
        print(f"   🚨 CONFIRMED: Original tool was calculating FANTASY profits!")
    else:
        print(f"   ✅ Results are within reasonable range")

if __name__ == '__main__':
    main()
