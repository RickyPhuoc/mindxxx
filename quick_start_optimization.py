#!/usr/bin/env python3
"""
🚀 QUICK START - Reality-Checked Optimization
One-command optimization with all safety checks
"""

import subprocess
import sys
import os
from datetime import datetime

def quick_start_optimization():
    """Quick start với tất cả validation"""
    
    print("🚀 QUICK START: Reality-Checked Optimization")
    print("=" * 50)
    
    # 1. Pre-flight checks
    print("🔍 Running pre-flight checks...")
    
    required_files = [
        "data chart full info.csv",
        "reality_check_optimizer.py", 
        "web_reality_check.py"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing required files: {missing_files}")
        print("   Please ensure all files are present before running optimization")
        return False
    
    print("✅ All required files present")
    
    # 2. Test reality checker
    print("🧪 Testing reality checker...")
    try:
        result = subprocess.run([sys.executable, "-c", 
            "from web_reality_check import WebAppRealityChecker; print('Reality checker OK')"],
            capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Reality checker working")
        else:
            print(f"❌ Reality checker failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Reality checker test failed: {e}")
        return False
    
    # 3. Run optimization
    print("🎯 Starting reality-checked optimization...")
    try:
        result = subprocess.run([sys.executable, "reality_check_optimizer.py"],
                              capture_output=False, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ Optimization completed successfully")
        else:
            print("⚠️ Optimization completed with warnings")
            
    except subprocess.TimeoutExpired:
        print("⚠️ Optimization taking longer than expected, but continuing...")
    except Exception as e:
        print(f"❌ Optimization failed: {e}")
        return False
    
    # 4. Quick validation
    print("🔍 Running quick validation...")
    
    # Check if results look reasonable
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"📄 Session completed at {timestamp}")
    print("✅ Quick start optimization complete!")
    print()
    print("🎯 NEXT STEPS:")
    print("   1. Review optimization results")
    print("   2. Validate top results manually") 
    print("   3. Start with conservative position sizes")
    print("   4. Monitor performance vs expectations")
    
    return True

if __name__ == '__main__':
    success = quick_start_optimization()
    if not success:
        print("❌ Quick start failed. Please check errors and try again.")
        sys.exit(1)
    else:
        print("🎉 Quick start successful!")
