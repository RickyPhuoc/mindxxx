#!/usr/bin/env python3
"""
🚀 REALITY CHECK MODULE for Web App Integration
Module tích hợp reality check vào web app hiện tại
"""

import pandas as pd
import numpy as np
from itertools import product
import time
from datetime import datetime
import json

class WebAppRealityChecker:
    """Reality checker tích hợp cho web app"""
    
    def __init__(self, data_file="data chart full info.csv"):
        """Khởi tạo với data file"""
        try:
            self.data = pd.read_csv(data_file)
            self.data['time'] = pd.to_datetime(self.data['time'])
            self.loaded = True
            print(f"✅ Reality Checker loaded: {len(self.data)} candles")
        except Exception as e:
            print(f"❌ Reality Checker failed to load: {e}")
            self.data = None
            self.loaded = False
    
    def validate_trade_result(self, entry_time, exit_time, entry_price, exit_price, side):
        """Validate một kết quả trade với data thực tế"""
        if not self.loaded:
            return {"valid": False, "reason": "Data not loaded"}
        
        try:
            # Find trade period
            entry_time_dt = pd.to_datetime(entry_time).tz_localize(self.data['time'].dt.tz)
            exit_time_dt = pd.to_datetime(exit_time).tz_localize(self.data['time'].dt.tz)
            
            entry_idx = abs(self.data['time'] - entry_time_dt).idxmin()
            exit_idx = abs(self.data['time'] - exit_time_dt).idxmin()
            
            trade_candles = self.data.iloc[entry_idx:exit_idx+1].copy()
            
            if len(trade_candles) == 0:
                return {"valid": False, "reason": "No candles in period"}
            
            # Get actual price extremes
            actual_min = trade_candles['low'].min()
            actual_max = trade_candles['high'].max()
            
            # Calculate claimed profit
            if side == 'SHORT':
                claimed_profit = (entry_price - exit_price) / entry_price * 100
                max_possible_profit = (entry_price - actual_min) / entry_price * 100
                is_reachable = exit_price >= actual_min
            else:  # LONG
                claimed_profit = (exit_price - entry_price) / entry_price * 100
                max_possible_profit = (actual_max - entry_price) / entry_price * 100
                is_reachable = exit_price <= actual_max
            
            # Reality check
            is_realistic = (claimed_profit <= max_possible_profit + 0.01) and is_reachable
            
            return {
                "valid": True,
                "is_realistic": is_realistic,
                "claimed_profit": claimed_profit,
                "max_possible_profit": max_possible_profit,
                "exit_reachable": is_reachable,
                "actual_min": actual_min,
                "actual_max": actual_max,
                "candles_count": len(trade_candles),
                "gap": abs(claimed_profit - max_possible_profit) if not is_realistic else 0
            }
            
        except Exception as e:
            return {"valid": False, "reason": f"Validation error: {e}"}
    
    def reality_check_optimization_results(self, results_data):
        """Reality check cho kết quả optimization"""
        if not self.loaded:
            return {"status": "error", "message": "Reality checker not loaded"}
        
        checked_results = []
        fantasy_count = 0
        
        for result in results_data:
            # Validate từng trade result
            validations = []
            
            # Giả sử structure của result có trade details
            if 'trades' in result:
                for trade in result['trades']:
                    validation = self.validate_trade_result(
                        trade.get('entry_time'),
                        trade.get('exit_time'), 
                        trade.get('entry_price'),
                        trade.get('exit_price'),
                        trade.get('side')
                    )
                    validations.append(validation)
            
            # Tính reality score
            valid_validations = [v for v in validations if v['valid']]
            realistic_count = sum(1 for v in valid_validations if v['is_realistic'])
            reality_score = realistic_count / len(valid_validations) if valid_validations else 0
            
            if reality_score < 0.8:  # Threshold for fantasy
                fantasy_count += 1
            
            # Add reality info to result
            result['reality_check'] = {
                'reality_score': reality_score,
                'realistic_trades': realistic_count,
                'total_trades': len(valid_validations),
                'is_fantasy': reality_score < 0.8,
                'validations': validations
            }
            
            checked_results.append(result)
        
        return {
            "status": "success",
            "results": checked_results,
            "summary": {
                "total_results": len(results_data),
                "fantasy_results": fantasy_count,
                "realistic_results": len(results_data) - fantasy_count,
                "fantasy_rate": fantasy_count / len(results_data) if results_data else 0
            }
        }

# Global instance
reality_checker = WebAppRealityChecker()

