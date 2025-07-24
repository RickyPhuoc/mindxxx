#!/usr/bin/env python3
"""
SMART PARAMETER ANALYZER
Phân tích tradelist để đưa ra dải parameters tối ưu cho optimization
Thay vì quét mù mẫn, ta sử dụng thống kê từ Run-up, Drawdown để khoanh vùng
"""

import pandas as pd
import numpy as np
import math

def analyze_tradelist_for_smart_ranges(tradelist_path):
    """
    Phân tích tradelist để đưa ra dải parameters thông minh
    
    Returns:
    {
        'sl_range': {'min': x, 'max': y, 'step': z},
        'be_range': {'min': x, 'max': y, 'step': z}, 
        'ts_range': {'min': x, 'max': y, 'step': z},
        'analysis': {...}
    }
    """
    print(f"🔍 SMART ANALYSIS: Loading {tradelist_path}")
    
    # Load data with proper parsing
    df = pd.read_csv(tradelist_path)
    
    # Clean column names
    df.columns = [col.strip().lower().replace(' ', '_').replace('/', '_').replace('#', '').replace('&', '') for col in df.columns]
    
    print(f"📊 Columns found: {df.columns.tolist()}")
    
    # Extract key columns with flexible naming
    runup_col = None
    drawdown_col = None
    pnl_col = None
    
    for col in df.columns:
        if 'run' in col and '%' in col:
            runup_col = col
        elif 'drawdown' in col and '%' in col:
            drawdown_col = col
        elif 'pl_%' in col or 'p_l_%' in col:
            pnl_col = col
    
    if not all([runup_col, drawdown_col, pnl_col]):
        print(f"⚠️ Missing key columns! Found: runup={runup_col}, drawdown={drawdown_col}, pnl={pnl_col}")
        return None
    
    print(f"✅ Key columns: {runup_col}, {drawdown_col}, {pnl_col}")
    
    # Clean and convert percentage columns
    for col in [runup_col, drawdown_col, pnl_col]:
        df[col] = df[col].astype(str).str.replace('%', '').str.replace(',', '')
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Filter for complete trades (Exit entries only)
    exit_trades = df[df['type'].str.lower().str.contains('exit')].copy()
    
    print(f"📈 Analyzing {len(exit_trades)} completed trades...")
    
    # Basic statistics
    runup_stats = {
        'mean': exit_trades[runup_col].mean(),
        'median': exit_trades[runup_col].median(),
        'std': exit_trades[runup_col].std(),
        'p25': exit_trades[runup_col].quantile(0.25),
        'p75': exit_trades[runup_col].quantile(0.75),
        'p90': exit_trades[runup_col].quantile(0.90),
        'max': exit_trades[runup_col].max()
    }
    
    drawdown_stats = {
        'mean': abs(exit_trades[drawdown_col].mean()),
        'median': abs(exit_trades[drawdown_col].median()),
        'std': exit_trades[drawdown_col].std(),
        'p25': abs(exit_trades[drawdown_col].quantile(0.25)),
        'p75': abs(exit_trades[drawdown_col].quantile(0.75)),
        'p90': abs(exit_trades[drawdown_col].quantile(0.90)),
        'max': abs(exit_trades[drawdown_col].min())  # min because drawdown is negative
    }
    
    pnl_stats = {
        'mean': exit_trades[pnl_col].mean(),
        'median': exit_trades[pnl_col].median(),
        'positive_rate': (exit_trades[pnl_col] > 0).mean() * 100
    }
    
    print(f"📊 RUN-UP STATS:")
    print(f"   Mean: {runup_stats['mean']:.2f}%, Median: {runup_stats['median']:.2f}%")
    print(f"   75th percentile: {runup_stats['p75']:.2f}%, 90th: {runup_stats['p90']:.2f}%")
    print(f"   Max: {runup_stats['max']:.2f}%")
    
    print(f"📊 DRAWDOWN STATS:")
    print(f"   Mean: {drawdown_stats['mean']:.2f}%, Median: {drawdown_stats['median']:.2f}%")
    print(f"   75th percentile: {drawdown_stats['p75']:.2f}%, 90th: {drawdown_stats['p90']:.2f}%")
    print(f"   Max: {drawdown_stats['max']:.2f}%")
    
    print(f"📊 P&L STATS:")
    print(f"   Mean: {pnl_stats['mean']:.2f}%, Win rate: {pnl_stats['positive_rate']:.1f}%")
    
    # SMART PARAMETER CALCULATION
    
    # 1. SL Range: Based on drawdown analysis
    # SL should be higher than typical drawdown but not so high that it never triggers
    sl_min = max(0.5, drawdown_stats['p25'])  # Start from 25th percentile
    sl_max = max(sl_min + 0.5, min(15.0, drawdown_stats['p90'] * 1.5))  # Ensure max > min
    sl_step = 0.5 if sl_max <= 5 else 1.0
    
    # 2. BE Range: Based on run-up analysis  
    # BE should be set where trades typically show profit
    be_min = max(0.5, runup_stats['p25'] * 0.5)  # Half of 25th percentile run-up
    be_max = min(5.0, runup_stats['median'])  # Up to median run-up
    be_step = 0.25 if be_max <= 2 else 0.5
    
    # 3. TS Range: Based on run-up patterns
    # TS trigger should be where significant profit starts
    ts_trig_min = max(0.5, runup_stats['p25'])  # 25th percentile run-up
    ts_trig_max = min(8.0, runup_stats['p75'])  # 75th percentile run-up  
    ts_trig_step = 0.5
    
    # TS step should be reasonable portion of typical moves
    ts_step_min = 0.2
    ts_step_max = min(2.0, runup_stats['median'] * 0.3)  # 30% of median run-up
    ts_step_step = 0.2
    
    # Risk assessment
    risk_level = "LOW"
    if drawdown_stats['p90'] > 8:
        risk_level = "HIGH"
    elif drawdown_stats['p90'] > 5:
        risk_level = "MEDIUM"
    
    # Profit potential assessment
    profit_potential = "LOW"
    if runup_stats['p75'] > 8:
        profit_potential = "HIGH"
    elif runup_stats['p75'] > 4:
        profit_potential = "MEDIUM"
    
    results = {
        'sl_range': {
            'min': round(sl_min, 1),
            'max': round(sl_max, 1), 
            'step': sl_step,
            'recommended': round(drawdown_stats['median'] * 1.2, 1)  # 20% above median drawdown
        },
        'be_range': {
            'min': round(be_min, 2),
            'max': round(be_max, 2),
            'step': be_step,
            'recommended': round(runup_stats['p25'], 2)
        },
        'ts_trig_range': {
            'min': round(ts_trig_min, 1),
            'max': round(ts_trig_max, 1),
            'step': ts_trig_step,
            'recommended': round(runup_stats['median'], 1)
        },
        'ts_step_range': {
            'min': ts_step_min,
            'max': round(ts_step_max, 1),
            'step': ts_step_step,
            'recommended': round(runup_stats['median'] * 0.2, 1)
        },
        'analysis': {
            'total_trades': len(exit_trades),
            'win_rate': pnl_stats['positive_rate'],
            'avg_runup': runup_stats['mean'],
            'avg_drawdown': drawdown_stats['mean'],
            'risk_level': risk_level,
            'profit_potential': profit_potential,
            'runup_stats': runup_stats,
            'drawdown_stats': drawdown_stats,
            'suggested_focus': []
        }
    }
    
    # Strategic recommendations
    if pnl_stats['positive_rate'] < 50:
        results['analysis']['suggested_focus'].append("Focus on SL optimization - low win rate")
    
    if runup_stats['p75'] > drawdown_stats['p75'] * 2:
        results['analysis']['suggested_focus'].append("Good TS potential - high run-ups vs drawdowns")
    
    if drawdown_stats['p90'] < 3:
        results['analysis']['suggested_focus'].append("Conservative strategy - tight ranges recommended")
    
    return results

