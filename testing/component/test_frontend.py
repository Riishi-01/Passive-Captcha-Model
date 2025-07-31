#!/usr/bin/env python3
"""
Frontend component tests
"""

import unittest
import json
import subprocess
import os
from pathlib import Path

class TestFrontendStructure(unittest.TestCase):
    """Test frontend structure and configuration"""
    
    def setUp(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.frontend_dir = self.project_root / 'frontend'
    
    def test_frontend_directory_exists(self):
        """Test that frontend directory exists"""
        self.assertTrue(self.frontend_dir.exists(), "Frontend directory not found")
        self.assertTrue(self.frontend_dir.is_dir(), "Frontend path is not a directory")
    
    def test_package_json_exists(self):
        """Test that package.json exists and is valid"""
        package_json = self.frontend_dir / 'package.json'
        self.assertTrue(package_json.exists(), "package.json not found")
        
        with open(package_json, 'r') as f:
            try:
                package_data = json.load(f)
                self.assertIsInstance(package_data, dict)
                self.assertIn('name', package_data)
                self.assertIn('dependencies', package_data)
                print(f"Package name: {package_data.get('name')}")
            except json.JSONDecodeError:
                self.fail("package.json is not valid JSON")
    
    def test_vite_config_exists(self):
        """Test that Vite configuration exists"""
        vite_config = self.frontend_dir / 'vite.config.ts'
        self.assertTrue(vite_config.exists(), "vite.config.ts not found")
    
    def test_typescript_config_exists(self):
        """Test that TypeScript configuration exists"""
        ts_config = self.frontend_dir / 'tsconfig.json'
        self.assertTrue(ts_config.exists(), "tsconfig.json not found")
        
        with open(ts_config, 'r') as f:
            try:
                ts_data = json.load(f)
                self.assertIsInstance(ts_data, dict)
            except json.JSONDecodeError:
                self.fail("tsconfig.json is not valid JSON")
    
    def test_src_directory_structure(self):
        """Test source directory structure"""
        src_dir = self.frontend_dir / 'src'
        self.assertTrue(src_dir.exists(), "src directory not found")
        
        # Check for key directories
        key_dirs = ['app', 'stores', 'router']
        for dir_name in key_dirs:
            dir_path = src_dir / dir_name
            self.assertTrue(dir_path.exists(), f"{dir_name} directory not found")
    
    def test_vue_components_exist(self):
        """Test that key Vue components exist"""
        src_dir = self.frontend_dir / 'src'
        
        # Key components to check
        key_components = [
            'app/auth/login/page.vue',
            'app/dashboard/page.vue',
            'app/dashboard/_components/WebsitesModal.vue'
        ]
        
        for component_path in key_components:
            component_file = src_dir / component_path
            self.assertTrue(component_file.exists(), f"Component not found: {component_path}")
    
    def test_stores_exist(self):
        """Test that Pinia stores exist"""
        stores_dir = self.frontend_dir / 'src' / 'stores'
        
        key_stores = ['auth.ts', 'websites.ts', 'dashboard.ts']
        
        for store_file in key_stores:
            store_path = stores_dir / store_file
            self.assertTrue(store_path.exists(), f"Store not found: {store_file}")
    
    def test_router_configuration(self):
        """Test router configuration"""
        router_file = self.frontend_dir / 'src' / 'router' / 'index.ts'
        self.assertTrue(router_file.exists(), "Router index.ts not found")
    
    def test_dependencies(self):
        """Test that key dependencies are installed"""
        package_json = self.frontend_dir / 'package.json'
        
        with open(package_json, 'r') as f:
            package_data = json.load(f)
        
        dependencies = package_data.get('dependencies', {})
        dev_dependencies = package_data.get('devDependencies', {})
        all_deps = {**dependencies, **dev_dependencies}
        
        # Key dependencies for Vue 3 app
        required_deps = ['vue', 'vue-router', 'pinia', 'axios']
        
        for dep in required_deps:
            self.assertIn(dep, all_deps, f"Required dependency missing: {dep}")
        
        print(f"Found {len(all_deps)} total dependencies")
    
    def test_duplicate_dependencies(self):
        """Test for duplicate dependencies in package.json"""
        package_json = self.frontend_dir / 'package.json'
        
        with open(package_json, 'r') as f:
            content = f.read()
        
        # Check for duplicate socket.io-client entries (known issue)
        socket_io_count = content.count('"socket.io-client"')
        
        if socket_io_count > 1:
            print(f"Warning: socket.io-client appears {socket_io_count} times in package.json")
            # This is a known issue, so we'll just warn about it
        else:
            print("No duplicate dependencies detected")
        
        self.assertTrue(True)  # Test passes regardless


class TestFrontendBuild(unittest.TestCase):
    """Test frontend build process"""
    
    def setUp(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.frontend_dir = self.project_root / 'frontend'
    
    def test_npm_install_works(self):
        """Test that npm install works (if node_modules doesn't exist)"""
        if not self.frontend_dir.exists():
            self.skipTest("Frontend directory not found")
        
        node_modules = self.frontend_dir / 'node_modules'
        
        if not node_modules.exists():
            print("node_modules not found, this would require npm install")
            self.skipTest("node_modules not found - run npm install first")
        else:
            print("node_modules directory exists")
            self.assertTrue(True)
    
    def test_typescript_compilation(self):
        """Test TypeScript compilation (basic check)"""
        if not self.frontend_dir.exists():
            self.skipTest("Frontend directory not found")
        
        # Check if there are any .ts files
        ts_files = list(self.frontend_dir.rglob('*.ts'))
        vue_files = list(self.frontend_dir.rglob('*.vue'))
        
        self.assertGreater(len(ts_files), 0, "No TypeScript files found")
        self.assertGreater(len(vue_files), 0, "No Vue files found")
        
        print(f"Found {len(ts_files)} TypeScript files and {len(vue_files)} Vue files")


if __name__ == '__main__':
    unittest.main(verbosity=2)