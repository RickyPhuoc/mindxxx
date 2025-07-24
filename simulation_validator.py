#!/usr/bin/env python3
"""
🛡️ VALIDATION SYSTEM: Ngăn chặn sai lầm trong backtest
- Reality check cho tất cả simulation results
- Automated testing cho logic quan trọng  
- Candle-by-candle verification
"""

import pandas as pd
import numpy as np

class SimulationValidator:
    """Hệ thống validation cho simulation results"""
    
    def __init__(self, candle_data):
        self.candles = candle_data
        
    def validate_trade_result(self, entry_price, exit_price, side, entry_time, exit_time, profit_pct):
        """Kiểm tra kết quả trade có thực tế không"""
        
        print(f"🔍 VALIDATING TRADE RESULT:")
        print(f"   Entry: {entry_price:.6f} @ {entry_time}")
        print(f"   Exit: {exit_price:.6f} @ {exit_time}")  
        print(f"   Side: {side}, Profit: {profit_pct:.2f}%")
        
        # Get candles for trade period
        trade_candles = self._get_trade_candles(entry_time, exit_time)
        if trade_candles.empty:
            raise ValueError("❌ Không tìm thấy candles cho trade period")
        
        # 1. Kiểm tra exit price có tồn tại
        if not self._exit_price_exists(exit_price, side, trade_candles):
            min_price = trade_candles['low'].min()
            max_price = trade_candles['high'].max()
            raise ValueError(f"❌ FANTASY EXIT: {exit_price:.6f} không tồn tại trong range [{min_price:.6f}, {max_price:.6f}]")
        
        # 2. Kiểm tra profit có vượt max possible
        max_possible_profit = self._calculate_max_possible_profit(entry_price, side, trade_candles)
        if profit_pct > max_possible_profit + 0.1:  # 0.1% tolerance
            raise ValueError(f"❌ IMPOSSIBLE PROFIT: {profit_pct:.2f}% > Max possible {max_possible_profit:.2f}%")
        
        print(f"   ✅ VALIDATION PASSED")
        print(f"   Max Possible Profit: {max_possible_profit:.2f}%")
        return True
    
    def _get_trade_candles(self, entry_time, exit_time):
        """Lấy candles trong trade period"""
        try:
            entry_dt = pd.to_datetime(entry_time)
            exit_dt = pd.to_datetime(exit_time)
            
            # Handle timezone issues
            if self.candles['time'].dt.tz is not None:
                if entry_dt.tz is None:
                    entry_dt = entry_dt.tz_localize(self.candles['time'].dt.tz)
                if exit_dt.tz is None:
                    exit_dt = exit_dt.tz_localize(self.candles['time'].dt.tz)
            
            # Find closest candles
            entry_idx = abs(self.candles['time'] - entry_dt).idxmin()
            exit_idx = abs(self.candles['time'] - exit_dt).idxmin()
            
            return self.candles.iloc[entry_idx:exit_idx+1]
        except Exception as e:
            print(f"⚠️ Error getting trade candles: {e}")
            return pd.DataFrame()
    
    def _exit_price_exists(self, exit_price, side, candles):
        """Kiểm tra exit price có tồn tại trong candles"""
        min_price = candles['low'].min()
        max_price = candles['high'].max()
        
        return min_price <= exit_price <= max_price
    
    def _calculate_max_possible_profit(self, entry_price, side, candles):
        """Tính max possible profit từ data thực"""
        if side == 'LONG':
            best_exit = candles['high'].max()
            return (best_exit - entry_price) / entry_price * 100
        else:  # SHORT
            best_exit = candles['low'].min()
            return (entry_price - best_exit) / entry_price * 100

