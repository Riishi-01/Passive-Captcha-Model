#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Deployment Testing Suite
Tests all critical components and identifies issues
"""

import os
import sys
import json
import subprocess
import re
from pathlib import Path

class DeploymentTester:
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent.parent
        self.issues = []
        self.fixes_applied = []

    def test_unicode_issues(self):
        """Test for Unicode characters causing syntax errors"""
        print("[CHAR] Testing for Unicode characters...")
        unicode_chars = ['[SUCCESS]', '[WARNING]', '[ERROR]', '[PROCESSING]', '[INFO]', '[SECURE]', '[NETWORK]', '[FEATURE]', '[TARGET]', '[DEPLOY]', '[HEALTH]']

        python_files = list(self.root_dir.rglob("*.py"))
        issues_found = []

        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                for char in unicode_chars:
                    if char in content:
                        lines = content.split('\n')
                        for i, line in enumerate(lines, 1):
                            if char in line:
                                issues_found.append({
                                    'file': str(py_file),
                                    'line': i,
                                    'char': char,
                                    'content': line.strip()
                                })
            except Exception as e:
                issues_found.append({
                    'file': str(py_file),
                    'error': f"Could not read file: {e}"
                })

        if issues_found:
            self.issues.append({
                'type': 'unicode_characters',
                'severity': 'critical',
                'description': 'Unicode characters found in Python files',
                'details': issues_found,
                'fix_command': 'fix_unicode_characters'
            })
            print(f"[ERROR] Found {len(issues_found)} Unicode character issues")
        else:
            print("[SUCCESS] No Unicode character issues found")

        return issues_found

    def test_node_version(self):
        """Test Node.js version configuration"""
        print("[CHAR] Testing Node.js version configuration...")
        issues_found = []

        package_files = ['package.json', 'frontend/package.json']

        for pkg_file in package_files:
            pkg_path = self.root_dir / pkg_file
            if pkg_path.exists():
                try:
                    with open(pkg_path, 'r') as f:
                        pkg_data = json.load(f)

                    if 'engines' in pkg_data and 'node' in pkg_data['engines']:
                        node_version = pkg_data['engines']['node']
                        if node_version.startswith('18'):
                            issues_found.append({
                                'file': pkg_file,
                                'current_version': node_version,
                                'required_version': '22.x'
                            })
                except Exception as e:
                    issues_found.append({
                        'file': pkg_file,
                        'error': f"Could not parse JSON: {e}"
                    })

        if issues_found:
            self.issues.append({
                'type': 'node_version',
                'severity': 'critical',
                'description': 'Node.js version needs to be updated to 22.x',
                'details': issues_found,
                'fix_command': 'fix_node_version'
            })
            print(f"[ERROR] Found {len(issues_found)} Node.js version issues")
        else:
            print("[SUCCESS] Node.js version configuration is correct")

        return issues_found

    def test_encoding_declarations(self):
        """Test for missing encoding declarations"""
        print("[CHAR] Testing for encoding declarations...")
        python_files = list(self.root_dir.rglob("*.py"))
        issues_found = []

        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                has_encoding = False
                for i, line in enumerate(lines[:3]):  # Check first 3 lines
                    if 'coding' in line or 'encoding' in line:
                        has_encoding = True
                        break

                if not has_encoding:
                    # Check if file contains non-ASCII characters
                    content = ''.join(lines)
                    if any(ord(char) > 127 for char in content):
                        issues_found.append({
                            'file': str(py_file),
                            'reason': 'Contains non-ASCII characters but no encoding declaration'
                        })
            except Exception as e:
                issues_found.append({
                    'file': str(py_file),
                    'error': f"Could not read file: {e}"
                })

        if issues_found:
            self.issues.append({
                'type': 'encoding_declarations',
                'severity': 'high',
                'description': 'Missing encoding declarations in Python files',
                'details': issues_found,
                'fix_command': 'fix_encoding_declarations'
            })
            print(f"[ERROR] Found {len(issues_found)} encoding declaration issues")
        else:
            print("[SUCCESS] Encoding declarations are correct")

        return issues_found

    def test_syntax_errors(self):
        """Test for Python syntax errors"""
        print("[CHAR] Testing for Python syntax errors...")
        python_files = list(self.root_dir.rglob("*.py"))
        issues_found = []

        for py_file in python_files:
            try:
                result = subprocess.run([
                    sys.executable, '-m', 'py_compile', str(py_file)
                ], capture_output=True, text=True, timeout=30)

                if result.returncode != 0:
                    issues_found.append({
                        'file': str(py_file),
                        'error': result.stderr
                    })
            except subprocess.TimeoutExpired:
                issues_found.append({
                    'file': str(py_file),
                    'error': 'Compilation timeout'
                })
            except Exception as e:
                issues_found.append({
                    'file': str(py_file),
                    'error': f"Could not compile: {e}"
                })

        if issues_found:
            self.issues.append({
                'type': 'syntax_errors',
                'severity': 'critical',
                'description': 'Python syntax errors found',
                'details': issues_found,
                'fix_command': 'fix_syntax_errors'
            })
            print(f"[ERROR] Found {len(issues_found)} syntax errors")
        else:
            print("[SUCCESS] No syntax errors found")

        return issues_found

    def test_import_errors(self):
        """Test for import errors"""
        print("[CHAR] Testing for import errors...")
        issues_found = []

        # Test main application files
        critical_files = [
            'backend/main.py',
            'backend/app/__init__.py',
            'backend/app/services/auth_service.py'
        ]

        for file_path in critical_files:
            full_path = self.root_dir / file_path
            if full_path.exists():
                try:
                    # Change to backend directory for proper imports
                    result = subprocess.run([
                        sys.executable, '-c', f'import sys; sys.path.insert(0, "backend"); exec(open("{file_path}").read())'
                    ], capture_output=True, text=True, timeout=30, cwd=self.root_dir)

                    if result.returncode != 0:
                        issues_found.append({
                            'file': file_path,
                            'error': result.stderr
                        })
                except Exception as e:
                    issues_found.append({
                        'file': file_path,
                        'error': f"Could not test imports: {e}"
                    })

        if issues_found:
            self.issues.append({
                'type': 'import_errors',
                'severity': 'high',
                'description': 'Import errors found',
                'details': issues_found,
                'fix_command': 'fix_import_errors'
            })
            print(f"[ERROR] Found {len(issues_found)} import errors")
        else:
            print("[SUCCESS] No import errors found")

        return issues_found

    def test_requirements_consistency(self):
        """Test requirements.txt consistency"""
        print("[CHAR] Testing requirements consistency...")
        issues_found = []

        req_files = [
            'backend/requirements.txt',
            'backend/requirements-render.txt'
        ]

        requirements = {}
        for req_file in req_files:
            req_path = self.root_dir / req_file
            if req_path.exists():
                try:
                    with open(req_path, 'r') as f:
                        lines = f.readlines()

                    reqs = []
                    for line in lines:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            reqs.append(line)

                    requirements[req_file] = reqs
                except Exception as e:
                    issues_found.append({
                        'file': req_file,
                        'error': f"Could not read requirements: {e}"
                    })

        # Check for version conflicts
        if len(requirements) > 1:
            # Compare requirements files
            files = list(requirements.keys())
            if len(files) == 2:
                req1, req2 = requirements[files[0]], requirements[files[1]]
                if set(req1) != set(req2):
                    issues_found.append({
                        'type': 'version_mismatch',
                        'file1': files[0],
                        'file2': files[1],
                        'difference': {
                            'only_in_1': list(set(req1) - set(req2)),
                            'only_in_2': list(set(req2) - set(req1))
                        }
                    })

        if issues_found:
            self.issues.append({
                'type': 'requirements_consistency',
                'severity': 'medium',
                'description': 'Requirements file inconsistencies',
                'details': issues_found,
                'fix_command': 'fix_requirements'
            })
            print(f"[ERROR] Found {len(issues_found)} requirements issues")
        else:
            print("[SUCCESS] Requirements are consistent")

        return issues_found

    def run_all_tests(self):
        """Run all deployment tests"""
        print("[DEPLOY] Starting Comprehensive Deployment Testing Suite\n")

        # Run all tests
        self.test_unicode_issues()
        self.test_node_version()
        self.test_encoding_declarations()
        self.test_syntax_errors()
        self.test_import_errors()
        self.test_requirements_consistency()

        # Generate report
        return self.generate_report()

    def generate_report(self):
        """Generate comprehensive test report"""
        critical_issues = [i for i in self.issues if i['severity'] == 'critical']
        high_issues = [i for i in self.issues if i['severity'] == 'high']
        medium_issues = [i for i in self.issues if i['severity'] == 'medium']

        report = {
            'timestamp': subprocess.check_output(['date'], text=True).strip(),
            'total_issues': len(self.issues),
            'critical_issues': len(critical_issues),
            'high_issues': len(high_issues),
            'medium_issues': len(medium_issues),
            'issues': self.issues,
            'deployment_ready': len(critical_issues) == 0
        }

        print(f"\n[INFO] DEPLOYMENT TEST REPORT")
        print(f"{'='*50}")
        print(f"Total Issues Found: {report['total_issues']}")
        print(f"Critical Issues: {report['critical_issues']}")
        print(f"High Priority Issues: {report['high_issues']}")
        print(f"Medium Priority Issues: {report['medium_issues']}")
        print(f"Deployment Ready: {'[SUCCESS] YES' if report['deployment_ready'] else '[ERROR] NO'}")

        if self.issues:
            print(f"\n[TOOL] Issues to Fix:")
            for i, issue in enumerate(self.issues, 1):
                print(f"{i}. {issue['type']} ({issue['severity']}): {issue['description']}")

        return report

if __name__ == "__main__":
    tester = DeploymentTester()
    report = tester.run_all_tests()

    # Save report
    with open('scripts/testing/test_report.json', 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\n[DOCUMENT] Report saved to: scripts/testing/test_report.json")
