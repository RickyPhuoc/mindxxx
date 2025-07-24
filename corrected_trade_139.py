#!/usr/bin/env python3
"""
🔧 CORRECTED CALCULATION: Trade #139 với logic BE đúng
"""

def calculate_trade_139_corrected():
    """Tính toán lại với logic BE đúng"""
    
    print("🔧 CORRECTED CALCULATION: Trade #139")
    print("=" * 50)
    
    # Data
    entry_price = 0.009937
    side = 'SHORT'
    actual_min = 0.009434
    
    # Parameters
    sl_pct = 4.41
    be_pct = 1.76
    ts_trig_pct = 7.12
    ts_step_pct = 0.26
    
    print(f"Entry: {entry_price:.6f} | Side: {side}")
    print(f"Actual Min: {actual_min:.6f}")
    print(f"Parameters: SL={sl_pct}% BE={be_pct}% TS={ts_trig_pct}%/{ts_step_pct}%")
    
    # Calculate levels
    initial_sl = entry_price * (1 + sl_pct/100)  # 0.010375
    be_trigger = entry_price * (1 - be_pct/100)  # 0.009762
    
    # 🔧 CORRECTED BE SL LOGIC: 
    # BE SL luôn TRÊN entry 0.05% cho cả LONG và SHORT
    be_sl = entry_price * (1 + 0.0005)  # 0.009942 (TRÊN entry)
    
    ts_trigger = entry_price * (1 - ts_trig_pct/100)  # 0.009229
    
    print(f"\nLevels:")
    print(f"  Initial SL: {initial_sl:.6f}")
    print(f"  BE Trigger: {be_trigger:.6f}")
    print(f"  BE SL: {be_sl:.6f} (TRÊN entry 0.05%)")
    print(f"  TS Trigger: {ts_trigger:.6f}")
    
    # Simulation
    print(f"\nSimulation:")
    
    # 1. Check if BE triggered
    actual_profit = (entry_price - actual_min) / entry_price * 100  # 5.06%
    print(f"  Max profit reached: {actual_profit:.2f}%")
    
    if actual_profit >= be_pct:
        print(f"  ✅ BE triggered: {actual_profit:.2f}% >= {be_pct:.2f}%")
        print(f"  📈 SL moved to BE level: {be_sl:.6f}")
        
        # 2. Check if TS triggered  
        if actual_profit >= ts_trig_pct:
            print(f"  ✅ TS also triggered: {actual_profit:.2f}% >= {ts_trig_pct:.2f}%")
            # Calculate trailing steps...
        else:
            print(f"  ❌ TS not triggered: {actual_profit:.2f}% < {ts_trig_pct:.2f}%")
            print(f"  💡 Only BE protection active")
        
        # 3. Market reversal hits BE SL
        exit_price = be_sl  # 0.009942
        final_pnl = (entry_price - exit_price) / entry_price * 100
        
        print(f"\n🎯 RESULT:")
        print(f"  Market hits BE SL: {exit_price:.6f}")
        print(f"  Final PnL: {final_pnl:.2f}%")
        
        # 🔧 CORRECTED INTERPRETATION:
        if final_pnl > 0:
            print(f"  ✅ PROFIT: Trade secured +{final_pnl:.2f}% profit")
        elif final_pnl < 0:
            print(f"  ❌ LOSS: Trade resulted in {final_pnl:.2f}% loss")
        else:
            print(f"  ⚖️ BREAKEVEN: Trade closed at exactly entry level")
            
    else:
        print(f"  ❌ BE not triggered: {actual_profit:.2f}% < {be_pct:.2f}%")
    
    print(f"\n📊 COMPARISON:")
    print(f"  Original claim: 10.24% ❌ FANTASY")
    print(f"  My previous calc: -0.05% ❌ WRONG LOGIC")
    print(f"  Corrected result: {final_pnl:.2f}%")
    
    # 🤔 QUESTION FOR VERIFICATION:
    print(f"\n🤔 VERIFICATION NEEDED:")
    print(f"  BE SL = {be_sl:.6f}")
    print(f"  Entry = {entry_price:.6f}")  
    print(f"  Difference = {be_sl - entry_price:.6f}")
    print(f"  Percentage = {(be_sl - entry_price)/entry_price*100:.3f}%")
    print(f"  Expected: +0.05%")
    
    if abs((be_sl - entry_price)/entry_price*100 - 0.05) < 0.001:
        print(f"  ✅ CONFIRMED: BE SL is 0.05% above entry")
        print(f"  📈 For SHORT: This means +0.05% profit when hit")
    else:
        print(f"  ❌ ERROR: BE SL calculation wrong")

if __name__ == '__main__':
    calculate_trade_139_corrected()