def print_smart_recommendations(results):
    """Pretty print smart recommendations"""
    if not results:
        print("❌ No analysis results available")
        return
    
    analysis = results['analysis']
    
    print(f"\n🎯 SMART PARAMETER RECOMMENDATIONS")
    print(f"=" * 50)
    print(f"📊 Strategy Profile:")
    print(f"   Trades analyzed: {analysis['total_trades']}")
    print(f"   Win rate: {analysis['win_rate']:.1f}%")
    print(f"   Risk level: {analysis['risk_level']}")
    print(f"   Profit potential: {analysis['profit_potential']}")
    
    print(f"\n🛡️ STOP LOSS:")
    sl = results['sl_range']
    print(f"   Range: {sl['min']}% - {sl['max']}% (step: {sl['step']}%)")
    print(f"   💡 Recommended: {sl['recommended']}%")
    
    print(f"\n⚖️ BREAKEVEN:")
    be = results['be_range']
    print(f"   Range: {be['min']}% - {be['max']}% (step: {be['step']}%)")
    print(f"   💡 Recommended: {be['recommended']}%")
    
    print(f"\n📈 TRAILING STOP:")
    ts_trig = results['ts_trig_range']
    ts_step = results['ts_step_range']
    print(f"   Trigger: {ts_trig['min']}% - {ts_trig['max']}% (step: {ts_trig['step']}%)")
    print(f"   💡 Recommended trigger: {ts_trig['recommended']}%")
    print(f"   Step: {ts_step['min']}% - {ts_step['max']}% (step: {ts_step['step']}%)")
    print(f"   💡 Recommended step: {ts_step['recommended']}%")
    
    if analysis['suggested_focus']:
        print(f"\n💡 STRATEGIC FOCUS:")
        for focus in analysis['suggested_focus']:
            print(f"   • {focus}")
    
    print(f"\n🎪 ESTIMATED COMBINATIONS:")
    sl_combos = len(np.arange(sl['min'], sl['max'] + sl['step']/2, sl['step']))
    be_combos = len(np.arange(be['min'], be['max'] + be['step']/2, be['step']))
    ts_trig_combos = len(np.arange(ts_trig['min'], ts_trig['max'] + ts_trig['step']/2, ts_trig['step']))
    ts_step_combos = len(np.arange(ts_step['min'], ts_step['max'] + ts_step['step']/2, ts_step['step']))
    
    total_combos = sl_combos * be_combos * ts_trig_combos * ts_step_combos
    print(f"   Total combinations: {total_combos:,}")
    print(f"   vs. Blind scan 1%-15% (step 0.5%): {29*8*15*10:,} combinations")
    if total_combos > 0:
        print(f"   🎯 Efficiency gain: {(29*8*15*10)/total_combos:.1f}x faster!")
    else:
        print(f"   🎯 Note: Very tight ranges detected")

if __name__ == "__main__":
    # Test with available tradelist
    tradelist_file = "60-tradelist-LONGSHORT.csv"
    
    print("🚀 SMART PARAMETER ANALYSIS")
    print("=" * 50)
    
    results = analyze_tradelist_for_smart_ranges(tradelist_file)
    
    if results:
        print_smart_recommendations(results)
    else:
        print("❌ Analysis failed - check file format")
