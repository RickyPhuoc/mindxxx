#!/usr/bin/env python3
"""
SMART PARAMETER RANGE FINDER
=========================
Mục đích: Tìm ra dải thông số thông minh để quét grid search hiệu quả
KHÔNG nhằm tìm thông số tối ưu cuối cùng - đó là việc của simulation thực chiến

Features:
1. Phân tích tradelist để khoanh vùng dải parameters có xác suất cao
2. Giảm thiểu không gian tìm kiếm từ hàng chục nghìn xuống hàng trăm combinations
3. Đảm bảo không miss các scenarios quan trọng
4. Chuẩn bị mở rộng cho TP1,2,4 + volume % trong tương lai

Output: Smart ranges cho SL, BE, TS để input vào grid search optimizer
"""

import pandas as pd
import numpy as np
import math
import warnings
warnings.filterwarnings('ignore')

class SmartRangeFinder:
    def __init__(self, tradelist_path):
        """
        Initialize Smart Range Finder
        Purpose: Find intelligent parameter ranges for efficient grid search
        """
        self.tradelist_path = tradelist_path
        self.df = None
        self.exit_trades = None
        self.range_analysis = {}
        self.validation_issues = []
        
        print(f"🎯 SMART RANGE FINDER")
        print(f"Purpose: Find intelligent parameter ranges for grid search")
        print(f"Loading: {tradelist_path}")
        
        # Load and validate data
        self._load_and_validate_data()
    
    def _load_and_validate_data(self):
        """Load and validate tradelist data with comprehensive error checking"""
        try:
            self.df = pd.read_csv(self.tradelist_path)
            print(f"✅ Loaded {len(self.df)} raw records")
            
            # Clean column names for consistent access
            self.df.columns = [col.strip().lower().replace(' ', '_').replace('/', '_').replace('#', '').replace('&', '') for col in self.df.columns]
            
            # Identify key columns with flexible naming
            self.runup_col = self._find_key_column(['run_up_%', 'run-up_%', 'runup_%', 'max_favorable_%'], 'Run-up')
            self.drawdown_col = self._find_key_column(['drawdown_%', 'draw_down_%', 'max_adverse_%'], 'Drawdown') 
            self.pnl_col = self._find_key_column(['cumulative_p_l_%', 'pl_%', 'p_l_%', 'pnl_%'], 'P&L')
            self.type_col = self._find_key_column(['type', 'signal_type', 'trade_type'], 'Type')
            
            # Validate required columns exist
            missing_cols = []
            if not self.runup_col: missing_cols.append("Run-up % column")
            if not self.drawdown_col: missing_cols.append("Drawdown % column")
            if not self.pnl_col: missing_cols.append("P&L % column")
            if not self.type_col: missing_cols.append("Type column")
            
            if missing_cols:
                raise ValueError(f"Missing critical columns: {missing_cols}")
            
            print(f"📊 Key columns identified:")
            print(f"   Run-up: {self.runup_col}")
            print(f"   Drawdown: {self.drawdown_col}")
            print(f"   P&L: {self.pnl_col}")
            print(f"   Type: {self.type_col}")
            
            # Clean and convert percentage data
            self._clean_percentage_columns()
            
            # Filter for completed trades (exit records only)
            self._extract_exit_trades()
            
            # Validate data quality
            self._validate_data_quality()
            
        except Exception as e:
            error_msg = f"❌ Data loading failed: {str(e)}"
            print(error_msg)
            self.validation_issues.append(error_msg)
            raise
    
    def _find_key_column(self, patterns, column_name):
        """Find column matching any of the given patterns"""
        for pattern in patterns:
            for col in self.df.columns:
                if pattern.lower() in col.lower():
                    return col
        
        print(f"⚠️ Could not find {column_name} column. Available columns:")
        print(f"   {self.df.columns.tolist()}")
        return None
    
    def _clean_percentage_columns(self):
        """Clean and convert percentage columns with error handling"""
        percentage_cols = [self.runup_col, self.drawdown_col, self.pnl_col]
        
        for col in percentage_cols:
            if col is None:
                continue
            
            print(f"🧹 Cleaning {col}...")
            
            # Remove formatting characters and convert to numeric
            self.df[col] = self.df[col].astype(str).str.replace('%', '').str.replace(',', '').str.replace('$', '')
            self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
            
            # Check for data issues
            null_count = self.df[col].isnull().sum()
            if null_count > 0:
                print(f"   ⚠️ {null_count} null values found and will be excluded")
    
    def _extract_exit_trades(self):
        """Extract completed trades (exit records) for analysis"""
        if self.type_col is None:
            raise ValueError("Cannot filter exit trades - no type column found")
        
        # Look for exit patterns in type column
        exit_patterns = ['exit', 'close', 'sell']
        exit_mask = pd.Series([False] * len(self.df))
        
        for pattern in exit_patterns:
            mask = self.df[self.type_col].str.lower().str.contains(pattern, na=False)
            exit_mask = exit_mask | mask
        
        self.exit_trades = self.df[exit_mask].copy()
        
        # Remove rows with null values in key columns
        key_cols = [self.runup_col, self.drawdown_col, self.pnl_col]
        before_count = len(self.exit_trades)
        self.exit_trades = self.exit_trades.dropna(subset=key_cols)
        after_count = len(self.exit_trades)
        
        if before_count != after_count:
            print(f"🧹 Removed {before_count - after_count} rows with missing data")
        
        print(f"📈 Extracted {len(self.exit_trades)} completed trades for analysis")
        
        if len(self.exit_trades) == 0:
            raise ValueError("No valid exit trades found for analysis")
    
    def _validate_data_quality(self):
        """Assess data quality and flag potential issues"""
        total_trades = len(self.exit_trades)
        
        # Check sample size
        if total_trades < 50:
            issue = f"Small sample size: {total_trades} trades (recommend >100 for reliable analysis)"
            print(f"⚠️ {issue}")
            self.validation_issues.append(issue)
        
        # Check for extreme values that might indicate data errors
        runup_vals = self.exit_trades[self.runup_col].abs()
        drawdown_vals = self.exit_trades[self.drawdown_col].abs()
        
        extreme_runups = (runup_vals > 100).sum()  # > 100% run-up
        extreme_drawdowns = (drawdown_vals > 100).sum()  # > 100% drawdown
        
        if extreme_runups > 0:
            issue = f"{extreme_runups} trades with extreme run-ups (>100%) - check data quality"
            print(f"⚠️ {issue}")
            self.validation_issues.append(issue)
        
        if extreme_drawdowns > 0:
            issue = f"{extreme_drawdowns} trades with extreme drawdowns (>100%) - check data quality"
            print(f"⚠️ {issue}")
            self.validation_issues.append(issue)
        
        # Calculate win rate for context
        winning_trades = (self.exit_trades[self.pnl_col] > 0).sum()
        win_rate = winning_trades / total_trades * 100
        
        print(f"📊 Data Quality Summary:")
        print(f"   Total trades: {total_trades}")
        print(f"   Win rate: {win_rate:.1f}%")
        print(f"   Data issues: {len(self.validation_issues)}")
    
    def analyze_price_movement_patterns(self):
        """
        Core analysis: Extract price movement patterns to determine smart parameter ranges
        """
        if len(self.exit_trades) == 0:
            raise ValueError("No exit trades available for analysis")
        
        print(f"\n🔍 ANALYZING PRICE MOVEMENT PATTERNS")
        print(f"=" * 55)
        
        # Extract absolute values for analysis
        runup_abs = self.exit_trades[self.runup_col].abs()
        drawdown_abs = self.exit_trades[self.drawdown_col].abs()
        pnl_values = self.exit_trades[self.pnl_col]
        
        # 1. STATISTICAL DISTRIBUTION ANALYSIS
        stats_analysis = self._analyze_statistical_distributions(runup_abs, drawdown_abs, pnl_values)
        
        # 2. BEHAVIORAL PATTERN CLASSIFICATION
        behavior_analysis = self._classify_trading_behaviors(runup_abs, drawdown_abs, pnl_values)
        
        # 3. RISK-REWARD SCENARIO MAPPING
        scenario_analysis = self._map_risk_reward_scenarios(runup_abs, drawdown_abs, pnl_values)
        
        # 4. PARAMETER RANGE CALCULATION
        range_recommendations = self._calculate_smart_ranges(stats_analysis, behavior_analysis, scenario_analysis)
        
        self.range_analysis = {
            'statistics': stats_analysis,
            'behaviors': behavior_analysis,
            'scenarios': scenario_analysis,
            'recommended_ranges': range_recommendations
        }
        
        return self.range_analysis
    
    def _analyze_statistical_distributions(self, runup_abs, drawdown_abs, pnl_values):
        """Analyze statistical distributions of price movements"""
        print(f"\n📊 STATISTICAL DISTRIBUTION ANALYSIS")
        
        # Calculate key percentiles for understanding distribution spread
        percentiles = [5, 10, 25, 50, 75, 90, 95]
        
        runup_percentiles = {}
        drawdown_percentiles = {}
        
        for p in percentiles:
            runup_percentiles[f'p{p}'] = runup_abs.quantile(p/100)
            drawdown_percentiles[f'p{p}'] = drawdown_abs.quantile(p/100)
        
        # Calculate key statistics
        stats = {
            'runup': {
                'mean': runup_abs.mean(),
                'median': runup_abs.median(),
                'std': runup_abs.std(),
                'max': runup_abs.max(),
                'percentiles': runup_percentiles
            },
            'drawdown': {
                'mean': drawdown_abs.mean(),
                'median': drawdown_abs.median(),
                'std': drawdown_abs.std(),
                'max': drawdown_abs.max(),
                'percentiles': drawdown_percentiles
            },
            'pnl': {
                'mean': pnl_values.mean(),
                'median': pnl_values.median(),
                'positive_rate': (pnl_values > 0).mean() * 100
            }
        }
        
        print(f"RUN-UP Distribution:")
        print(f"   Mean: {stats['runup']['mean']:.2f}%, Median: {stats['runup']['median']:.2f}%")
        print(f"   25th-75th percentile: {runup_percentiles['p25']:.2f}% - {runup_percentiles['p75']:.2f}%")
        print(f"   90th-95th percentile: {runup_percentiles['p90']:.2f}% - {runup_percentiles['p95']:.2f}%")
        
        print(f"DRAWDOWN Distribution:")
        print(f"   Mean: {stats['drawdown']['mean']:.2f}%, Median: {stats['drawdown']['median']:.2f}%")
        print(f"   25th-75th percentile: {drawdown_percentiles['p25']:.2f}% - {drawdown_percentiles['p75']:.2f}%")
        print(f"   90th-95th percentile: {drawdown_percentiles['p90']:.2f}% - {drawdown_percentiles['p95']:.2f}%")
        
        return stats
    
    def _classify_trading_behaviors(self, runup_abs, drawdown_abs, pnl_values):
        """Classify trades into behavioral patterns for targeted parameter tuning"""
        print(f"\n🎭 TRADING BEHAVIOR CLASSIFICATION")
        
        # Define behavior categories based on price movement characteristics
        behaviors = {}
        total_trades = len(runup_abs)
        
        # 1. TRENDING WINNERS: High run-up, profitable
        trending_winners = (runup_abs > runup_abs.quantile(0.75)) & (pnl_values > 0)
        behaviors['trending_winners'] = {
            'count': trending_winners.sum(),
            'percentage': trending_winners.sum() / total_trades * 100,
            'avg_runup': runup_abs[trending_winners].mean(),
            'avg_drawdown': drawdown_abs[trending_winners].mean(),
            'description': 'Strong trends with good profits - need wider TS ranges'
        }
        
        # 2. VOLATILE WINNERS: High drawdown but still profitable
        volatile_winners = (drawdown_abs > drawdown_abs.quantile(0.75)) & (pnl_values > 0)
        behaviors['volatile_winners'] = {
            'count': volatile_winners.sum(),
            'percentage': volatile_winners.sum() / total_trades * 100,
            'avg_runup': runup_abs[volatile_winners].mean(),
            'avg_drawdown': drawdown_abs[volatile_winners].mean(),
            'description': 'High volatility but profitable - need wider SL ranges'
        }
        
        # 3. QUICK LOSERS: High drawdown, minimal run-up, losing
        quick_losers = (drawdown_abs > drawdown_abs.quantile(0.6)) & (runup_abs < runup_abs.quantile(0.4)) & (pnl_values <= 0)
        behaviors['quick_losers'] = {
            'count': quick_losers.sum(),
            'percentage': quick_losers.sum() / total_trades * 100,
            'avg_runup': runup_abs[quick_losers].mean(),
            'avg_drawdown': drawdown_abs[quick_losers].mean(),
            'description': 'Fast losses - SL should catch these early'
        }
        
        # 4. NEAR MISS LOSERS: Good run-up but ultimately losing
        near_miss_losers = (runup_abs > runup_abs.quantile(0.5)) & (pnl_values <= 0)
        behaviors['near_miss_losers'] = {
            'count': near_miss_losers.sum(),
            'percentage': near_miss_losers.sum() / total_trades * 100,
            'avg_runup': runup_abs[near_miss_losers].mean(),
            'avg_drawdown': drawdown_abs[near_miss_losers].mean(),
            'description': 'Had potential but failed - BE/TS could help'
        }
        
        # Print behavior analysis
        for behavior_name, data in behaviors.items():
            if data['count'] > 0:
                print(f"{behavior_name.upper().replace('_', ' ')}: {data['count']} trades ({data['percentage']:.1f}%)")
                print(f"   Avg Run-up: {data['avg_runup']:.2f}%, Avg Drawdown: {data['avg_drawdown']:.2f}%")
                print(f"   Implication: {data['description']}")
        
        return behaviors
    
    def _map_risk_reward_scenarios(self, runup_abs, drawdown_abs, pnl_values):
        """Map different risk-reward scenarios for parameter optimization"""
        print(f"\n🎯 RISK-REWARD SCENARIO MAPPING")
        
        scenarios = {}
        
        # Scenario 1: Conservative (focus on protecting capital)
        conservative_mask = drawdown_abs <= drawdown_abs.quantile(0.6)
        scenarios['conservative'] = {
            'trade_count': conservative_mask.sum(),
            'percentage': conservative_mask.sum() / len(drawdown_abs) * 100,
            'target_sl_max': drawdown_abs[conservative_mask].quantile(0.8),
            'target_be_range': runup_abs[conservative_mask].quantile(0.3),
            'target_ts_trigger': runup_abs[conservative_mask].quantile(0.5),
            'description': 'Lower risk tolerance - tight parameters'
        }
        
        # Scenario 2: Balanced (standard risk-reward)
        balanced_mask = (drawdown_abs > drawdown_abs.quantile(0.3)) & (drawdown_abs <= drawdown_abs.quantile(0.8))
        scenarios['balanced'] = {
            'trade_count': balanced_mask.sum(),
            'percentage': balanced_mask.sum() / len(drawdown_abs) * 100,
            'target_sl_max': drawdown_abs[balanced_mask].quantile(0.85),
            'target_be_range': runup_abs[balanced_mask].quantile(0.4),
            'target_ts_trigger': runup_abs[balanced_mask].quantile(0.6),
            'description': 'Standard risk-reward balance'
        }
        
        # Scenario 3: Aggressive (maximize profit potential)
        aggressive_mask = drawdown_abs > drawdown_abs.quantile(0.7)
        scenarios['aggressive'] = {
            'trade_count': aggressive_mask.sum(),
            'percentage': aggressive_mask.sum() / len(drawdown_abs) * 100,
            'target_sl_max': drawdown_abs[aggressive_mask].quantile(0.9),
            'target_be_range': runup_abs[aggressive_mask].quantile(0.25),
            'target_ts_trigger': runup_abs[aggressive_mask].quantile(0.75),
            'description': 'Higher risk for higher potential reward'
        }
        
        # Print scenario analysis
        for scenario_name, data in scenarios.items():
            print(f"{scenario_name.upper()} SCENARIO: {data['trade_count']} trades ({data['percentage']:.1f}%)")
            print(f"   Target SL Max: {data['target_sl_max']:.2f}%")
            print(f"   Target BE: {data['target_be_range']:.2f}%")
            print(f"   Target TS Trigger: {data['target_ts_trigger']:.2f}%")
            print(f"   {data['description']}")
        
        return scenarios
    
    def _calculate_smart_ranges(self, stats, behaviors, scenarios):
        """Calculate intelligent parameter ranges for grid search optimization"""
        print(f"\n🎯 CALCULATING SMART PARAMETER RANGES")
        print(f"=" * 45)
        
        # Extract key statistics
        runup_stats = stats['runup']
        drawdown_stats = stats['drawdown']
        
        # 1. STOP LOSS RANGES
        # Base SL on drawdown patterns with safety margins
        sl_conservative = max(0.5, drawdown_stats['percentiles']['p50'] * 1.1)  # 10% above median
        sl_balanced = max(sl_conservative + 0.5, drawdown_stats['percentiles']['p75'] * 1.2)  # 20% above 75th percentile
        sl_aggressive = max(sl_balanced + 0.5, drawdown_stats['percentiles']['p90'] * 1.3)  # 30% above 90th percentile
        
        sl_ranges = {
            'conservative': {'min': sl_conservative, 'max': sl_balanced, 'step': 0.5},
            'balanced': {'min': sl_balanced, 'max': sl_aggressive, 'step': 0.5},
            'aggressive': {'min': sl_aggressive, 'max': min(50.0, drawdown_stats['max'] * 1.5), 'step': 1.0}
        }
        
        # 2. BREAKEVEN RANGES
        # Base BE on early run-up patterns
        be_conservative = max(0.2, runup_stats['percentiles']['p25'] * 0.6)  # 60% of 25th percentile
        be_balanced = max(0.3, runup_stats['percentiles']['p50'] * 0.7)  # 70% of median
        be_aggressive = max(0.5, runup_stats['percentiles']['p75'] * 0.8)  # 80% of 75th percentile
        
        be_ranges = {
            'conservative': {'min': be_conservative, 'max': be_balanced, 'step': 0.25},
            'balanced': {'min': be_balanced, 'max': be_aggressive, 'step': 0.25},
            'aggressive': {'min': be_aggressive, 'max': min(10.0, runup_stats['percentiles']['p90']), 'step': 0.5}
        }
        
        # 3. TRAILING STOP RANGES
        # Base TS trigger on run-up patterns where profits typically develop
        ts_conservative = max(0.5, runup_stats['percentiles']['p25'])  # Start at 25th percentile
        ts_balanced = max(0.7, runup_stats['percentiles']['p50'])  # Start at median
        ts_aggressive = max(1.0, runup_stats['percentiles']['p75'])  # Start at 75th percentile
        
        ts_ranges = {
            'conservative': {'min': ts_conservative, 'max': ts_balanced, 'step': 0.5},
            'balanced': {'min': ts_balanced, 'max': ts_aggressive, 'step': 0.5},
            'aggressive': {'min': ts_aggressive, 'max': min(20.0, runup_stats['percentiles']['p90']), 'step': 1.0}
        }
        
        # 4. TRAILING STEP RANGES
        # Base TS step on volatility and typical move sizes
        volatility_factor = runup_stats['std'] / runup_stats['mean'] if runup_stats['mean'] > 0 else 0.5
        
        ts_step_base = max(0.1, runup_stats['percentiles']['p25'] * 0.3)  # 30% of 25th percentile run-up
        ts_step_max = max(ts_step_base * 2, runup_stats['percentiles']['p50'] * 0.4)  # 40% of median run-up
        
        ts_step_ranges = {
            'conservative': {'min': ts_step_base, 'max': ts_step_max, 'step': 0.1},
            'balanced': {'min': ts_step_base, 'max': ts_step_max * 1.5, 'step': 0.2},
            'aggressive': {'min': ts_step_base, 'max': min(5.0, ts_step_max * 2), 'step': 0.3}
        }
        
        # 5. CALCULATE EFFICIENCY GAINS
        efficiency_analysis = self._calculate_efficiency_gains(sl_ranges, be_ranges, ts_ranges, ts_step_ranges)
        
        # Print recommendations
        print(f"📋 SMART PARAMETER RANGES SUMMARY:")
        print(f"\n🛡️ STOP LOSS RANGES:")
        for strategy, range_data in sl_ranges.items():
            print(f"   {strategy.capitalize()}: {range_data['min']:.1f}% - {range_data['max']:.1f}% (step: {range_data['step']})")
        
        print(f"\n⚖️ BREAKEVEN RANGES:")
        for strategy, range_data in be_ranges.items():
            print(f"   {strategy.capitalize()}: {range_data['min']:.2f}% - {range_data['max']:.2f}% (step: {range_data['step']})")
        
        print(f"\n🎯 TRAILING STOP TRIGGER RANGES:")
        for strategy, range_data in ts_ranges.items():
            print(f"   {strategy.capitalize()}: {range_data['min']:.2f}% - {range_data['max']:.2f}% (step: {range_data['step']})")
        
        print(f"\n📏 TRAILING STEP RANGES:")
        for strategy, range_data in ts_step_ranges.items():
            print(f"   {strategy.capitalize()}: {range_data['min']:.2f}% - {range_data['max']:.2f}% (step: {range_data['step']})")
        
        return {
            'sl_ranges': sl_ranges,
            'be_ranges': be_ranges,
            'ts_ranges': ts_ranges,
            'ts_step_ranges': ts_step_ranges,
            'efficiency_analysis': efficiency_analysis
        }
    
    def _calculate_efficiency_gains(self, sl_ranges, be_ranges, ts_ranges, ts_step_ranges):
        """Calculate efficiency gains from smart ranging vs blind search"""
        print(f"\n⚡ EFFICIENCY ANALYSIS:")
        
        # Calculate combinations for each strategy
        combinations = {}
        for strategy in ['conservative', 'balanced', 'aggressive']:
            sl_count = int((sl_ranges[strategy]['max'] - sl_ranges[strategy]['min']) / sl_ranges[strategy]['step']) + 1
            be_count = int((be_ranges[strategy]['max'] - be_ranges[strategy]['min']) / be_ranges[strategy]['step']) + 1
            ts_count = int((ts_ranges[strategy]['max'] - ts_ranges[strategy]['min']) / ts_ranges[strategy]['step']) + 1
            ts_step_count = int((ts_step_ranges[strategy]['max'] - ts_step_ranges[strategy]['min']) / ts_step_ranges[strategy]['step']) + 1
            
            combinations[strategy] = sl_count * be_count * ts_count * ts_step_count
        
        # Typical blind search parameters (example)
        typical_blind_combinations = 20 * 10 * 8 * 6  # 20 SL * 10 BE * 8 TS * 6 TS_step = 9,600
        
        print(f"Smart Range Combinations:")
        total_smart_combinations = 0
        for strategy, combo_count in combinations.items():
            print(f"   {strategy.capitalize()}: {combo_count:,} combinations")
            total_smart_combinations += combo_count
        
        print(f"   Total Smart: {total_smart_combinations:,} combinations")
        print(f"   Typical Blind Search: {typical_blind_combinations:,} combinations")
        
        efficiency_gain = typical_blind_combinations / total_smart_combinations if total_smart_combinations > 0 else 0
        print(f"   Efficiency Gain: {efficiency_gain:.1f}x faster")
        
        return {
            'smart_combinations': combinations,
            'total_smart': total_smart_combinations,
            'typical_blind': typical_blind_combinations,
            'efficiency_gain': efficiency_gain
        }
    
    def generate_final_recommendations(self):
        """Generate final parameter range recommendations for grid search input"""
        if not self.range_analysis:
            self.analyze_price_movement_patterns()
        
        print(f"\n🏆 FINAL RECOMMENDATIONS FOR GRID SEARCH")
        print(f"=" * 50)
        
        ranges = self.range_analysis['recommended_ranges']
        efficiency = ranges['efficiency_analysis']
        
        # Recommend balanced strategy as default
        recommended_strategy = 'balanced'
        sl_rec = ranges['sl_ranges'][recommended_strategy]
        be_rec = ranges['be_ranges'][recommended_strategy]
        ts_rec = ranges['ts_ranges'][recommended_strategy]
        ts_step_rec = ranges['ts_step_ranges'][recommended_strategy]
        
        print(f"🎯 RECOMMENDED STRATEGY: {recommended_strategy.upper()}")
        print(f"📊 Based on {len(self.exit_trades)} completed trades")
        
        print(f"\n📋 GRID SEARCH INPUT PARAMETERS:")
        print(f"   SL Range: {sl_rec['min']:.1f}% to {sl_rec['max']:.1f}% (step: {sl_rec['step']})")
        print(f"   BE Range: {be_rec['min']:.2f}% to {be_rec['max']:.2f}% (step: {be_rec['step']})")
        print(f"   TS Trigger: {ts_rec['min']:.2f}% to {ts_rec['max']:.2f}% (step: {ts_rec['step']})")
        print(f"   TS Step: {ts_step_rec['min']:.2f}% to {ts_step_rec['max']:.2f}% (step: {ts_step_rec['step']})")
        
        print(f"\n⚡ EFFICIENCY BENEFITS:")
        print(f"   Smart combinations: {efficiency['smart_combinations'][recommended_strategy]:,}")
        print(f"   vs Blind search: {efficiency['typical_blind']:,}")
        print(f"   Speed improvement: {efficiency['efficiency_gain']:.1f}x faster")
        
        if self.validation_issues:
            print(f"\n⚠️ DATA QUALITY NOTES:")
            for issue in self.validation_issues:
                print(f"   - {issue}")
        
        print(f"\n🔬 NEXT STEPS:")
        print(f"   1. Use these ranges in your grid search optimizer")
        print(f"   2. Run simulation with actual candle data")
        print(f"   3. Fine-tune based on simulation results")
        print(f"   4. Consider expanding to TP1,2,4 + volume % in future")
        
        return {
            'recommended_strategy': recommended_strategy,
            'parameter_ranges': {
                'sl': sl_rec,
                'be': be_rec, 
                'ts_trigger': ts_rec,
                'ts_step': ts_step_rec
            },
            'efficiency_gain': efficiency['efficiency_gain'],
            'combinations_count': efficiency['smart_combinations'][recommended_strategy],
            'data_quality_issues': self.validation_issues,
            'total_trades_analyzed': len(self.exit_trades)
        }

def main():
    """Test the Smart Range Finder"""
    try:
        # Initialize range finder
        finder = SmartRangeFinder('60-tradelist-LONGSHORT.csv')
        
        # Run analysis
        analysis_results = finder.analyze_price_movement_patterns()
        
        # Generate final recommendations
        recommendations = finder.generate_final_recommendations()
        
        return finder, analysis_results, recommendations
        
    except Exception as e:
        print(f"❌ Smart Range Finder failed: {str(e)}")
        return None, None, None

if __name__ == "__main__":
    finder, analysis, recommendations = main()