def add_reality_check_to_flask_app(app):
    """Thêm reality check endpoints vào Flask app"""
    
    @app.route('/api/reality-check/validate-trade', methods=['POST'])
    def validate_trade_endpoint():
        """API endpoint để validate trade"""
        try:
            data = request.get_json()
            
            validation = reality_checker.validate_trade_result(
                data.get('entry_time'),
                data.get('exit_time'),
                data.get('entry_price'), 
                data.get('exit_price'),
                data.get('side')
            )
            
            return jsonify(validation)
            
        except Exception as e:
            return jsonify({"valid": False, "reason": f"API error: {e}"}), 500
    
    @app.route('/api/reality-check/audit-results', methods=['POST'])
    def audit_results_endpoint():
        """API endpoint để audit optimization results"""
        try:
            data = request.get_json()
            results = data.get('results', [])
            
            audit_result = reality_checker.reality_check_optimization_results(results)
            
            return jsonify(audit_result)
            
        except Exception as e:
            return jsonify({"status": "error", "message": f"Audit error: {e}"}), 500
    
    @app.route('/reality-check-dashboard')
    def reality_check_dashboard():
        """Dashboard để xem reality check results"""
        return render_template('reality_check_dashboard.html')
    
    print("✅ Reality Check endpoints added to Flask app")
    return app

# Wrapper functions để tích hợp với existing optimization
def reality_checked_grid_search(trade_pairs, df_candle, sl_list, be_list, ts_trig_list, ts_step_list, opt_type):
    """Grid search với reality check tích hợp"""
    
    # Import original function
    try:
        from backtest_gridsearch_slbe_ts_Version3 import grid_search_parallel
        
        # Run original optimization
        original_results = grid_search_parallel(
            trade_pairs, df_candle, sl_list, be_list, ts_trig_list, ts_step_list, opt_type
        )
        
        # Add reality check to results
        if original_results and len(original_results) > 0:
            # Convert results to format for reality check
            results_for_check = []
            
            for result in original_results:
                # Convert result format to match reality checker expected format
                result_data = {
                    'trades': [],
                    'parameters': result  # Original result parameters
                }
                
                # Add trade data if available
                for trade_pair in trade_pairs:
                    result_data['trades'].append({
                        'entry_time': trade_pair.get('entry_time'),
                        'exit_time': trade_pair.get('exit_time'),
                        'entry_price': trade_pair.get('entry_price'),
                        'exit_price': None,  # Will be calculated by simulation
                        'side': trade_pair.get('side')
                    })
                
                results_for_check.append(result_data)
            
            # Run reality check
            checked_results = reality_checker.reality_check_optimization_results(results_for_check)
            
            if checked_results['status'] == 'success':
                # Add reality info back to original results
                for i, original_result in enumerate(original_results):
                    if i < len(checked_results['results']):
                        reality_info = checked_results['results'][i]['reality_check']
                        original_results[i] = {
                            **original_result,
                            'reality_score': reality_info['reality_score'],
                            'is_fantasy': reality_info['is_fantasy'],
                            'realistic_trades': reality_info['realistic_trades']
                        }
                
                # Sort by reality score first, then by profit
                original_results.sort(key=lambda x: (x.get('reality_score', 0), x.get('avg_profit', 0)), reverse=True)
                
                print(f"✅ Reality check applied: {checked_results['summary']['realistic_results']}/{checked_results['summary']['total_results']} realistic")
        
        return original_results
        
    except Exception as e:
        print(f"❌ Reality checked grid search failed: {e}")
        return []

def simulate_trade_with_reality_check(trade_pair, df_candle, sl, be, ts_trig, ts_step):
    """Simulate trade với reality check"""
    
    try:
        # Import original function
        from backtest_gridsearch_slbe_ts_Version3 import simulate_trade
        
        # Run original simulation
        result, errors = simulate_trade(trade_pair, df_candle, sl, be, ts_trig, ts_step)
        
        if result and not errors:
            # Add reality check
            validation = reality_checker.validate_trade_result(
                trade_pair.get('entry_time'),
                trade_pair.get('exit_time'),
                trade_pair.get('entry_price'),
                result.get('exit_price'),
                trade_pair.get('side')
            )
            
            # Add reality info to result
            result['reality_check'] = validation
            
            if not validation.get('is_realistic', True):
                errors.append(f"🚨 FANTASY RESULT: Profit {validation.get('claimed_profit', 0):.2f}% exceeds max possible {validation.get('max_possible_profit', 0):.2f}%")
        
        return result, errors
        
    except Exception as e:
        return None, [f"Reality checked simulation failed: {e}"]

if __name__ == '__main__':
    print("🚀 Reality Check Module for Web App")
    print("✅ Ready for integration")
