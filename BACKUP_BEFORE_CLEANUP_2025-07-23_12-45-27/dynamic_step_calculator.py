#!/usr/bin/env python3
"""
DYNAMIC STEP CALCULATOR - Statistical Foundation for Parameter Steps
==================================================================

PROBLEM: Current system uses hard-coded step values (0.5, 0.25, 1.0) without statistical basis.
SOLUTION: Calculate optimal step sizes based on actual data distribution and market volatility.

MATHEMATICAL FOUNDATIONS:
1. STATISTICAL RESOLUTION: Step size should capture meaningful price movement differences
2. VARIANCE-BASED SCALING: Higher volatility → larger steps, lower volatility → smaller steps  
3. PERCENTILE DISTRIBUTION: Steps should align with natural data clustering patterns
4. OPTIMIZATION EFFICIENCY: Balance between granularity and computational cost

Created: July 22, 2025
Author: GitHub Copilot Assistant
"""

import pandas as pd
import numpy as np
import math
from datetime import datetime

class DynamicStepCalculator:
    """
    Calculate statistically-optimal step sizes for grid search parameters
    based on actual market data distribution and volatility patterns
    """
    
    def __init__(self, tradelist_file):
        """Initialize with tradelist data"""
        self.tradelist_file = tradelist_file
        self.data = None
        self.statistics = None
        self.step_analysis = None
        self.load_and_validate_data()
    
    def load_and_validate_data(self):
        """Load and validate tradelist data"""
        print(f"📊 DYNAMIC STEP CALCULATOR")
        print(f"=" * 50)
        print(f"Loading data from: {self.tradelist_file}")
        
        try:
            # Read CSV with flexible parsing
            self.data = pd.read_csv(self.tradelist_file)
            print(f"✅ Loaded {len(self.data)} trade records")
            
            # Validate required columns - support multiple formats
            potential_cols = {
                'runup': ['Run-up%', 'Run-up %', 'Runup%', 'Runup %'],
                'drawdown': ['Drawdown%', 'Drawdown %', 'Draw-down%', 'Draw-down %'],
                'pnl': ['P&L%', 'P&L %', 'PnL%', 'PnL %', 'PL%', 'PL %']
            }
            
            # Map actual columns
            column_mapping = {}
            for param_type, possible_names in potential_cols.items():
                found_col = None
                for col_name in possible_names:
                    if col_name in self.data.columns:
                        found_col = col_name
                        break
                
                if found_col:
                    column_mapping[param_type] = found_col
                else:
                    print(f"❌ Missing {param_type} column. Tried: {possible_names}")
                    print(f"Available columns: {list(self.data.columns)}")
                    raise ValueError(f"Required {param_type} column not found")
            
            print(f"✅ Column mapping: {column_mapping}")
            
            # Clean and convert data using mapped columns
            for param_type, col_name in column_mapping.items():
                # Clean percentage and comma formatting
                clean_data = self.data[col_name].astype(str).str.replace('%', '').str.replace(',', '').str.replace('"', '')
                self.data[f'{param_type}_clean'] = pd.to_numeric(clean_data, errors='coerce')
                
                # Debug first few values
                print(f"   {param_type} ({col_name}): {len(self.data[f'{param_type}_clean'].dropna())} valid values")
                print(f"   Sample values: {self.data[f'{param_type}_clean'].dropna().head(3).tolist()}")
            
            # Remove invalid rows
            clean_cols = [f'{param_type}_clean' for param_type in column_mapping.keys()]
            self.data = self.data.dropna(subset=clean_cols)
            print(f"✅ {len(self.data)} valid trades after cleaning")
            
            if len(self.data) < 10:
                raise ValueError("Insufficient data for statistical analysis (need ≥10 trades)")
                
        except Exception as e:
            print(f"❌ Data loading failed: {str(e)}")
            raise
    
    def calculate_statistical_foundations(self):
        """Calculate core statistical metrics for step determination"""
        print(f"\n📈 STATISTICAL FOUNDATION ANALYSIS")
        print(f"-" * 40)
        
        # Extract absolute values for analysis
        runup_abs = self.data['runup_clean'].abs()
        drawdown_abs = self.data['drawdown_clean'].abs()
        pnl_values = self.data['pnl_clean']
        
        # Calculate comprehensive statistics
        self.statistics = {}
        
        for name, series in [('runup', runup_abs), ('drawdown', drawdown_abs), ('pnl', pnl_values)]:
            stats = {
                'mean': series.mean(),
                'median': series.median(),
                'std': series.std(),
                'min': series.min(),
                'max': series.max(),
                'q25': series.quantile(0.25),
                'q75': series.quantile(0.75),
                'iqr': series.quantile(0.75) - series.quantile(0.25),
                'mad': (series - series.median()).abs().mean(),  # Mean Absolute Deviation
                'cv': series.std() / series.mean() if series.mean() > 0 else 0,  # Coefficient of Variation
                'skewness': series.skew(),
                'kurtosis': series.kurtosis()
            }
            
            # Calculate percentile gaps for natural clustering
            percentiles = [5, 10, 25, 50, 75, 90, 95]
            percentile_values = [series.quantile(p/100) for p in percentiles]
            percentile_gaps = [percentile_values[i+1] - percentile_values[i] for i in range(len(percentile_values)-1)]
            
            stats['percentile_gaps'] = {
                'p5_p10': percentile_gaps[0],
                'p10_p25': percentile_gaps[1], 
                'p25_p50': percentile_gaps[2],
                'p50_p75': percentile_gaps[3],
                'p75_p90': percentile_gaps[4],
                'p90_p95': percentile_gaps[5],
                'median_gap': np.median(percentile_gaps),
                'mean_gap': np.mean(percentile_gaps)
            }
            
            self.statistics[name] = stats
            
            # Print key statistics
            print(f"\n{name.upper()} STATISTICS:")
            print(f"   Mean: {stats['mean']:.3f}, Median: {stats['median']:.3f}, Std: {stats['std']:.3f}")
            print(f"   IQR: {stats['iqr']:.3f}, MAD: {stats['mad']:.3f}, CV: {stats['cv']:.3f}")
            print(f"   Median Gap: {stats['percentile_gaps']['median_gap']:.3f}")
            print(f"   Key Gaps: P25-P50={stats['percentile_gaps']['p25_p50']:.3f}, P50-P75={stats['percentile_gaps']['p50_p75']:.3f}")
    
    def calculate_optimal_steps(self):
        """Calculate statistically-optimal step sizes using multiple methodologies"""
        print(f"\n🎯 OPTIMAL STEP CALCULATION")
        print(f"-" * 35)
        
        if not self.statistics:
            self.calculate_statistical_foundations()
        
        self.step_analysis = {}
        
        # METHOD 1: VARIANCE-BASED STEPS
        # Step size proportional to standard deviation and range
        for param_type in ['runup', 'drawdown']:
            stats = self.statistics[param_type]
            
            # Multiple calculation methods
            methods = {
                'std_fraction': stats['std'] * 0.5,  # Half standard deviation
                'iqr_fraction': stats['iqr'] * 0.25,  # Quarter of IQR  
                'mad_based': stats['mad'] * 0.6,  # 60% of Mean Absolute Deviation
                'percentile_gap': stats['percentile_gaps']['median_gap'],  # Natural clustering
                'cv_scaled': stats['mean'] * stats['cv'] * 0.3,  # Coefficient of variation scaled
                'range_fraction': (stats['q75'] - stats['q25']) * 0.2  # 20% of middle range
            }
            
            # Calculate statistical bounds for each method
            step_values = list(methods.values())
            step_median = np.median(step_values)
            step_mean = np.mean(step_values)
            step_std = np.std(step_values)
            
            # INTELLIGENT STEP SELECTION based on data characteristics
            if stats['cv'] < 0.5:  # Low volatility data
                optimal_step = min(methods['iqr_fraction'], methods['mad_based'])
                reasoning = "Low volatility → Fine-grained steps for precision"
            elif stats['cv'] > 1.5:  # High volatility data  
                optimal_step = max(methods['std_fraction'], methods['percentile_gap'])
                reasoning = "High volatility → Coarser steps for efficiency"
            else:  # Moderate volatility
                optimal_step = step_median
                reasoning = "Moderate volatility → Median of multiple methods"
            
            # Ensure reasonable bounds
            min_step = 0.05 if param_type == 'runup' else 0.1  # BE more precise than SL
            max_step = stats['iqr'] * 0.5  # Don't exceed half IQR
            optimal_step = max(min_step, min(optimal_step, max_step))
            
            # Round to reasonable precision
            if optimal_step < 0.1:
                optimal_step = round(optimal_step, 3)
            elif optimal_step < 1.0:
                optimal_step = round(optimal_step, 2) 
            else:
                optimal_step = round(optimal_step, 1)
            
            self.step_analysis[param_type] = {
                'methods': methods,
                'optimal_step': optimal_step,
                'reasoning': reasoning,
                'statistics': {
                    'median': step_median,
                    'mean': step_mean,
                    'std': step_std
                },
                'bounds': {
                    'min_step': min_step,
                    'max_step': max_step
                }
            }
            
            print(f"\n{param_type.upper()} STEP ANALYSIS:")
            print(f"   Statistical Methods:")
            for method, value in methods.items():
                print(f"     {method}: {value:.3f}")
            print(f"   Optimal Step: {optimal_step:.3f}")
            print(f"   Reasoning: {reasoning}")
    
    def calculate_parameter_specific_steps(self):
        """Calculate specific steps for SL, BE, TS parameters with market logic"""
        print(f"\n🔧 PARAMETER-SPECIFIC STEP CALCULATION")
        print(f"-" * 42)
        
        if not self.step_analysis:
            self.calculate_optimal_steps()
        
        # Extract base step calculations
        runup_step = self.step_analysis['runup']['optimal_step']
        drawdown_step = self.step_analysis['drawdown']['optimal_step']
        
        # STOP LOSS STEPS - Based on drawdown analysis with safety margin
        sl_base_step = drawdown_step
        sl_conservative_step = max(0.2, sl_base_step * 0.8)  # Finer for conservative
        sl_balanced_step = sl_base_step  # Standard step
        sl_aggressive_step = sl_base_step * 1.5  # Coarser for aggressive
        
        # BREAKEVEN STEPS - Based on early run-up patterns (finer precision needed)
        be_base_step = runup_step * 0.6  # Finer than TS trigger (early movement)
        be_conservative_step = max(0.1, be_base_step * 0.8)
        be_balanced_step = be_base_step
        be_aggressive_step = be_base_step * 1.3
        
        # TRAILING STOP TRIGGER STEPS - Based on run-up analysis
        ts_trigger_base_step = runup_step
        ts_trigger_conservative_step = max(0.2, ts_trigger_base_step * 0.9)
        ts_trigger_balanced_step = ts_trigger_base_step
        ts_trigger_aggressive_step = ts_trigger_base_step * 1.4
        
        # TRAILING STOP STEP - Based on volatility and typical move sizes
        volatility_factor = self.statistics['runup']['cv']
        ts_step_base = runup_step * 0.4 * (1 + volatility_factor)  # Adjust for volatility
        ts_step_conservative_step = max(0.05, ts_step_base * 0.7)
        ts_step_balanced_step = ts_step_base
        ts_step_aggressive_step = ts_step_base * 1.6
        
        # Round all steps to appropriate precision
        def smart_round(value):
            if value < 0.1:
                return round(value, 3)
            elif value < 1.0:
                return round(value, 2)
            else:
                return round(value, 1)
        
        parameter_steps = {
            'sl_steps': {
                'conservative': smart_round(sl_conservative_step),
                'balanced': smart_round(sl_balanced_step), 
                'aggressive': smart_round(sl_aggressive_step),
                'base_calculation': f"Drawdown step ({drawdown_step:.3f}) with safety margins"
            },
            'be_steps': {
                'conservative': smart_round(be_conservative_step),
                'balanced': smart_round(be_balanced_step),
                'aggressive': smart_round(be_aggressive_step),
                'base_calculation': f"60% of run-up step ({runup_step:.3f}) for early precision"
            },
            'ts_trigger_steps': {
                'conservative': smart_round(ts_trigger_conservative_step),
                'balanced': smart_round(ts_trigger_balanced_step),
                'aggressive': smart_round(ts_trigger_aggressive_step), 
                'base_calculation': f"Run-up step ({runup_step:.3f}) for profit development"
            },
            'ts_step_steps': {
                'conservative': smart_round(ts_step_conservative_step),
                'balanced': smart_round(ts_step_balanced_step),
                'aggressive': smart_round(ts_step_aggressive_step),
                'base_calculation': f"40% of run-up step * (1 + CV={volatility_factor:.2f}) for volatility adjustment"
            }
        }
        
        # Print results with reasoning
        for param_name, param_data in parameter_steps.items():
            print(f"\n{param_name.upper().replace('_', ' ')}:")
            print(f"   Conservative: {param_data['conservative']}")
            print(f"   Balanced: {param_data['balanced']}")
            print(f"   Aggressive: {param_data['aggressive']}")
            print(f"   Logic: {param_data['base_calculation']}")
        
        return parameter_steps
    
    def validate_step_effectiveness(self, parameter_steps):
        """Validate step sizes against actual data distribution"""
        print(f"\n✅ STEP EFFECTIVENESS VALIDATION")
        print(f"-" * 35)
        
        validation_results = {}
        
        # Test step sizes against actual data clustering
        for param_type in ['runup', 'drawdown']:
            data_series = self.data['runup_clean'].abs() if param_type == 'runup' else self.data['drawdown_clean'].abs()
            
            # Get corresponding step sizes
            if param_type == 'runup':
                test_steps = {
                    'be_balanced': parameter_steps['be_steps']['balanced'],
                    'ts_trigger_balanced': parameter_steps['ts_trigger_steps']['balanced'],
                    'ts_step_balanced': parameter_steps['ts_step_steps']['balanced']
                }
            else:  # drawdown
                test_steps = {
                    'sl_balanced': parameter_steps['sl_steps']['balanced']
                }
            
            for step_name, step_value in test_steps.items():
                # Calculate how well step captures data variation
                data_range = data_series.max() - data_series.min()
                num_steps_in_range = data_range / step_value
                
                # Calculate data points per step
                data_points_per_step = len(data_series) / num_steps_in_range
                
                # Assess effectiveness
                if data_points_per_step < 2:
                    effectiveness = "Too fine - may overfit"
                elif data_points_per_step > 10:
                    effectiveness = "Too coarse - may miss optimal values"
                else:
                    effectiveness = "Good balance"
                
                validation_results[step_name] = {
                    'step_value': step_value,
                    'steps_in_range': num_steps_in_range,
                    'data_points_per_step': data_points_per_step,
                    'effectiveness': effectiveness
                }
                
                print(f"\n{step_name.upper()}:")
                print(f"   Step size: {step_value}")
                print(f"   Steps in data range: {num_steps_in_range:.1f}")
                print(f"   Data points per step: {data_points_per_step:.1f}")
                print(f"   Assessment: {effectiveness}")
        
        return validation_results
    
    def generate_comprehensive_report(self):
        """Generate complete analysis report with statistical justification"""
        print(f"\n📋 COMPREHENSIVE STEP CALCULATION REPORT")
        print(f"=" * 50)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Data source: {self.tradelist_file}")
        print(f"Total trades analyzed: {len(self.data)}")
        
        # Run full analysis
        self.calculate_statistical_foundations()
        parameter_steps = self.calculate_parameter_specific_steps()
        validation = self.validate_step_effectiveness(parameter_steps)
        
        # SUMMARY OF MATHEMATICAL FOUNDATIONS
        print(f"\n🔬 MATHEMATICAL FOUNDATIONS:")
        print(f"   1. Statistical Distribution Analysis: Percentile gaps, IQR, MAD")
        print(f"   2. Volatility-Based Scaling: Coefficient of variation adjustment")
        print(f"   3. Market Logic Integration: Early/late movement characteristics")
        print(f"   4. Precision Optimization: Balance granularity vs efficiency")
        
        # COMPARISON WITH HARD-CODED STEPS
        print(f"\n📊 COMPARISON: STATISTICAL vs HARD-CODED STEPS")
        print(f"-" * 45)
        
        comparisons = [
            ('SL Balanced', parameter_steps['sl_steps']['balanced'], 0.5, 'Stop Loss'),
            ('BE Balanced', parameter_steps['be_steps']['balanced'], 0.25, 'Breakeven'),
            ('TS Trigger Balanced', parameter_steps['ts_trigger_steps']['balanced'], 0.5, 'Trailing Stop Trigger'),
            ('TS Step Balanced', parameter_steps['ts_step_steps']['balanced'], 0.2, 'Trailing Stop Step')
        ]
        
        total_improvement = 0
        for param_name, stat_step, hard_step, description in comparisons:
            improvement = abs(stat_step - hard_step) / hard_step * 100
            total_improvement += improvement
            
            print(f"{param_name}:")
            print(f"   Statistical: {stat_step} vs Hard-coded: {hard_step}")
            print(f"   Difference: {improvement:.1f}% ({description})")
        
        avg_improvement = total_improvement / len(comparisons)
        print(f"\nAverage parameter improvement: {avg_improvement:.1f}%")
        
        # FINAL RECOMMENDATIONS
        print(f"\n🎯 FINAL STATISTICAL RECOMMENDATIONS:")
        print(f"-" * 40)
        for param_type, steps in parameter_steps.items():
            print(f"\n{param_type.upper().replace('_', ' ')}:")
            print(f"   Conservative: {steps['conservative']} | Balanced: {steps['balanced']} | Aggressive: {steps['aggressive']}")
            print(f"   Mathematical Basis: {steps['base_calculation']}")
        
        return {
            'parameter_steps': parameter_steps,
            'validation_results': validation,
            'statistical_foundations': self.statistics,
            'improvement_metrics': {
                'avg_parameter_improvement': avg_improvement,
                'total_trades_analyzed': len(self.data)
            }
        }

def main():
    """Test the Dynamic Step Calculator"""
    try:
        # Initialize calculator
        calculator = DynamicStepCalculator('60-tradelist-LONGSHORT.csv')
        
        # Generate comprehensive report
        report = calculator.generate_comprehensive_report()
        
        print(f"\n✅ DYNAMIC STEP CALCULATION COMPLETE!")
        print(f"Mathematical foundation established for all parameter steps.")
        
        return calculator, report
        
    except Exception as e:
        print(f"❌ Dynamic Step Calculator failed: {str(e)}")
        return None, None

if __name__ == "__main__":
    calculator, report = main()
