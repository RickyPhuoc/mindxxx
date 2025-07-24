#!/usr/bin/env python3
"""
🧹 WORKSPACE CLEANUP TOOL - Safe cleanup for Trading Optimization System
Dọn dẹp workspace một cách an toàn, chỉ giữ lại các file cần thiết

BACKUP TRƯỚC KHI CHẠY: Hệ thống sẽ tự động tạo backup của các file quan trọng
"""

import os
import shutil
from datetime import datetime
import json

# 🔒 ESSENTIAL FILES - KHÔNG ĐƯỢC XÓA
ESSENTIAL_FILES = {
    # Core Application Files
    'web_app.py': 'Main Flask application',
    'backtest_gridsearch_slbe_ts_Version3.py': 'Advanced simulation engine', 
    'backtest_realistic_engine.py': 'Realistic trading engine',
    
    # Configuration & Dependencies
    'requirements.txt': 'Python dependencies',
    'BTC.code-workspace': 'VS Code workspace settings',
    
    # Emergency Tools
    'emergency_server.py': 'Emergency backup server',
    'EMERGENCY_START.bat': 'Emergency start script',
    'QUICK_START.bat': 'Quick start script',
    'start_server.bat': 'Server start script',
    'start_server_enhanced.bat': 'Enhanced server start script',
    'run_server.py': 'Alternative server runner',
    
    # Core Supporting Scripts
    'smart_parameter_analyzer.py': 'Smart parameter analysis',
    'smart_range_finder.py': 'Smart range finding',
    'dynamic_step_calculator.py': 'Dynamic step calculation',
    'integration_plan.py': 'Integration planning',
    'validation_suite.py': 'Validation suite',
}

# 🌐 ESSENTIAL DIRECTORIES - KHÔNG ĐƯỢC XÓA
ESSENTIAL_DIRS = {
    'templates': 'Web interface templates',
    'BACKUP_SAFE_2025-07-22_18-05-28': 'Critical backup folder',
    'web_backtest': 'Alternative web interface',
}

# 📊 SAMPLE DATA FILES - GIỮ LẠI VÀI FILE MẪU
SAMPLE_DATA_KEEP = {
    # Trade data samples
    '30-tradelist-BS4.csv': 'Sample trade data 30min',
    '60-tradelist-LONGSHORT.csv': 'Sample trade data 60min', 
    'M5-tradelist-BSATR.csv': 'Sample trade data 5min',
    
    # Candle data samples
    'BINANCE_BTCUSDT, 60.csv': 'BTC candle data 60min',
    'BINANCE_BTCUSDT.P, 30.csv': 'BTC perpetual candle data 30min',
    'BINANCE_BTCUSDT.P, 5.csv': 'BTC perpetual candle data 5min',
    'BINANCE_BOMEUSDT.P, 240.csv': 'BOME candle data 4h',
    
    # Result samples
    'slbe_ts_opt_log.csv': 'Optimization log sample',
    'slbe_ts_opt_results.csv': 'Optimization results sample',
}

# 📋 DOCUMENTATION FILES - GIỮ LẠI
DOCUMENTATION_KEEP = {
    'README_DEPLOYMENT.md': 'Deployment guide',
    'BACKUP_GUIDE.md': 'Backup guide',
    'FINAL_BACKUP_CHECKLIST.md': 'Final backup checklist',
    'MISSING_FILES_REPORT.md': 'Missing files report',
    'WORKSPACE_CLEANUP.md': 'Workspace cleanup guide',
    'WORKSPACE_CLEANUP_FINAL.md': 'Final workspace cleanup guide',
    'SMART_RANGE_FINDER_SOLUTION.md': 'Smart range finder documentation',
    'STEP_LOGIC_ANALYSIS.md': 'Step logic analysis',
}

# 🗑️ FILES TO DELETE - CÁC FILE CÓ THỂ XÓA AN TOÀN
FILES_TO_DELETE = [
    # Test files - có thể xóa an toàn
    'test_*.py',
    'verify_*.py',
    'analyze_*.py',
    'advanced_smart_analyzer.py',
    
    # Temporary output files
    'step_output.txt',
    'TaoQuan_Strategy_Tester_*.csv',
    'TaoQuan_Strategy_Tester_*.xlsx',
    
    # Python cache
    '__pycache__',
    '*.pyc',
    '*.pyo',
]

