#!/usr/bin/env python3
"""
🎯 MANUAL TEST - Test trực tiếp logic trailing stop đã sửa
"""

def test_manual_trailing_logic():
    """Test manual logic trailing stop đã sửa"""
    
    print("🎯 MANUAL TEST TRAILING STOP LOGIC")
    print("=" * 50)
    
    # Parameters
    entry_price = 0.009937
    be_pct = 1.76
    ts_trig_pct = 7.12
    ts_step_pct = 0.26
    side = 'SHORT'
    
    print(f"📊 PARAMETERS:")
    print(f"   Entry: {entry_price:.6f}")
    print(f"   BE: {be_pct:.2f}%")
    print(f"   TS Trigger: {ts_trig_pct:.2f}%")
    print(f"   TS Step: {ts_step_pct:.2f}%")
    print(f"   Side: {side}")
    
    # Calculate trigger levels
    be_trigger = entry_price * (1 - be_pct/100)
    ts_trigger = entry_price * (1 - ts_trig_pct/100)
    
    print(f"\n🎯 TRIGGER LEVELS:")
    print(f"   BE Trigger: {be_trigger:.6f}")
    print(f"   TS Trigger: {ts_trigger:.6f}")
    
    # Simulate current price at 5.06% profit (actual max)
    current_price = 0.009434
    profit_pct = (entry_price - current_price) / entry_price * 100
    
    print(f"\n📈 CURRENT STATE:")
    print(f"   Current Price: {current_price:.6f}")
    print(f"   Current Profit: {profit_pct:.2f}%")
    
    # Check which triggers activated
    BE_reached = profit_pct >= be_pct
    TS_reached = profit_pct >= ts_trig_pct
    
    print(f"\n🔄 TRIGGER STATUS:")
    print(f"   BE Reached: {BE_reached} ({profit_pct:.2f}% >= {be_pct:.2f}%)")
    print(f"   TS Reached: {TS_reached} ({profit_pct:.2f}% >= {ts_trig_pct:.2f}%)")
    
    # Calculate steps and trailing SL
    if BE_reached:
        steps = int((profit_pct - be_pct) / ts_step_pct)
        print(f"\n⚙️ TRAILING CALCULATION (BE MODE):")
        print(f"   Steps: int(({profit_pct:.2f}% - {be_pct:.2f}%) / {ts_step_pct:.2f}%) = {steps}")
        
        # 🔧 FIXED LOGIC: Use BE for BE trailing
        if TS_reached:
            base_pct = ts_trig_pct
            mode = "TS"
        else:
            base_pct = be_pct  # ✅ Fixed: Use BE not TS_TRIG
            mode = "BE"
            
        trailing_distance = base_pct + (steps * ts_step_pct)
        trailing_sl = entry_price * (1 - trailing_distance / 100)
        
        print(f"   Mode: {mode} Trailing")
        print(f"   Base: {base_pct:.2f}%")
        print(f"   Distance: {base_pct:.2f}% + ({steps} * {ts_step_pct:.2f}%) = {trailing_distance:.2f}%")
        print(f"   Trailing SL: {entry_price:.6f} * (1 - {trailing_distance:.2f}/100) = {trailing_sl:.6f}")
        
        # Compare với old buggy logic
        old_distance = ts_trig_pct + (steps * ts_step_pct)
        old_sl = entry_price * (1 - old_distance / 100)
        
        print(f"\n🚨 SO SÁNH VỚI BUG CŨ:")
        print(f"   Bug Distance: {ts_trig_pct:.2f}% + ({steps} * {ts_step_pct:.2f}%) = {old_distance:.2f}%")
        print(f"   Bug SL: {entry_price:.6f} * (1 - {old_distance:.2f}/100) = {old_sl:.6f}")
        
        # Reality check
        actual_min = 0.009434
        print(f"\n🔍 REALITY CHECK:")
        print(f"   Actual Min: {actual_min:.6f}")
        print(f"   Fixed SL reachable: {trailing_sl >= actual_min} ({trailing_sl:.6f} >= {actual_min:.6f})")
        print(f"   Bug SL reachable: {old_sl >= actual_min} ({old_sl:.6f} >= {actual_min:.6f})")
        
        # Final profit calculation
        final_profit = (entry_price - trailing_sl) / entry_price * 100
        bug_profit = (entry_price - old_sl) / entry_price * 100
        
        print(f"\n📊 FINAL RESULTS:")
        print(f"   ✅ Fixed PnL: {final_profit:.2f}%")
        print(f"   🚨 Bug PnL: {bug_profit:.2f}%")
        print(f"   📏 Difference: {abs(final_profit - bug_profit):.2f}%")
        
        if trailing_sl >= actual_min and old_sl < actual_min:
            print(f"\n🎉 BUG SUCCESSFULLY FIXED!")
            print(f"   Fixed version creates reachable exit prices")
            print(f"   Bug version created fantasy exits")

if __name__ == '__main__':
    test_manual_trailing_logic()
