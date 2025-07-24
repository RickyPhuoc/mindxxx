#!/usr/bin/env python3
"""
🕵️ HISTORICAL AUDIT TOOL
Audit tất cả optimization results cũ để tìm fantasy profits
"""

import pandas as pd
import numpy as np
import os
import json
from datetime import datetime
import glob

class HistoricalAuditor:
    """Tool audit kết quả optimization cũ"""
    
    def __init__(self, data_file="data chart full info.csv"):
        """Khởi tạo auditor"""
        self.data = pd.read_csv(data_file)
        self.data['time'] = pd.to_datetime(self.data['time'])
        print(f"✅ Historical Auditor loaded: {len(self.data)} candles")
        
    def find_optimization_files(self, search_patterns=None):
        """Tìm tất cả file optimization results"""
        if search_patterns is None:
            search_patterns = [
                "*tradelist*.csv",
                "*optimization*.csv", 
                "*results*.csv",
                "*slbe*.csv",
                "*gridsearch*.csv"
            ]
        
        found_files = []
        for pattern in search_patterns:
            files = glob.glob(pattern)
            found_files.extend(files)
        
        # Remove duplicates
        found_files = list(set(found_files))
        
        print(f"🔍 Found {len(found_files)} potential optimization files:")
        for f in found_files:
            print(f"   📁 {f}")
        
        return found_files
    
    def audit_csv_file(self, file_path):
        """Audit một CSV file"""
        try:
            df = pd.read_csv(file_path)
            
            # Detect if this is optimization results
            optimization_columns = ['sl', 'be', 'ts_trig', 'ts_step', 'profit', 'avg_profit']
            trade_columns = ['entry_time', 'exit_time', 'entry_price', 'exit_price', 'side']
            
            is_optimization = any(col in df.columns.str.lower() for col in optimization_columns)
            is_trades = any(col in df.columns.str.lower() for col in trade_columns)
            
            audit_result = {
                'file_path': file_path,
                'file_size': os.path.getsize(file_path),
                'rows': len(df),
                'columns': list(df.columns),
                'is_optimization': is_optimization,
                'is_trades': is_trades,
                'fantasy_flags': [],
                'suspicious_profits': [],
                'max_claimed_profit': 0,
                'audit_status': 'unknown'
            }
            
            # Check for suspiciously high profits
            profit_columns = [col for col in df.columns if 'profit' in col.lower()]
            
            for col in profit_columns:
                try:
                    profits = pd.to_numeric(df[col], errors='coerce').dropna()
                    if len(profits) > 0:
                        max_profit = profits.max()
                        audit_result['max_claimed_profit'] = max(audit_result['max_claimed_profit'], max_profit)
                        
                        # Flag suspicious profits (>15% for SHORT, >20% for LONG)
                        suspicious = profits[profits > 15.0]  # Conservative threshold
                        if len(suspicious) > 0:
                            audit_result['suspicious_profits'].extend([
                                {
                                    'column': col,
                                    'value': float(profit),
                                    'row': int(idx)
                                }
                                for idx, profit in suspicious.items()
                            ])
                
                except Exception as e:
                    print(f"   ⚠️ Error processing column {col}: {e}")
            
            # Check for specific patterns indicating fantasy results
            if 'exit_price' in df.columns and 'entry_price' in df.columns:
                try:
                    entry_prices = pd.to_numeric(df['entry_price'], errors='coerce')
                    exit_prices = pd.to_numeric(df['exit_price'], errors='coerce')
                    
                    # Look for unrealistic exit prices
                    if len(entry_prices) > 0 and len(exit_prices) > 0:
                        # Check for trades claiming to exit at prices like 0.008919
                        fantasy_exits = exit_prices[(exit_prices < 0.009000) & (entry_prices > 0.009500)]
                        
                        for idx, exit_price in fantasy_exits.items():
                            audit_result['fantasy_flags'].append({
                                'type': 'unrealistic_exit_price',
                                'exit_price': float(exit_price),
                                'entry_price': float(entry_prices.iloc[idx]) if idx < len(entry_prices) else 'unknown',
                                'row': int(idx)
                            })
                            
                except Exception as e:
                    print(f"   ⚠️ Error checking exit prices: {e}")
            
            # Determine audit status
            if len(audit_result['fantasy_flags']) > 0:
                audit_result['audit_status'] = 'FANTASY_DETECTED'
            elif len(audit_result['suspicious_profits']) > 0:
                audit_result['audit_status'] = 'SUSPICIOUS'
            elif audit_result['max_claimed_profit'] > 10.0:
                audit_result['audit_status'] = 'HIGH_PROFIT_CLAIMS'
            else:
                audit_result['audit_status'] = 'CLEAN'
            
            return audit_result
            
        except Exception as e:
            return {
                'file_path': file_path,
                'error': str(e),
                'audit_status': 'ERROR'
            }
    
    def run_full_audit(self):
        """Chạy audit toàn bộ workspace"""
        print("🕵️ STARTING FULL HISTORICAL AUDIT")
        print("=" * 50)
        
        # Find all potential files
        files = self.find_optimization_files()
        
        if not files:
            print("ℹ️ No optimization files found to audit")
            return
        
        audit_results = []
        fantasy_count = 0
        suspicious_count = 0
        clean_count = 0
        error_count = 0
        
        for file_path in files:
            print(f"\n🔍 Auditing: {file_path}")
            result = self.audit_csv_file(file_path)
            audit_results.append(result)
            
            status = result['audit_status']
            if status == 'FANTASY_DETECTED':
                fantasy_count += 1
                print(f"   🚨 FANTASY DETECTED: {len(result['fantasy_flags'])} fantasy flags")
            elif status == 'SUSPICIOUS':
                suspicious_count += 1
                print(f"   ⚠️ SUSPICIOUS: {len(result['suspicious_profits'])} suspicious profits")
            elif status == 'HIGH_PROFIT_CLAIMS':
                suspicious_count += 1
                print(f"   📈 HIGH CLAIMS: Max profit {result['max_claimed_profit']:.2f}%")
            elif status == 'CLEAN':
                clean_count += 1
                print(f"   ✅ CLEAN: No issues detected")
            else:
                error_count += 1
                print(f"   ❌ ERROR: {result.get('error', 'Unknown error')}")
        
        # Generate summary report
        print(f"\n📊 AUDIT SUMMARY REPORT")
        print("=" * 50)
        print(f"   Total files audited: {len(files)}")
        print(f"   🚨 Fantasy detected: {fantasy_count}")
        print(f"   ⚠️ Suspicious files: {suspicious_count}")
        print(f"   ✅ Clean files: {clean_count}")
        print(f"   ❌ Errors: {error_count}")
        
        if fantasy_count > 0:
            print(f"\n🚨 CRITICAL FINDINGS:")
            for result in audit_results:
                if result['audit_status'] == 'FANTASY_DETECTED':
                    print(f"   📁 {result['file_path']}")
                    for flag in result['fantasy_flags']:
                        print(f"      🚩 {flag['type']}: Row {flag['row']}")
                        if 'exit_price' in flag:
                            print(f"         Exit: {flag['exit_price']:.6f} | Entry: {flag.get('entry_price', 'unknown')}")
        
        # Save detailed report
        report_file = f"audit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(audit_results, f, indent=2)
        
        print(f"\n📄 Detailed report saved: {report_file}")
        
        # Recommendations
        print(f"\n🔧 RECOMMENDATIONS:")
        if fantasy_count > 0:
            print("   1️⃣ IMMEDIATELY stop using results from fantasy-flagged files")
            print("   2️⃣ RE-RUN optimization with reality check enabled")
            print("   3️⃣ VALIDATE all high-profit strategies with actual data")
        
        if suspicious_count > 0:
            print("   4️⃣ REVIEW suspicious files for unrealistic claims")
            print("   5️⃣ APPLY reality check to suspicious results")
        
        print("   6️⃣ IMPLEMENT mandatory reality check for all future optimization")
        print("   7️⃣ BACKUP current files before making changes")
        
        return audit_results

def main():
    """Main audit function"""
    auditor = HistoricalAuditor()
    results = auditor.run_full_audit()
    
    print(f"\n🎯 AUDIT COMPLETE!")
    print("   Use reality_check_optimizer.py for future optimization")
    print("   All suspicious results should be re-validated")

if __name__ == '__main__':
    main()
