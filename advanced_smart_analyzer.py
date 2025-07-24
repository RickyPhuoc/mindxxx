#!/usr/bin/env python3
"""
ADVANCED SMART PARAMETER ANALYZER
Phân tích chi tiết tradelist để đưa ra dải parameters tối ưu với độ tin cậy cao

Key Features:
1. Phân tích đa chiều: Run-up, Drawdown, P&L patterns
2. Phân loại trades theo behavioral patterns
3. Tối ưu hóa parameters cho từng scenario
4. Validation và error checking toàn diện
5. Recommendations với confidence scores
"""

import pandas as pd
import numpy as np
import math
import warnings
warnings.filterwarnings('ignore')

class AdvancedSmartAnalyzer:
    def __init__(self, tradelist_path):
        """Initialize analyzer with comprehensive error checking"""
        self.tradelist_path = tradelist_path
        self.df = None
        self.exit_trades = None
        self.analysis_results = {}
        self.validation_errors = []
        
        # Load and validate data
        self._load_and_validate()
    
    def _load_and_validate(self):
        """Load tradelist with comprehensive validation"""
        try:
            print(f"🔍 ADVANCED ANALYSIS: Loading {self.tradelist_path}")
            self.df = pd.read_csv(self.tradelist_path)
            
            # Clean column names
            self.df.columns = [col.strip().lower().replace(' ', '_').replace('/', '_').replace('#', '').replace('&', '') for col in self.df.columns]
            
            print(f"📊 Raw data: {len(self.df)} rows, columns: {self.df.columns.tolist()}")
            
            # Identify key columns with multiple naming patterns
            self.runup_col = self._find_column(['run_up_%', 'run-up_%', 'runup_%', 'max_favorable_%'])
            self.drawdown_col = self._find_column(['drawdown_%', 'draw_down_%', 'max_adverse_%', 'drawdown'])
            self.pnl_col = self._find_column(['cumulative_p_l_%', 'pl_%', 'p_l_%', 'pnl_%', 'profit_loss_%'])
            self.type_col = self._find_column(['type', 'signal_type', 'trade_type'])
            
            if not all([self.runup_col, self.drawdown_col, self.pnl_col, self.type_col]):
                missing = []
                if not self.runup_col: missing.append("Run-up column")
                if not self.drawdown_col: missing.append("Drawdown column") 
                if not self.pnl_col: missing.append("P&L column")
                if not self.type_col: missing.append("Type column")
                
                error_msg = f"❌ Missing required columns: {missing}"
                print(error_msg)
                self.validation_errors.append(error_msg)
                return False
            
            print(f"✅ Key columns identified:")
            print(f"   Run-up: {self.runup_col}")
            print(f"   Drawdown: {self.drawdown_col}")
            print(f"   P&L: {self.pnl_col}")
            print(f"   Type: {self.type_col}")
            
            # Clean and convert data
            self._clean_percentage_data()
            
            # Filter for exit trades only
            self._filter_exit_trades()
            
            return True
            
        except Exception as e:
            error_msg = f"❌ Data loading error: {str(e)}"
            print(error_msg)
            self.validation_errors.append(error_msg)
            return False
    
    def _find_column(self, patterns):
        """Find column matching any of the given patterns"""
        for pattern in patterns:
            for col in self.df.columns:
                if pattern.lower() in col.lower():
                    return col
        return None
    
    def _clean_percentage_data(self):
        """Clean and convert percentage columns with error handling"""
        percentage_cols = [self.runup_col, self.drawdown_col, self.pnl_col]
        
        for col in percentage_cols:
            if col is None:
                continue
                
            print(f"🧹 Cleaning column: {col}")
            original_count = len(self.df)
            
            # Remove % signs and other formatting
            self.df[col] = self.df[col].astype(str).str.replace('%', '').str.replace(',', '').str.replace('$', '')
            
            # Convert to numeric
            self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
            
            # Check for data quality issues
            null_count = self.df[col].isnull().sum()
            if null_count > 0:
                print(f"   ⚠️ Found {null_count} null values in {col}")
            
            # Check for unrealistic values
            extreme_positive = (self.df[col] > 100).sum() if col != self.drawdown_col else 0
            extreme_negative = (self.df[col] < -100).sum() if col != self.runup_col else 0
            
            if extreme_positive > 0:
                print(f"   ⚠️ Found {extreme_positive} extremely high values (>100%) in {col}")
            if extreme_negative > 0:
                print(f"   ⚠️ Found {extreme_negative} extremely low values (<-100%) in {col}")
    
    def _filter_exit_trades(self):
        """Filter for exit trades with validation"""
        if self.type_col is None:
            self.validation_errors.append("Cannot filter exit trades - no type column")
            return
        
        # Find exit patterns
        exit_patterns = ['exit', 'close', 'sell']
        exit_mask = False
        
        for pattern in exit_patterns:
            mask = self.df[self.type_col].str.lower().str.contains(pattern, na=False)
            exit_mask = exit_mask | mask
        
        self.exit_trades = self.df[exit_mask].copy()
        
        print(f"📈 Filtered to {len(self.exit_trades)} exit trades from {len(self.df)} total records")
        
        if len(self.exit_trades) == 0:
            error_msg = "❌ No exit trades found! Check if Type column contains 'exit', 'close', or 'sell' values"
            print(error_msg)
            self.validation_errors.append(error_msg)
    
    def analyze_price_movement_patterns(self):
        """Phân tích patterns chuyển động giá chi tiết"""
        if self.exit_trades is None or len(self.exit_trades) == 0:
            return None
        
        print(f"\n🎯 ANALYZING PRICE MOVEMENT PATTERNS")
        print(f"=" * 50)
        
        # 1. BEHAVIORAL CLASSIFICATION
        patterns = self._classify_trade_behaviors()
        
        # 2. PRICE RANGE ANALYSIS 
        price_ranges = self._analyze_price_ranges()
        
        # 3. TIME-BASED PATTERNS
        time_patterns = self._analyze_time_patterns()
        
        # 4. RISK-REWARD CORRELATION
        risk_reward = self._analyze_risk_reward_correlation()
        
        # 5. OPTIMIZATION SCENARIOS
        scenarios = self._generate_optimization_scenarios()
        
        self.analysis_results = {
            'behavioral_patterns': patterns,
            'price_ranges': price_ranges,
            'time_patterns': time_patterns,
            'risk_reward': risk_reward,
            'optimization_scenarios': scenarios,
            'data_quality': self._assess_data_quality()
        }
        
        return self.analysis_results
    
    def _classify_trade_behaviors(self):
        """Phân loại trades theo hành vi giá"""
        runup = self.exit_trades[self.runup_col].abs()
        drawdown = self.exit_trades[self.drawdown_col].abs() 
        pnl = self.exit_trades[self.pnl_col]
        
        # Define behavioral categories
        behaviors = {
            'trending_winners': ((runup > runup.quantile(0.75)) & (pnl > 0)),
            'choppy_winners': ((runup <= runup.quantile(0.5)) & (pnl > 0) & (drawdown <= drawdown.quantile(0.5))),
            'volatile_winners': ((drawdown > drawdown.quantile(0.75)) & (pnl > 0)),
            'quick_losers': ((drawdown > drawdown.quantile(0.6)) & (pnl < 0) & (runup <= runup.quantile(0.3))),
            'near_miss_losers': ((runup > runup.quantile(0.6)) & (pnl < 0)),
            'grinding_losers': ((runup <= runup.quantile(0.4)) & (pnl < 0) & (drawdown <= drawdown.quantile(0.6)))
        }
        
        results = {}
        total_trades = len(self.exit_trades)
        
        for behavior, mask in behaviors.items():
            count = mask.sum()
            percentage = count / total_trades * 100
            
            if count > 0:
                avg_runup = runup[mask].mean()
                avg_drawdown = drawdown[mask].mean()
                avg_pnl = pnl[mask].mean()
                
                results[behavior] = {
                    'count': count,
                    'percentage': percentage,
                    'avg_runup': avg_runup,
                    'avg_drawdown': avg_drawdown, 
                    'avg_pnl': avg_pnl
                }
                
                print(f"📊 {behavior.upper().replace('_', ' ')}: {count} trades ({percentage:.1f}%)")
                print(f"   Avg Run-up: {avg_runup:.2f}%, Drawdown: {avg_drawdown:.2f}%, P&L: {avg_pnl:.2f}%")
        
        return results
    
    def _analyze_price_ranges(self):
        """Phân tích chi tiết các dải giá movement"""
        runup = self.exit_trades[self.runup_col].abs()
        drawdown = self.exit_trades[self.drawdown_col].abs()
        
        # Percentile analysis
        percentiles = [10, 25, 50, 75, 90, 95]
        
        runup_percentiles = {}
        drawdown_percentiles = {}
        
        for p in percentiles:
            runup_percentiles[f'p{p}'] = runup.quantile(p/100)
            drawdown_percentiles[f'p{p}'] = drawdown.quantile(p/100)
        
        print(f"\n📈 RUN-UP DISTRIBUTION:")
        for p in percentiles:
            print(f"   {p}th percentile: {runup_percentiles[f'p{p}']:.2f}%")
        
        print(f"\n📉 DRAWDOWN DISTRIBUTION:")
        for p in percentiles:
            print(f"   {p}th percentile: {drawdown_percentiles[f'p{p}']:.2f}%")
        
        # Identify outliers
        runup_q75 = runup.quantile(0.75)
        runup_q25 = runup.quantile(0.25)
        runup_iqr = runup_q75 - runup_q25
        runup_outliers = ((runup < runup_q25 - 1.5*runup_iqr) | (runup > runup_q75 + 1.5*runup_iqr)).sum()
        
        drawdown_q75 = drawdown.quantile(0.75)
        drawdown_q25 = drawdown.quantile(0.25)
        drawdown_iqr = drawdown_q75 - drawdown_q25
        drawdown_outliers = ((drawdown < drawdown_q25 - 1.5*drawdown_iqr) | (drawdown > drawdown_q75 + 1.5*drawdown_iqr)).sum()
        
        print(f"\n🎯 OUTLIER ANALYSIS:")
        print(f"   Run-up outliers: {runup_outliers} trades ({runup_outliers/len(runup)*100:.1f}%)")
        print(f"   Drawdown outliers: {drawdown_outliers} trades ({drawdown_outliers/len(drawdown)*100:.1f}%)")
        
        return {
            'runup_percentiles': runup_percentiles,
            'drawdown_percentiles': drawdown_percentiles,
            'runup_outliers': runup_outliers,
            'drawdown_outliers': drawdown_outliers,
            'runup_iqr': runup_iqr,
            'drawdown_iqr': drawdown_iqr
        }
    
    def _analyze_time_patterns(self):
        """Phân tích patterns theo thời gian (nếu có cột date)"""
        # Placeholder for time-based analysis
        # Would need date columns to implement fully
        print(f"\n⏰ TIME PATTERN ANALYSIS:")
        print(f"   (Requires date columns - future enhancement)")
        
        return {
            'note': 'Time analysis requires date columns - not implemented yet'
        }
    
    def _analyze_risk_reward_correlation(self):
        """Phân tích mối tương quan giữa risk và reward"""
        runup = self.exit_trades[self.runup_col].abs()
        drawdown = self.exit_trades[self.drawdown_col].abs()
        pnl = self.exit_trades[self.pnl_col]
        
        # Correlation analysis
        runup_pnl_corr = runup.corr(pnl)
        drawdown_pnl_corr = drawdown.corr(pnl)
        runup_drawdown_corr = runup.corr(drawdown)
        
        print(f"\n🔄 RISK-REWARD CORRELATIONS:")
        print(f"   Run-up vs P&L: {runup_pnl_corr:.3f}")
        print(f"   Drawdown vs P&L: {drawdown_pnl_corr:.3f}")
        print(f"   Run-up vs Drawdown: {runup_drawdown_corr:.3f}")
        
        # Risk efficiency metrics
        winning_trades = self.exit_trades[pnl > 0]
        losing_trades = self.exit_trades[pnl <= 0]
        
        if len(winning_trades) > 0 and len(losing_trades) > 0:
            avg_win_runup = winning_trades[self.runup_col].abs().mean()
            avg_win_drawdown = winning_trades[self.drawdown_col].abs().mean()
            avg_loss_runup = losing_trades[self.runup_col].abs().mean()
            avg_loss_drawdown = losing_trades[self.drawdown_col].abs().mean()
            
            print(f"\n🏆 WINNERS vs 💥 LOSERS:")
            print(f"   Win Trades: Avg Run-up {avg_win_runup:.2f}%, Avg Drawdown {avg_win_drawdown:.2f}%")
            print(f"   Loss Trades: Avg Run-up {avg_loss_runup:.2f}%, Avg Drawdown {avg_loss_drawdown:.2f}%")
            
            return {
                'correlations': {
                    'runup_pnl': runup_pnl_corr,
                    'drawdown_pnl': drawdown_pnl_corr,
                    'runup_drawdown': runup_drawdown_corr
                },
                'winner_stats': {
                    'avg_runup': avg_win_runup,
                    'avg_drawdown': avg_win_drawdown
                },
                'loser_stats': {
                    'avg_runup': avg_loss_runup,
                    'avg_drawdown': avg_loss_drawdown
                }
            }
        
        return {'note': 'Insufficient data for correlation analysis'}
    
    def _generate_optimization_scenarios(self):
        """Tạo ra các scenarios tối ưu hóa khác nhau"""
        runup = self.exit_trades[self.runup_col].abs()
        drawdown = self.exit_trades[self.drawdown_col].abs()
        pnl = self.exit_trades[self.pnl_col]
        
        scenarios = {}
        
        # 1. CONSERVATIVE SCENARIO: Tối thiểu risk
        conservative_sl = drawdown.quantile(0.6)  # 60th percentile
        conservative_be = runup.quantile(0.3)     # 30th percentile
        conservative_ts = runup.quantile(0.4)     # 40th percentile
        
        scenarios['conservative'] = {
            'description': 'Minimize risk, accept lower profits',
            'sl_range': {'min': conservative_sl * 0.8, 'max': conservative_sl * 1.2, 'step': 0.5},
            'be_range': {'min': conservative_be * 0.5, 'max': conservative_be * 1.5, 'step': 0.25},
            'ts_range': {'min': conservative_ts * 0.7, 'max': conservative_ts * 1.3, 'step': 0.5},
            'confidence': 'HIGH'
        }
        
        # 2. BALANCED SCENARIO: Cân bằng risk-reward
        balanced_sl = drawdown.quantile(0.75)    # 75th percentile
        balanced_be = runup.quantile(0.4)        # 40th percentile
        balanced_ts = runup.quantile(0.6)        # 60th percentile
        
        scenarios['balanced'] = {
            'description': 'Balance between risk and reward',
            'sl_range': {'min': balanced_sl * 0.8, 'max': balanced_sl * 1.3, 'step': 0.5},
            'be_range': {'min': balanced_be * 0.6, 'max': balanced_be * 1.8, 'step': 0.25},
            'ts_range': {'min': balanced_ts * 0.7, 'max': balanced_ts * 1.5, 'step': 0.5},
            'confidence': 'HIGH'
        }
        
        # 3. AGGRESSIVE SCENARIO: Tối đa profits
        aggressive_sl = drawdown.quantile(0.9)   # 90th percentile
        aggressive_be = runup.quantile(0.2)      # 20th percentile (thấp để không miss profits)
        aggressive_ts = runup.quantile(0.8)      # 80th percentile
        
        scenarios['aggressive'] = {
            'description': 'Maximize profits, accept higher risk',
            'sl_range': {'min': aggressive_sl * 0.7, 'max': aggressive_sl * 1.5, 'step': 1.0},
            'be_range': {'min': aggressive_be * 0.3, 'max': aggressive_be * 2.0, 'step': 0.25},
            'ts_range': {'min': aggressive_ts * 0.6, 'max': aggressive_ts * 1.8, 'step': 0.5},
            'confidence': 'MEDIUM'
        }
        
        print(f"\n🎯 OPTIMIZATION SCENARIOS:")
        for name, scenario in scenarios.items():
            print(f"\n📋 {name.upper()} STRATEGY:")
            print(f"   {scenario['description']}")
            print(f"   SL Range: {scenario['sl_range']['min']:.1f}% - {scenario['sl_range']['max']:.1f}%")
            print(f"   BE Range: {scenario['be_range']['min']:.2f}% - {scenario['be_range']['max']:.2f}%")
            print(f"   TS Range: {scenario['ts_range']['min']:.2f}% - {scenario['ts_range']['max']:.2f}%")
            print(f"   Confidence: {scenario['confidence']}")
        
        return scenarios
    
    def _assess_data_quality(self):
        """Đánh giá chất lượng dữ liệu"""
        if self.exit_trades is None:
            return {'quality': 'POOR', 'issues': ['No exit trades found']}
        
        total_trades = len(self.exit_trades)
        issues = []
        
        # Check sample size
        if total_trades < 50:
            issues.append(f"Small sample size: {total_trades} trades (recommend >100)")
        elif total_trades < 20:
            issues.append(f"Very small sample: {total_trades} trades (results unreliable)")
        
        # Check for null values
        runup_nulls = self.exit_trades[self.runup_col].isnull().sum()
        drawdown_nulls = self.exit_trades[self.drawdown_col].isnull().sum()
        pnl_nulls = self.exit_trades[self.pnl_col].isnull().sum()
        
        null_percentage = (runup_nulls + drawdown_nulls + pnl_nulls) / (total_trades * 3) * 100
        if null_percentage > 10:
            issues.append(f"High null values: {null_percentage:.1f}%")
        
        # Check for unrealistic values
        extreme_runups = (self.exit_trades[self.runup_col].abs() > 50).sum()
        extreme_drawdowns = (self.exit_trades[self.drawdown_col].abs() > 50).sum()
        
        if extreme_runups > total_trades * 0.05:
            issues.append(f"Many extreme run-ups: {extreme_runups} trades")
        if extreme_drawdowns > total_trades * 0.05:
            issues.append(f"Many extreme drawdowns: {extreme_drawdowns} trades")
        
        # Overall quality assessment
        if len(issues) == 0:
            quality = 'EXCELLENT'
        elif len(issues) <= 2:
            quality = 'GOOD'
        elif len(issues) <= 4:
            quality = 'FAIR'
        else:
            quality = 'POOR'
        
        print(f"\n📊 DATA QUALITY ASSESSMENT: {quality}")
        if issues:
            print(f"   Issues found:")
            for issue in issues:
                print(f"   - {issue}")
        else:
            print(f"   ✅ No quality issues detected")
        
        return {
            'quality': quality,
            'total_trades': total_trades,
            'null_percentage': null_percentage,
            'issues': issues
        }
    
    def generate_final_recommendations(self):
        """Tạo khuyến nghị cuối cùng với confidence scores"""
        if not self.analysis_results:
            self.analyze_price_movement_patterns()
        
        if not self.analysis_results or self.validation_errors:
            print(f"\n❌ CANNOT GENERATE RECOMMENDATIONS")
            print(f"Validation errors: {self.validation_errors}")
            return None
        
        print(f"\n🎯 FINAL SMART RECOMMENDATIONS")
        print(f"=" * 60)
        
        scenarios = self.analysis_results['optimization_scenarios']
        data_quality = self.analysis_results['data_quality']
        
        # Choose best scenario based on data quality
        if data_quality['quality'] in ['EXCELLENT', 'GOOD']:
            recommended_scenario = 'balanced'
            confidence = 'HIGH'
        elif data_quality['quality'] == 'FAIR':
            recommended_scenario = 'conservative'
            confidence = 'MEDIUM'
        else:
            recommended_scenario = 'conservative'
            confidence = 'LOW'
        
        best_scenario = scenarios[recommended_scenario]
        
        print(f"\n🏆 RECOMMENDED STRATEGY: {recommended_scenario.upper()}")
        print(f"📊 Confidence Level: {confidence}")
        print(f"💡 Rationale: {best_scenario['description']}")
        print(f"📈 Data Quality: {data_quality['quality']} ({data_quality['total_trades']} trades)")
        
        # Calculate efficiency gain
        conservative_combinations = self._calculate_combinations(scenarios['conservative'])
        balanced_combinations = self._calculate_combinations(scenarios['balanced'])
        aggressive_combinations = self._calculate_combinations(scenarios['aggressive'])
        
        # Typical blind scan would be much larger
        typical_blind_scan = 35 * 8 * 6 * 5  # Example: 35 SL * 8 BE * 6 TS_trig * 5 TS_step
        
        efficiency_gain = typical_blind_scan / balanced_combinations if balanced_combinations > 0 else 0
        
        print(f"\n⚡ EFFICIENCY ANALYSIS:")
        print(f"   Conservative scenario: {conservative_combinations} combinations")
        print(f"   Balanced scenario: {balanced_combinations} combinations")
        print(f"   Aggressive scenario: {aggressive_combinations} combinations")
        print(f"   Typical blind scan: {typical_blind_scan:,} combinations")
        print(f"   Smart analysis efficiency: {efficiency_gain:.0f}x faster")
        
        # Final parameter ranges
        final_ranges = best_scenario.copy()
        del final_ranges['description']
        del final_ranges['confidence']
        
        # Round to practical values
        for param_type in ['sl_range', 'be_range', 'ts_range']:
            for bound in ['min', 'max']:
                final_ranges[param_type][bound] = round(final_ranges[param_type][bound], 2)
        
        print(f"\n📋 FINAL PARAMETER RANGES:")
        print(f"   Stop Loss: {final_ranges['sl_range']['min']:.1f}% - {final_ranges['sl_range']['max']:.1f}% (step: {final_ranges['sl_range']['step']})")
        print(f"   Breakeven: {final_ranges['be_range']['min']:.2f}% - {final_ranges['be_range']['max']:.2f}% (step: {final_ranges['be_range']['step']})")
        print(f"   Trailing Stop: {final_ranges['ts_range']['min']:.2f}% - {final_ranges['ts_range']['max']:.2f}% (step: {final_ranges['ts_range']['step']})")
        
        return {
            'recommended_scenario': recommended_scenario,
            'confidence': confidence,
            'parameter_ranges': final_ranges,
            'efficiency_gain': efficiency_gain,
            'data_quality': data_quality,
            'all_scenarios': scenarios
        }
    
    def _calculate_combinations(self, scenario):
        """Tính số combinations cho một scenario"""
        sl_count = max(1, int((scenario['sl_range']['max'] - scenario['sl_range']['min']) / scenario['sl_range']['step']) + 1)
        be_count = max(1, int((scenario['be_range']['max'] - scenario['be_range']['min']) / scenario['be_range']['step']) + 1)
        ts_count = max(1, int((scenario['ts_range']['max'] - scenario['ts_range']['min']) / scenario['ts_range']['step']) + 1)
        
        return sl_count * be_count * ts_count

def main():
    """Test the advanced analyzer"""
    analyzer = AdvancedSmartAnalyzer('60-tradelist-LONGSHORT.csv')
    
    if analyzer.validation_errors:
        print("❌ Validation failed, cannot proceed")
        return
    
    # Run full analysis
    results = analyzer.analyze_price_movement_patterns()
    
    # Generate recommendations
    recommendations = analyzer.generate_final_recommendations()
    
    return analyzer, results, recommendations

if __name__ == "__main__":
    analyzer, results, recommendations = main()
