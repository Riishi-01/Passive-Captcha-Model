#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Final Deployment Validation - Clean Version
"""

import subprocess
import sys
import os
from pathlib import Path

def test_python_syntax():
    """Test Python syntax of main files"""
    print("Testing Python syntax...")
    
    critical_files = [
        'backend/main.py',
        'backend/app/__init__.py',
        'backend/app/services/auth_service.py'
    ]
    
    for file_path in critical_files:
        if os.path.exists(file_path):
            try:
                result = subprocess.run([
                    sys.executable, '-m', 'py_compile', file_path
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"  [OK] {file_path}")
                else:
                    print(f"  [ERROR] {file_path}: {result.stderr}")
                    return False
            except Exception as e:
                print(f"  [ERROR] {file_path}: {e}")
                return False
    
    return True

def test_requirements():
    """Test requirements files exist and are readable"""
    print("Testing requirements files...")
    
    req_files = [
        'backend/requirements.txt',
        'backend/requirements-render.txt'
    ]
    
    for req_file in req_files:
        if os.path.exists(req_file):
            try:
                with open(req_file, 'r') as f:
                    lines = f.readlines()
                print(f"  [OK] {req_file} ({len(lines)} dependencies)")
            except Exception as e:
                print(f"  [ERROR] {req_file}: {e}")
                return False
        else:
            print(f"  [WARNING] {req_file} not found")
    
    return True

def test_config_files():
    """Test configuration files"""
    print("Testing configuration files...")
    
    config_files = [
        'package.json',
        'vercel.json'
    ]
    
    for config_file in config_files:
        if os.path.exists(config_file):
            print(f"  [OK] {config_file} exists")
        else:
            print(f"  [WARNING] {config_file} not found")
    
    return True

def main():
    """Run final deployment validation"""
    print("=== FINAL DEPLOYMENT VALIDATION ===")
    print()
    
    all_passed = True
    
    # Test Python syntax
    if not test_python_syntax():
        all_passed = False
    print()
    
    # Test requirements
    if not test_requirements():
        all_passed = False
    print()
    
    # Test config files
    if not test_config_files():
        all_passed = False
    print()
    
    # Final result
    if all_passed:
        print("[SUCCESS] All critical tests passed!")
        print("Ready for Vercel deployment")
        return 0
    else:
        print("[ERROR] Some tests failed")
        print("Review errors before deployment")
        return 1

if __name__ == "__main__":
    exit(main())
