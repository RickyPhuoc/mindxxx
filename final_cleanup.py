#!/usr/bin/env python3
"""
🧹 FINAL WORKSPACE CLEANUP - Remove remaining unnecessary files
Dọn dẹp cuối cùng để workspace chỉ còn những file thực sự cần thiết
"""

import os
import shutil
from datetime import datetime

def remove_virtual_environments():
    """Xóa virtual environments để tiết kiệm không gian"""
    venv_dirs = ['.venv', '.venv_new']
    removed = []
    
    for venv_dir in venv_dirs:
        if os.path.exists(venv_dir) and os.path.isdir(venv_dir):
            try:
                print(f"🗑️ Removing {venv_dir}...")
                shutil.rmtree(venv_dir)
                removed.append(venv_dir)
                print(f"   ✅ Deleted: {venv_dir}")
            except Exception as e:
                print(f"   ❌ Failed to delete {venv_dir}: {e}")
    
    if removed:
        print(f"🎯 Virtual environments removed: {len(removed)}")
        print(f"💡 To recreate: python -m venv .venv && .venv\\Scripts\\activate && pip install -r requirements.txt")
    else:
        print("✅ No virtual environments found to remove")

def remove_cleanup_scripts():
    """Xóa các script cleanup sau khi sử dụng xong"""
    cleanup_files = [
        'cleanup_workspace.py',
        'CLEANUP_REPORT_2025-07-23_12-45-49.json'
    ]
    
    removed = []
    for file in cleanup_files:
        if os.path.exists(file):
            try:
                os.remove(file)
                removed.append(file)
                print(f"   ✅ Deleted: {file}")
            except Exception as e:
                print(f"   ❌ Failed to delete {file}: {e}")
    
    if removed:
        print(f"🎯 Cleanup scripts removed: {len(removed)}")

def create_final_structure_report():
    """Tạo báo cáo cấu trúc cuối cùng"""
    print("\n📊 FINAL WORKSPACE STRUCTURE:")
    print("=" * 50)
    
    # Count files by category
    essential_files = 0
    data_files = 0
    doc_files = 0
    other_files = 0
    total_size_mb = 0
    
    for root, dirs, files in os.walk('.'):
        # Skip backup directories
        dirs[:] = [d for d in dirs if not d.startswith('BACKUP_') and d != '__pycache__']
        
        for file in files:
            file_path = os.path.join(root, file)
            try:
                file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
                total_size_mb += file_size
            except:
                pass
            
            if file.endswith('.py') or file.endswith('.bat'):
                essential_files += 1
            elif file.endswith('.csv') or 'BINANCE_' in file:
                data_files += 1
            elif file.endswith('.md') or file.endswith('.txt'):
                doc_files += 1
            else:
                other_files += 1
    
    print(f"📁 Total directories: {len([d for d in os.listdir('.') if os.path.isdir(d) and not d.startswith('BACKUP_')])}")
    print(f"📄 Essential files (Python/scripts): {essential_files}")
    print(f"📊 Data files (CSV/BINANCE): {data_files}")
    print(f"📋 Documentation: {doc_files}")
    print(f"❓ Other files: {other_files}")
    print(f"💾 Total size: {total_size_mb:.1f} MB")
    
    # List essential directories
    print(f"\n📁 Essential directories:")
    for item in os.listdir('.'):
        if os.path.isdir(item) and not item.startswith('.') and not item.startswith('BACKUP_'):
            print(f"   ├── {item}")
    
    # List essential files
    essential_py_files = [f for f in os.listdir('.') if f.endswith('.py')]
    if essential_py_files:
        print(f"\n🐍 Core Python files:")
        for file in sorted(essential_py_files):
            print(f"   ├── {file}")

def main():
    """Main cleanup function"""
    print("🧹 FINAL WORKSPACE CLEANUP")
    print("=" * 40)
    print("🎯 This will remove virtual environments and cleanup files")
    print("🔒 All essential files will be preserved")
    
    # Change to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    print(f"📁 Working directory: {os.getcwd()}")
    
    # Ask for confirmation
    print(f"\n⚠️  This will:")
    print(f"   - Delete .venv and .venv_new directories (can be recreated)")
    print(f"   - Remove cleanup scripts (no longer needed)")
    print(f"   - Keep all essential files and data")
    
    confirm = input(f"\n🤔 Continue? (y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ Cleanup cancelled")
        return
    
    print(f"\n🚀 Starting final cleanup...")
    
    # Remove virtual environments
    remove_virtual_environments()
    
    # Remove cleanup files (but not this script yet)
    print(f"\n🗑️ Removing cleanup artifacts...")
    remove_cleanup_scripts()
    
    # Create final report
    create_final_structure_report()
    
    print(f"\n🎉 FINAL CLEANUP COMPLETED!")
    print(f"✅ Workspace is now clean and optimized")
    print(f"📦 Ready for backup or deployment")
    
    # Self-destruct option
    print(f"\n🤔 Remove this final cleanup script too? (y/n): ", end='')
    self_delete = input().strip().lower()
    if self_delete == 'y':
        try:
            script_name = os.path.basename(__file__)
            print(f"🗑️ Self-destructing: {script_name}")
            # Can't delete self while running, so just mark for manual deletion
            print(f"💡 Please manually delete: {script_name}")
        except:
            pass

if __name__ == '__main__':
    main()
