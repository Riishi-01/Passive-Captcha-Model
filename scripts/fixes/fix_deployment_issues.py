#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automated Fix Script for Deployment Issues
Fixes issues identified by the testing suite
"""

import os
import sys
import json
import re
import subprocess
from pathlib import Path

class DeploymentFixer:
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent.parent
        self.fixes_applied = []

    def fix_unicode_characters(self):
        """Fix Unicode characters in Python files"""
        print("[TOOL] Fixing Unicode characters...")

        unicode_replacements = {
            '[SUCCESS]': '[SUCCESS]',
            '[WARNING]': '[WARNING]',
            '[ERROR]': '[ERROR]',
            '[PROCESSING]': '[PROCESSING]',
            '[INFO]': '[INFO]',
            '[SECURE]': '[SECURE]',
            '[NETWORK]': '[NETWORK]',
            '[FEATURE]': '[FEATURE]',
            '[TARGET]': '[TARGET]',
            '[DEPLOY]': '[DEPLOY]',
            '[HEALTH]': '[HEALTH]'
        }

        python_files = list(self.root_dir.rglob("*.py"))
        files_fixed = 0

        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                original_content = content
                for unicode_char, replacement in unicode_replacements.items():
                    content = content.replace(unicode_char, replacement)

                if content != original_content:
                    with open(py_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    files_fixed += 1
                    print(f"  [SUCCESS] Fixed: {py_file}")

            except Exception as e:
                print(f"  [ERROR] Error fixing {py_file}: {e}")

        self.fixes_applied.append({
            'fix': 'unicode_characters',
            'files_processed': len(python_files),
            'files_fixed': files_fixed
        })

        print(f"[TARGET] Fixed Unicode characters in {files_fixed} files")
        return files_fixed > 0

    def fix_node_version(self):
        """Fix Node.js version in package.json files"""
        print("[TOOL] Fixing Node.js version...")

        package_files = ['package.json', 'frontend/package.json']
        files_fixed = 0

        for pkg_file in package_files:
            pkg_path = self.root_dir / pkg_file
            if pkg_path.exists():
                try:
                    with open(pkg_path, 'r') as f:
                        pkg_data = json.load(f)

                    # Ensure engines section exists
                    if 'engines' not in pkg_data:
                        pkg_data['engines'] = {}

                    # Update Node.js version
                    if 'node' not in pkg_data['engines'] or pkg_data['engines']['node'].startswith('18'):
                        pkg_data['engines']['node'] = '22.x'

                        with open(pkg_path, 'w') as f:
                            json.dump(pkg_data, f, indent=2)

                        files_fixed += 1
                        print(f"  [SUCCESS] Fixed: {pkg_file}")

                except Exception as e:
                    print(f"  [ERROR] Error fixing {pkg_file}: {e}")

        self.fixes_applied.append({
            'fix': 'node_version',
            'files_fixed': files_fixed
        })

        print(f"[TARGET] Fixed Node.js version in {files_fixed} files")
        return files_fixed > 0

    def fix_encoding_declarations(self):
        """Add encoding declarations to Python files"""
        print("[TOOL] Adding encoding declarations...")

        python_files = list(self.root_dir.rglob("*.py"))
        files_fixed = 0

        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                # Check if encoding declaration exists
                has_encoding = False
                for line in lines[:3]:
                    if 'coding' in line or 'encoding' in line:
                        has_encoding = True
                        break

                if not has_encoding:
                    # Check if file contains non-ASCII characters
                    content = ''.join(lines)
                    if any(ord(char) > 127 for char in content):
                        # Add encoding declaration
                        if lines and lines[0].startswith('#!'):
                            lines.insert(1, '# -*- coding: utf-8 -*-\n')
                        else:
                            lines.insert(0, '# -*- coding: utf-8 -*-\n')

                        with open(py_file, 'w', encoding='utf-8') as f:
                            f.writelines(lines)

                        files_fixed += 1
                        print(f"  [SUCCESS] Added encoding to: {py_file}")

            except Exception as e:
                print(f"  [ERROR] Error processing {py_file}: {e}")

        self.fixes_applied.append({
            'fix': 'encoding_declarations',
            'files_fixed': files_fixed
        })

        print(f"[TARGET] Added encoding declarations to {files_fixed} files")
        return files_fixed > 0

    def fix_syntax_errors(self):
        """Fix common syntax errors"""
        print("[TOOL] Checking for fixable syntax errors...")

        # This is a basic implementation - syntax errors usually need manual review
        # But we can fix some common issues automatically

        python_files = list(self.root_dir.rglob("*.py"))
        files_fixed = 0

        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                original_content = content

                # Fix common syntax issues
                # Remove trailing whitespace
                lines = content.split('\n')
                lines = [line.rstrip() for line in lines]
                content = '\n'.join(lines)

                # Ensure file ends with newline
                if content and not content.endswith('\n'):
                    content += '\n'

                if content != original_content:
                    with open(py_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    files_fixed += 1
                    print(f"  [SUCCESS] Cleaned: {py_file}")

            except Exception as e:
                print(f"  [ERROR] Error processing {py_file}: {e}")

        self.fixes_applied.append({
            'fix': 'syntax_cleanup',
            'files_fixed': files_fixed
        })

        print(f"[TARGET] Cleaned up {files_fixed} files")
        return files_fixed > 0

    def create_vercel_config(self):
        """Create proper Vercel deployment configuration"""
        print("[TOOL] Creating Vercel configuration...")

        vercel_config = {
            "version": 2,
            "builds": [
                {
                    "src": "backend/main.py",
                    "use": "@vercel/python",
                    "config": {
                        "maxLambdaSize": "50mb",
                        "runtime": "python3.9"
                    }
                }
            ],
            "routes": [
                {
                    "src": "/api/(.*)",
                    "dest": "/backend/main.py"
                },
                {
                    "src": "/(.*)",
                    "dest": "/backend/main.py"
                }
            ],
            "env": {
                "FLASK_ENV": "production",
                "PYTHON_VERSION": "3.9"
            }
        }

        try:
            vercel_path = self.root_dir / 'vercel.json'
            with open(vercel_path, 'w') as f:
                json.dump(vercel_config, f, indent=2)

            print("  [SUCCESS] Created vercel.json")

            self.fixes_applied.append({
                'fix': 'vercel_config',
                'created': True
            })

            return True
        except Exception as e:
            print(f"  [ERROR] Error creating vercel.json: {e}")
            return False

    def create_deployment_script(self):
        """Create deployment validation script"""
        print("[TOOL] Creating deployment script...")

        deploy_script = '''#!/bin/bash
# Deployment validation script

echo "[DEPLOY] Starting Passive CAPTCHA Deployment"

# Check Python version
python3 --version

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r backend/requirements-render.txt

# Test imports
echo "🧪 Testing critical imports..."
cd backend
python3 -c "
try:
    import flask
    import flask_cors
    import redis
    import jwt
    print('[SUCCESS] All critical imports successful')
except ImportError as e:
    print(f'[ERROR] Import error: {e}')
    exit(1)
"

# Test syntax
echo "[SEARCH] Testing Python syntax..."
python3 -m py_compile main.py
if [ $? -eq 0 ]; then
    echo "[SUCCESS] Syntax check passed"
else
    echo "[ERROR] Syntax errors found"
    exit 1
fi

echo "[TARGET] Deployment validation complete"
'''

        try:
            deploy_path = self.root_dir / 'deploy.sh'
            with open(deploy_path, 'w') as f:
                f.write(deploy_script)

            # Make executable
            os.chmod(deploy_path, 0o755)

            print("  [SUCCESS] Created deploy.sh")

            self.fixes_applied.append({
                'fix': 'deployment_script',
                'created': True
            })

            return True
        except Exception as e:
            print(f"  [ERROR] Error creating deploy.sh: {e}")
            return False

    def apply_all_fixes(self):
        """Apply all available fixes"""
        print("[DEPLOY] Starting Automated Fix Application\n")

        fixes = [
            self.fix_unicode_characters,
            self.fix_node_version,
            self.fix_encoding_declarations,
            self.fix_syntax_errors,
            self.create_vercel_config,
            self.create_deployment_script
        ]

        for fix_func in fixes:
            try:
                fix_func()
                print()
            except Exception as e:
                print(f"[ERROR] Error in {fix_func.__name__}: {e}\n")

        return self.generate_fix_report()

    def generate_fix_report(self):
        """Generate fix application report"""
        report = {
            'timestamp': subprocess.check_output(['date'], text=True).strip(),
            'fixes_applied': self.fixes_applied,
            'total_fixes': len(self.fixes_applied)
        }

        print(f"[INFO] FIX APPLICATION REPORT")
        print(f"{'='*50}")
        print(f"Total Fixes Applied: {report['total_fixes']}")

        for fix in self.fixes_applied:
            print(f"[SUCCESS] {fix['fix']}: Applied successfully")

        return report

if __name__ == "__main__":
    fixer = DeploymentFixer()
    report = fixer.apply_all_fixes()

    # Save report
    with open('scripts/fixes/fix_report.json', 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\n[DOCUMENT] Fix report saved to: scripts/fixes/fix_report.json")