class BELogicValidator:
    """Validator cho BE logic"""
    
    @staticmethod
    def test_be_sl_calculation():
        """Test BE SL calculation logic"""
        print("🧪 TESTING BE SL CALCULATION:")
        
        entry_price = 1.0000
        
        # Test LONG
        be_sl_long = BELogicValidator.calculate_be_sl(entry_price, 'LONG')
        expected_long = 1.0005
        assert abs(be_sl_long - expected_long) < 1e-6, f"LONG BE SL sai: {be_sl_long} != {expected_long}"
        profit_long = (be_sl_long - entry_price) / entry_price * 100
        assert abs(profit_long - 0.05) < 0.001, f"LONG profit sai: {profit_long}% != 0.05%"
        
        # Test SHORT
        be_sl_short = BELogicValidator.calculate_be_sl(entry_price, 'SHORT')
        expected_short = 0.9995
        assert abs(be_sl_short - expected_short) < 1e-6, f"SHORT BE SL sai: {be_sl_short} != {expected_short}"
        profit_short = (entry_price - be_sl_short) / entry_price * 100
        assert abs(profit_short - 0.05) < 0.001, f"SHORT profit sai: {profit_short}% != 0.05%"
        
        print(f"   ✅ LONG: Entry {entry_price:.4f} → BE SL {be_sl_long:.4f} → Profit {profit_long:.2f}%")
        print(f"   ✅ SHORT: Entry {entry_price:.4f} → BE SL {be_sl_short:.4f} → Profit {profit_short:.2f}%")
        print("   ✅ BE LOGIC TESTS PASSED")
        
    @staticmethod
    def calculate_be_sl(entry_price, side):
        """Tính BE SL đảm bảo lợi nhuận +0.05%"""
        if side == 'LONG':
            # LONG: BE SL phải CAO HƠN entry để có lãi khi exit
            return entry_price * (1 + 0.0005)  # +0.05% profit
        else:  # SHORT
            # SHORT: BE SL phải THẤP HƠN entry để có lãi khi exit
            return entry_price * (1 - 0.0005)  # +0.05% profit

def validate_tool_result(trade_data, candle_data, result):
    """Validate kết quả từ tool với reality check"""
    
    validator = SimulationValidator(candle_data)
    
    try:
        validator.validate_trade_result(
            entry_price=trade_data['entryPrice'],
            exit_price=result['finalExitPrice'], 
            side=trade_data['side'],
            entry_time=trade_data['entryDt'],
            exit_time=result.get('finalExitDt', trade_data['exitDt']),
            profit_pct=result['pnlPct']
        )
        return True
    except ValueError as e:
        print(f"❌ VALIDATION FAILED: {e}")
        return False

def run_comprehensive_validation():
    """Chạy toàn bộ validation suite"""
    
    print("🛡️ COMPREHENSIVE VALIDATION SUITE")
    print("=" * 50)
    
    # 1. Test BE Logic
    BELogicValidator.test_be_sl_calculation()
    print()
    
    # 2. Test Trade #139 validation
    print("🔍 TESTING TRADE #139 VALIDATION:")
    
    try:
        candles = pd.read_csv("data chart full info.csv")
        candles['time'] = pd.to_datetime(candles['time'])
        
        validator = SimulationValidator(candles)
        
        # Test with fantasy result (should fail)
        print("   Testing fantasy result (should FAIL):")
        try:
            validator.validate_trade_result(
                entry_price=0.009937,
                exit_price=0.008919,  # Fantasy exit
                side='SHORT',
                entry_time='2025-06-20 22:00:00',
                exit_time='2025-06-21 08:30:00',
                profit_pct=10.24  # Fantasy profit
            )
            print("   ❌ ERROR: Validation should have failed!")
        except ValueError as e:
            print(f"   ✅ CORRECTLY DETECTED FANTASY: {e}")
        
        # Test with realistic result (should pass)
        print("   Testing realistic result (should PASS):")
        validator.validate_trade_result(
            entry_price=0.009937,
            exit_price=0.009932,  # Realistic BE exit
            side='SHORT', 
            entry_time='2025-06-20 22:00:00',
            exit_time='2025-06-21 08:30:00',
            profit_pct=0.05  # Realistic profit
        )
        
    except Exception as e:
        print(f"❌ Error in validation test: {e}")
    
    print("\n🎯 VALIDATION SUITE COMPLETED")

if __name__ == '__main__':
    run_comprehensive_validation()