# 📁 DIRECTORIES TO DELETE - CÁC THỦ MỤC CÓ THỂ XÓA
DIRS_TO_DELETE = [
    '__pycache__',
    '.pytest_cache',
    '.venv_new',  # Virtual environment có thể tái tạo
]

def create_backup_before_cleanup():
    """Tạo backup trước khi dọn dẹp"""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_dir = f"BACKUP_BEFORE_CLEANUP_{timestamp}"
    
    print(f"🛡️ Creating backup: {backup_dir}")
    
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    # Backup essential files
    backup_count = 0
    for filename in ESSENTIAL_FILES.keys():
        if os.path.exists(filename):
            shutil.copy2(filename, backup_dir)
            backup_count += 1
    
    # Backup essential directories
    for dirname in ESSENTIAL_DIRS.keys():
        if os.path.exists(dirname):
            shutil.copytree(dirname, os.path.join(backup_dir, dirname), dirs_exist_ok=True)
            backup_count += 1
    
    print(f"✅ Backup created: {backup_count} items backed up to {backup_dir}")
    return backup_dir

def analyze_workspace():
    """Phân tích workspace hiện tại"""
    print("🔍 Analyzing current workspace...")
    
    all_files = []
    all_dirs = []
    
    for root, dirs, files in os.walk('.'):
        # Skip virtual environment and backup directories
        dirs[:] = [d for d in dirs if not d.startswith('.venv') and not d.startswith('BACKUP_')]
        
        for file in files:
            if not file.endswith('.pyc'):
                all_files.append(os.path.join(root, file))
        
        for dir in dirs:
            all_dirs.append(os.path.join(root, dir))
    
    print(f"📊 Current workspace:")
    print(f"   Files: {len(all_files)}")
    print(f"   Directories: {len(all_dirs)}")
    
    return all_files, all_dirs

def categorize_files(all_files):
    """Phân loại files theo mức độ quan trọng"""
    essential = []
    sample_data = []
    documentation = []
    test_files = []
    temp_files = []
    other_files = []
    
    for file_path in all_files:
        filename = os.path.basename(file_path)
        
        # Remove .\ prefix if present
        if file_path.startswith('.\\'):
            file_path = file_path[2:]
        
        if filename in ESSENTIAL_FILES:
            essential.append(file_path)
        elif filename in SAMPLE_DATA_KEEP:
            sample_data.append(file_path)
        elif filename in DOCUMENTATION_KEEP:
            documentation.append(file_path)
        elif filename.startswith('test_') or filename.startswith('verify_') or filename.startswith('analyze_'):
            test_files.append(file_path)
        elif (filename.endswith('.txt') and 'output' in filename) or filename.startswith('TaoQuan_'):
            temp_files.append(file_path)
        else:
            other_files.append(file_path)
    
    return {
        'essential': essential,
        'sample_data': sample_data, 
        'documentation': documentation,
        'test_files': test_files,
        'temp_files': temp_files,
        'other_files': other_files
    }

