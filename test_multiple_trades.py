#!/usr/bin/env python3
"""
🧪 MULTI-TRADE REALITY TEST
Test reality check optimizer với multiple trades
"""

from reality_check_optimizer import RealityCheckOptimizer

def test_multiple_trades():
    """Test với nhiều trades khác nhau"""
    
    print("🧪 MULTI-TRADE REALITY TEST")
    print("=" * 50)
    
    optimizer = RealityCheckOptimizer("data chart full info.csv")
    
    # Test configs with different trades
    trade_configs = [
        {
            'entry_time': '2025-06-20 22:00:00',
            'exit_time': '2025-06-21 08:30:00', 
            'entry_price': 0.009937,
            'side': 'SHORT',
            'name': 'Trade #139 (Original Bug)'
        },
        {
            'entry_time': '2025-06-19 10:00:00',
            'exit_time': '2025-06-19 16:00:00',
            'entry_price': 0.010150,
            'side': 'SHORT', 
            'name': 'Test Trade #1'
        },
        {
            'entry_time': '2025-06-18 14:00:00',
            'exit_time': '2025-06-18 20:00:00',
            'entry_price': 0.009800,
            'side': 'LONG',
            'name': 'Test Trade #2 (LONG)'
        }
    ]
    
    param_ranges = {
        'sl': [2.0, 3.0, 4.0],
        'be': [1.0, 1.5], 
        'ts_trig': [2.5, 3.0, 3.5],
        'ts_step': [0.2, 0.3]
    }
    
    for trade_config in trade_configs:
        print(f"\n🎯 TESTING: {trade_config['name']}")
        print("-" * 40)
        
        # Test single trade
        single_trade_config = [trade_config]
        
        try:
            results = optimizer.optimize_parameters(single_trade_config, param_ranges)
            
            if results:
                best = results[0]
                print(f"   ✅ Best Result: {best['avg_profit']:.2f}% profit")
                print(f"   🎯 Reality Score: {best['realism_score']:.1%}")
                print(f"   📊 Parameters: SL={best['sl']}% BE={best['be']}% TS={best['ts_trig']}%")
                
                if best['realism_score'] < 0.8:
                    print(f"   🚨 WARNING: Low reality score!")
                else:
                    print(f"   ✅ REALISTIC: High confidence result")
            else:
                print(f"   ❌ No valid results for this trade")
                
        except Exception as e:
            print(f"   ❌ Error testing trade: {e}")
    
    print(f"\n✅ MULTI-TRADE TEST COMPLETE!")

if __name__ == '__main__':
    test_multiple_trades()
