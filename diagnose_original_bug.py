#!/usr/bin/env python3
"""
🔧 CHẨN ĐOÁN VÀ SỬA BUG TOOL GỐC
Tìm và sửa lỗi trong logic trailing stop của tool gốc
"""

def analyze_original_bug():
    """Phân tích bug trong tool gốc"""
    
    print("🔧 CHẨN ĐOÁN BUG TOOL GỐC")
    print("=" * 50)
    
    print("📊 TRADE #139 WITH PARAMETERS:")
    entry_price = 0.009937
    be_pct = 1.76  
    ts_trig_pct = 7.12
    ts_step_pct = 0.26
    
    print(f"   Entry: {entry_price:.6f}")
    print(f"   BE: {be_pct:.2f}%")
    print(f"   TS Trigger: {ts_trig_pct:.2f}%") 
    print(f"   TS Step: {ts_step_pct:.2f}%")
    
    # Simulate phát hiện BE trigger
    print(f"\n🎯 WHEN BE TRIGGERED:")
    be_trigger = entry_price * (1 - be_pct/100)
    print(f"   BE Trigger Price: {be_trigger:.6f}")
    
    # Giả sử giá đi xuống 5.06% (actual min)
    current_price = 0.009434
    profit_pct = (entry_price - current_price) / entry_price * 100
    print(f"   Current Price: {current_price:.6f}")
    print(f"   Current Profit: {profit_pct:.2f}%")
    
    # Calculate steps
    steps = int((profit_pct - be_pct) / ts_step_pct)
    print(f"   Steps: int(({profit_pct:.2f}% - {be_pct:.2f}%) / {ts_step_pct:.2f}%) = {steps}")
    
    print(f"\n🚨 BUG TRONG TOOL GỐC:")
    print("   Code gốc tính trailing SL:")
    
    # BUG VERSION (tool gốc)
    bug_formula = f"entryPrice * (1 - (ts_trig + steps * ts_step) / 100)"
    bug_distance = ts_trig_pct + (steps * ts_step_pct)
    bug_sl = entry_price * (1 - bug_distance / 100)
    
    print(f"   🚨 BUG: {bug_formula}")
    print(f"   🚨 Distance: {ts_trig_pct:.2f}% + ({steps} * {ts_step_pct:.2f}%) = {bug_distance:.2f}%")
    print(f"   🚨 Bug SL: {entry_price:.6f} * (1 - {bug_distance:.2f}/100) = {bug_sl:.6f}")
    
    # CORRECT VERSION  
    print(f"\n✅ CÁCH TÍNH ĐÚNG:")
    print("   Khi BE triggered, phải dùng BE làm base:")
    
    correct_formula = f"entryPrice * (1 - (be + steps * ts_step) / 100)"
    correct_distance = be_pct + (steps * ts_step_pct)
    correct_sl = entry_price * (1 - correct_distance / 100)
    
    print(f"   ✅ CORRECT: {correct_formula}")
    print(f"   ✅ Distance: {be_pct:.2f}% + ({steps} * {ts_step_pct:.2f}%) = {correct_distance:.2f}%")
    print(f"   ✅ Correct SL: {entry_price:.6f} * (1 - {correct_distance:.2f}/100) = {correct_sl:.6f}")
    
    print(f"\n📊 SO SÁNH KẾT QUẢ:")
    bug_profit = (entry_price - bug_sl) / entry_price * 100
    correct_profit = (entry_price - correct_sl) / entry_price * 100
    
    print(f"   🚨 Bug SL: {bug_sl:.6f} → Profit: {bug_profit:.2f}%")
    print(f"   ✅ Correct SL: {correct_sl:.6f} → Profit: {correct_profit:.2f}%")
    print(f"   📏 Difference: {abs(bug_profit - correct_profit):.2f}%")
    
    # Reality check
    actual_min = 0.009434
    print(f"\n🔍 REALITY CHECK:")
    print(f"   Actual Min Price: {actual_min:.6f}")
    print(f"   Bug SL reachable: {bug_sl >= actual_min} ({bug_sl:.6f} >= {actual_min:.6f})")
    print(f"   Correct SL reachable: {correct_sl >= actual_min} ({correct_sl:.6f} >= {actual_min:.6f})")
    
    if bug_sl < actual_min:
        print(f"   🚨 BUG CREATES FANTASY EXIT: Tool claims exit at {bug_sl:.6f} but min was {actual_min:.6f}!")
    
    print(f"\n💡 KẾT LUẬN:")
    print(f"   Tool gốc dùng TS_TRIG để tính BE trailing → tạo ra fantasy profits")
    print(f"   Cần sửa: Dùng BE cho BE trailing, TS_TRIG cho TS trailing")
    print(f"   Original claim 10.24% có thể đến từ bug này!")

if __name__ == '__main__':
    analyze_original_bug()