def safe_delete_file(file_path):
    """Xóa file một cách an toàn"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
    except Exception as e:
        print(f"⚠️ Could not delete {file_path}: {e}")
        return False
    return False

def safe_delete_directory(dir_path):
    """Xóa thư mục một cách an toàn"""
    try:
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            shutil.rmtree(dir_path)
            return True
    except Exception as e:
        print(f"⚠️ Could not delete directory {dir_path}: {e}")
        return False
    return False

def interactive_cleanup():
    """Dọn dẹp tương tác với người dùng"""
    print("🧹 INTERACTIVE WORKSPACE CLEANUP")
    print("=" * 50)
    
    # Analyze workspace
    all_files, all_dirs = analyze_workspace()
    categories = categorize_files(all_files)
    
    # Show categories
    print(f"\n📋 File Categories:")
    print(f"   🔒 Essential files: {len(categories['essential'])}")
    print(f"   📊 Sample data: {len(categories['sample_data'])}")
    print(f"   📋 Documentation: {len(categories['documentation'])}") 
    print(f"   🧪 Test files: {len(categories['test_files'])}")
    print(f"   🗑️ Temp files: {len(categories['temp_files'])}")
    print(f"   ❓ Other files: {len(categories['other_files'])}")
    
    # Ask user what to delete
    print(f"\n🤔 What would you like to clean up?")
    print(f"1. Delete test files only ({len(categories['test_files'])} files)")
    print(f"2. Delete temp files only ({len(categories['temp_files'])} files)")
    print(f"3. Delete test + temp files ({len(categories['test_files']) + len(categories['temp_files'])} files)")
    print(f"4. Custom cleanup (you choose)")
    print(f"5. Show file lists first")
    print(f"6. Cancel cleanup")
    
    choice = input(f"\n🎯 Enter your choice (1-6): ").strip()
    
    if choice == '1':
        cleanup_test_files(categories['test_files'])
    elif choice == '2':
        cleanup_temp_files(categories['temp_files'])
    elif choice == '3':
        cleanup_test_files(categories['test_files'])
        cleanup_temp_files(categories['temp_files'])
    elif choice == '4':
        custom_cleanup(categories)
    elif choice == '5':
        show_file_lists(categories)
        interactive_cleanup()  # Ask again after showing lists
    elif choice == '6':
        print("❌ Cleanup cancelled by user")
        return
    else:
        print("❌ Invalid choice. Cleanup cancelled.")
        return

def cleanup_test_files(test_files):
    """Xóa các file test"""
    if not test_files:
        print("✅ No test files to delete")
        return
    
    print(f"\n🧪 Deleting {len(test_files)} test files...")
    deleted_count = 0
    
    for file_path in test_files:
        if safe_delete_file(file_path):
            print(f"   ✅ Deleted: {file_path}")
            deleted_count += 1
        else:
            print(f"   ❌ Failed: {file_path}")
    
    print(f"🎯 Test cleanup completed: {deleted_count}/{len(test_files)} files deleted")

def cleanup_temp_files(temp_files):
    """Xóa các file tạm thời"""
    if not temp_files:
        print("✅ No temp files to delete")
        return
    
    print(f"\n🗑️ Deleting {len(temp_files)} temp files...")
    deleted_count = 0
    
    for file_path in temp_files:
        if safe_delete_file(file_path):
            print(f"   ✅ Deleted: {file_path}")
            deleted_count += 1
        else:
            print(f"   ❌ Failed: {file_path}")
    
    print(f"🎯 Temp cleanup completed: {deleted_count}/{len(temp_files)} files deleted")

def show_file_lists(categories):
    """Hiển thị danh sách file theo từng loại"""
    print(f"\n📋 DETAILED FILE LISTS:")
    print("=" * 50)
    
    for category, files in categories.items():
        if files:
            print(f"\n🔸 {category.upper()} ({len(files)} files):")
            for file_path in sorted(files)[:10]:  # Show first 10 files
                print(f"   - {file_path}")
            if len(files) > 10:
                print(f"   ... and {len(files) - 10} more files")
        else:
            print(f"\n🔸 {category.upper()}: No files")

def custom_cleanup(categories):
    """Dọn dẹp tùy chỉnh"""
    print(f"\n🎨 CUSTOM CLEANUP")
    print("-" * 30)
    
    for category, files in categories.items():
        if files and category not in ['essential', 'documentation']:  # Don't ask about essential files
            answer = input(f"Delete {len(files)} {category} files? (y/n): ").strip().lower()
            if answer == 'y':
                if category == 'test_files':
                    cleanup_test_files(files)
                elif category == 'temp_files':
                    cleanup_temp_files(files)
                else:
                    generic_cleanup(files, category)

def generic_cleanup(files, category_name):
    """Xóa files tổng quát"""
    print(f"\n🗑️ Deleting {len(files)} {category_name}...")
    deleted_count = 0
    
    for file_path in files:
        if safe_delete_file(file_path):
            print(f"   ✅ Deleted: {file_path}")
            deleted_count += 1
        else:
            print(f"   ❌ Failed: {file_path}")
    
    print(f"🎯 {category_name} cleanup completed: {deleted_count}/{len(files)} files deleted")

def cleanup_pycache():
    """Xóa __pycache__ directories"""
    print(f"\n🐍 Cleaning up Python cache directories...")
    deleted_count = 0
    
    for root, dirs, files in os.walk('.'):
        if '__pycache__' in dirs:
            pycache_path = os.path.join(root, '__pycache__')
            if safe_delete_directory(pycache_path):
                print(f"   ✅ Deleted: {pycache_path}")
                deleted_count += 1
                dirs.remove('__pycache__')  # Don't traverse into deleted directory
    
    print(f"🎯 Python cache cleanup completed: {deleted_count} directories deleted")

def cleanup_virtual_env():
    """Xóa virtual environment (nếu user đồng ý)"""
    venv_dirs = ['.venv_new', '.venv', 'venv', 'env']
    
    existing_venvs = [d for d in venv_dirs if os.path.exists(d) and os.path.isdir(d)]
    
    if not existing_venvs:
        print("✅ No virtual environments found")
        return
    
    print(f"\n🐍 Found virtual environments: {existing_venvs}")
    print("⚠️  Virtual environments can be recreated with 'pip install -r requirements.txt'")
    
    answer = input(f"Delete virtual environments? (y/n): ").strip().lower()
    if answer == 'y':
        deleted_count = 0
        for venv_dir in existing_venvs:
            if safe_delete_directory(venv_dir):
                print(f"   ✅ Deleted: {venv_dir}")
                deleted_count += 1
            else:
                print(f"   ❌ Failed: {venv_dir}")
        
        print(f"🎯 Virtual environment cleanup completed: {deleted_count}/{len(existing_venvs)} directories deleted")
    else:
        print("⏭️  Skipping virtual environment cleanup")

def generate_cleanup_report():
    """Tạo báo cáo sau khi dọn dẹp"""
    print(f"\n📊 CLEANUP REPORT")
    print("=" * 30)
    
    all_files, all_dirs = analyze_workspace()
    categories = categorize_files(all_files)
    
    print(f"🎯 Current workspace state:")
    print(f"   Total files: {len(all_files)}")
    print(f"   Total directories: {len(all_dirs)}")
    
    print(f"\n📋 Files by category:")
    for category, files in categories.items():
        print(f"   {category}: {len(files)} files")
    
    # Save report to file
    report_file = f"CLEANUP_REPORT_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"
    report_data = {
        'timestamp': datetime.now().isoformat(),
        'total_files': len(all_files),
        'total_directories': len(all_dirs),
        'categories': {k: len(v) for k, v in categories.items()},
        'file_lists': {k: v for k, v in categories.items()}
    }
    
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        print(f"📄 Detailed report saved to: {report_file}")
    except Exception as e:
        print(f"⚠️  Could not save report: {e}")

def main():
    """Main function"""
    print("🧹 TRADING OPTIMIZATION WORKSPACE CLEANUP TOOL")
    print("=" * 60)
    print("🛡️  This tool will safely clean up your workspace")
    print("🔒 Essential files will be automatically protected")
    print("💾 A backup will be created before any changes")
    print()
    
    # Change to the script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    print(f"📁 Working directory: {os.getcwd()}")
    
    # Create backup first
    backup_dir = create_backup_before_cleanup()
    
    # Clean up Python cache first (safe to delete)
    cleanup_pycache()
    
    # Interactive cleanup
    interactive_cleanup()
    
    # Optional: Clean up virtual environment
    cleanup_virtual_env()
    
    # Generate final report
    generate_cleanup_report()
    
    print(f"\n🎉 CLEANUP COMPLETED!")
    print(f"🛡️  Backup location: {backup_dir}")
    print(f"📝 Essential files preserved:")
    for filename, description in ESSENTIAL_FILES.items():
        if os.path.exists(filename):
            print(f"   ✅ {filename}")
        else:
            print(f"   ⚠️  {filename} (missing)")
    
    print(f"\n💡 To restore from backup if needed:")
    print(f"   copy {backup_dir}\\* .")

if __name__ == '__main__':
    main()
