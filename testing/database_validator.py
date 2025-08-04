#!/usr/bin/env python3
"""
Database Schema Validator and Migration Tool
Ensures database integrity, validates schema, and provides migration capabilities
"""

import os
import sys
import sqlite3
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class TableSchema:
    """Database table schema definition"""
    name: str
    columns: List[Dict[str, Any]]
    indexes: List[str] = None
    constraints: List[str] = None

@dataclass
class ValidationResult:
    """Schema validation result"""
    table_name: str
    status: str  # PASS, FAIL, MISSING
    issues: List[str] = None
    suggestions: List[str] = None

class DatabaseValidator:
    """Comprehensive database schema validator and migration tool"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or os.getenv('DATABASE_URL', 'passive_captcha.db')
        self.expected_schema = self._define_expected_schema()
        
    def _define_expected_schema(self) -> List[TableSchema]:
        """Define the expected database schema"""
        return [
            TableSchema(
                name="websites",
                columns=[
                    {"name": "website_id", "type": "VARCHAR(36)", "nullable": False, "primary_key": True},
                    {"name": "website_name", "type": "VARCHAR(255)", "nullable": False},
                    {"name": "website_url", "type": "VARCHAR(500)", "nullable": False},
                    {"name": "admin_email", "type": "VARCHAR(255)", "nullable": False},
                    {"name": "api_key", "type": "VARCHAR(255)", "nullable": False, "unique": True},
                    {"name": "secret_key", "type": "VARCHAR(255)", "nullable": False},
                    {"name": "created_at", "type": "DATETIME", "nullable": True},
                    {"name": "status", "type": "VARCHAR(20)", "nullable": True, "default": "'active'"},
                    {"name": "permissions", "type": "TEXT", "nullable": True},
                    {"name": "rate_limits", "type": "TEXT", "nullable": True}
                ],
                indexes=["idx_websites_admin_email", "idx_websites_status", "idx_websites_api_key"],
                constraints=["UNIQUE(api_key)"]
            ),
            TableSchema(
                name="verification_logs",
                columns=[
                    {"name": "id", "type": "INTEGER", "nullable": False, "primary_key": True, "autoincrement": True},
                    {"name": "website_id", "type": "VARCHAR(36)", "nullable": False},
                    {"name": "session_id", "type": "VARCHAR(255)", "nullable": False},
                    {"name": "ip_address", "type": "VARCHAR(45)", "nullable": True},
                    {"name": "user_agent", "type": "TEXT", "nullable": True},
                    {"name": "origin", "type": "VARCHAR(255)", "nullable": True},
                    {"name": "is_human", "type": "BOOLEAN", "nullable": False},
                    {"name": "confidence", "type": "FLOAT", "nullable": False},
                    {"name": "mouse_movement_count", "type": "INTEGER", "nullable": True},
                    {"name": "avg_mouse_velocity", "type": "FLOAT", "nullable": True},
                    {"name": "mouse_acceleration_variance", "type": "FLOAT", "nullable": True},
                    {"name": "keystroke_count", "type": "INTEGER", "nullable": True},
                    {"name": "avg_keystroke_interval", "type": "FLOAT", "nullable": True},
                    {"name": "typing_rhythm_consistency", "type": "FLOAT", "nullable": True},
                    {"name": "session_duration_normalized", "type": "FLOAT", "nullable": True},
                    {"name": "webgl_support_score", "type": "FLOAT", "nullable": True},
                    {"name": "canvas_uniqueness_score", "type": "FLOAT", "nullable": True},
                    {"name": "hardware_legitimacy_score", "type": "FLOAT", "nullable": True},
                    {"name": "browser_consistency_score", "type": "FLOAT", "nullable": True},
                    {"name": "response_time", "type": "FLOAT", "nullable": True},
                    {"name": "timestamp", "type": "DATETIME", "nullable": True}
                ],
                indexes=[
                    "idx_verification_logs_website_id",
                    "idx_verification_logs_timestamp",
                    "idx_verification_logs_session_id",
                    "idx_verification_logs_ip_address"
                ],
                constraints=["FOREIGN KEY(website_id) REFERENCES websites(website_id)"]
            ),
            TableSchema(
                name="admin_users",
                columns=[
                    {"name": "user_id", "type": "VARCHAR(36)", "nullable": False, "primary_key": True},
                    {"name": "email", "type": "VARCHAR(255)", "nullable": False, "unique": True},
                    {"name": "password_hash", "type": "VARCHAR(255)", "nullable": False},
                    {"name": "name", "type": "VARCHAR(255)", "nullable": False},
                    {"name": "role", "type": "VARCHAR(50)", "nullable": False, "default": "'admin'"},
                    {"name": "is_active", "type": "BOOLEAN", "nullable": False, "default": True},
                    {"name": "created_at", "type": "DATETIME", "nullable": True},
                    {"name": "last_login", "type": "DATETIME", "nullable": True},
                    {"name": "failed_login_attempts", "type": "INTEGER", "nullable": False, "default": 0},
                    {"name": "account_locked_until", "type": "DATETIME", "nullable": True},
                    {"name": "password_changed_at", "type": "DATETIME", "nullable": True},
                    {"name": "security_settings", "type": "TEXT", "nullable": True}
                ],
                indexes=["idx_admin_users_email", "idx_admin_users_role", "idx_admin_users_active"],
                constraints=["UNIQUE(email)"]
            ),
            TableSchema(
                name="system_logs",
                columns=[
                    {"name": "id", "type": "INTEGER", "nullable": False, "primary_key": True, "autoincrement": True},
                    {"name": "level", "type": "VARCHAR(20)", "nullable": False},
                    {"name": "message", "type": "TEXT", "nullable": False},
                    {"name": "timestamp", "type": "DATETIME", "nullable": False},
                    {"name": "component", "type": "VARCHAR(100)", "nullable": True},
                    {"name": "user_id", "type": "VARCHAR(36)", "nullable": True},
                    {"name": "ip_address", "type": "VARCHAR(45)", "nullable": True},
                    {"name": "metadata", "type": "TEXT", "nullable": True}
                ],
                indexes=["idx_system_logs_timestamp", "idx_system_logs_level", "idx_system_logs_component"],
                constraints=[]
            ),
            TableSchema(
                name="script_tokens",
                columns=[
                    {"name": "token_id", "type": "VARCHAR(36)", "nullable": False, "primary_key": True},
                    {"name": "website_id", "type": "VARCHAR(36)", "nullable": False},
                    {"name": "script_token", "type": "VARCHAR(255)", "nullable": False, "unique": True},
                    {"name": "integration_key", "type": "VARCHAR(255)", "nullable": False},
                    {"name": "status", "type": "VARCHAR(20)", "nullable": False, "default": "'pending'"},
                    {"name": "script_version", "type": "VARCHAR(50)", "nullable": False},
                    {"name": "environment", "type": "VARCHAR(20)", "nullable": False, "default": "'production'"},
                    {"name": "created_at", "type": "DATETIME", "nullable": False},
                    {"name": "activated_at", "type": "DATETIME", "nullable": True},
                    {"name": "last_used_at", "type": "DATETIME", "nullable": True},
                    {"name": "revoked_at", "type": "DATETIME", "nullable": True},
                    {"name": "revoked_by", "type": "VARCHAR(255)", "nullable": True},
                    {"name": "revoked_reason", "type": "TEXT", "nullable": True},
                    {"name": "usage_count", "type": "INTEGER", "nullable": False, "default": 0},
                    {"name": "regeneration_count", "type": "INTEGER", "nullable": False, "default": 0},
                    {"name": "parent_token_id", "type": "VARCHAR(36)", "nullable": True},
                    {"name": "config", "type": "TEXT", "nullable": True},
                    {"name": "rate_limit_config", "type": "TEXT", "nullable": True},
                    {"name": "security_config", "type": "TEXT", "nullable": True},
                    {"name": "monitoring_config", "type": "TEXT", "nullable": True},
                    {"name": "notification_config", "type": "TEXT", "nullable": True},
                    {"name": "metadata", "type": "TEXT", "nullable": True}
                ],
                indexes=[
                    "idx_script_tokens_website_id",
                    "idx_script_tokens_status",
                    "idx_script_tokens_script_token",
                    "idx_script_tokens_environment"
                ],
                constraints=[
                    "UNIQUE(script_token)",
                    "FOREIGN KEY(website_id) REFERENCES websites(website_id)"
                ]
            )
        ]
    
    def connect_database(self) -> sqlite3.Connection:
        """Create database connection"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    def get_existing_schema(self) -> Dict[str, Any]:
        """Get current database schema"""
        schema = {}
        
        try:
            with self.connect_database() as conn:
                # Get all tables
                cursor = conn.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                """)
                tables = [row[0] for row in cursor.fetchall()]
                
                for table in tables:
                    # Get table schema
                    cursor = conn.execute(f"PRAGMA table_info({table})")
                    columns = []
                    for row in cursor.fetchall():
                        columns.append({
                            "name": row[1],
                            "type": row[2],
                            "nullable": not bool(row[3]),
                            "default": row[4],
                            "primary_key": bool(row[5])
                        })
                    
                    # Get indexes
                    cursor = conn.execute(f"PRAGMA index_list({table})")
                    indexes = [row[1] for row in cursor.fetchall()]
                    
                    schema[table] = {
                        "columns": columns,
                        "indexes": indexes
                    }
                    
        except Exception as e:
            logger.error(f"Failed to get existing schema: {e}")
            schema = {}
        
        return schema
    
    def validate_schema(self) -> List[ValidationResult]:
        """Validate current schema against expected schema"""
        results = []
        existing_schema = self.get_existing_schema()
        
        for expected_table in self.expected_schema:
            if expected_table.name not in existing_schema:
                results.append(ValidationResult(
                    table_name=expected_table.name,
                    status="MISSING",
                    issues=[f"Table {expected_table.name} does not exist"],
                    suggestions=[f"Create table {expected_table.name}"]
                ))
                continue
            
            # Validate columns
            existing_table = existing_schema[expected_table.name]
            existing_columns = {col["name"]: col for col in existing_table["columns"]}
            
            issues = []
            suggestions = []
            
            for expected_col in expected_table.columns:
                col_name = expected_col["name"]
                
                if col_name not in existing_columns:
                    issues.append(f"Missing column: {col_name}")
                    suggestions.append(f"ADD COLUMN {col_name} {expected_col['type']}")
                else:
                    existing_col = existing_columns[col_name]
                    
                    # Check type compatibility (simplified)
                    expected_type = expected_col["type"].upper()
                    existing_type = existing_col["type"].upper()
                    
                    if expected_type != existing_type:
                        # Allow some type variations
                        type_compatible = (
                            (expected_type.startswith("VARCHAR") and existing_type.startswith("VARCHAR")) or
                            (expected_type in ["INTEGER", "INT"] and existing_type in ["INTEGER", "INT"]) or
                            (expected_type == "BOOLEAN" and existing_type in ["BOOLEAN", "INTEGER"]) or
                            (expected_type == "DATETIME" and existing_type in ["DATETIME", "TEXT"])
                        )
                        
                        if not type_compatible:
                            issues.append(f"Column {col_name} type mismatch: expected {expected_type}, got {existing_type}")
                            suggestions.append(f"Consider updating column {col_name} type")
            
            # Check for unexpected columns
            for existing_col_name in existing_columns:
                if not any(col["name"] == existing_col_name for col in expected_table.columns):
                    issues.append(f"Unexpected column: {existing_col_name}")
            
            # Validate indexes
            if expected_table.indexes:
                existing_indexes = set(existing_table["indexes"])
                expected_indexes = set(expected_table.indexes)
                
                missing_indexes = expected_indexes - existing_indexes
                for index in missing_indexes:
                    issues.append(f"Missing index: {index}")
                    suggestions.append(f"CREATE INDEX {index}")
            
            status = "FAIL" if issues else "PASS"
            results.append(ValidationResult(
                table_name=expected_table.name,
                status=status,
                issues=issues,
                suggestions=suggestions
            ))
        
        return results
    
    def create_missing_tables(self) -> Dict[str, bool]:
        """Create missing tables and indexes"""
        results = {}
        existing_schema = self.get_existing_schema()
        
        try:
            with self.connect_database() as conn:
                for expected_table in self.expected_schema:
                    if expected_table.name not in existing_schema:
                        try:
                            # Create table
                            sql = self._generate_create_table_sql(expected_table)
                            conn.execute(sql)
                            
                            # Create indexes
                            if expected_table.indexes:
                                for index in expected_table.indexes:
                                    index_sql = self._generate_create_index_sql(expected_table.name, index)
                                    conn.execute(index_sql)
                            
                            results[expected_table.name] = True
                            logger.info(f"Created table: {expected_table.name}")
                            
                        except Exception as e:
                            results[expected_table.name] = False
                            logger.error(f"Failed to create table {expected_table.name}: {e}")
                    else:
                        results[expected_table.name] = True  # Already exists
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Database creation failed: {e}")
            
        return results
    
    def _generate_create_table_sql(self, table: TableSchema) -> str:
        """Generate CREATE TABLE SQL"""
        columns = []
        
        for col in table.columns:
            col_def = f"{col['name']} {col['type']}"
            
            if col.get("primary_key"):
                col_def += " PRIMARY KEY"
            
            if col.get("autoincrement"):
                col_def += " AUTOINCREMENT"
            
            if not col.get("nullable", True):
                col_def += " NOT NULL"
            
            if col.get("unique"):
                col_def += " UNIQUE"
            
            if col.get("default") is not None:
                col_def += f" DEFAULT {col['default']}"
            
            columns.append(col_def)
        
        # Add constraints
        if table.constraints:
            columns.extend(table.constraints)
        
        sql = f"CREATE TABLE {table.name} (\n    " + ",\n    ".join(columns) + "\n)"
        return sql
    
    def _generate_create_index_sql(self, table_name: str, index_name: str) -> str:
        """Generate CREATE INDEX SQL"""
        # Simplified index creation - assumes single column index
        # In production, you'd want more sophisticated index parsing
        column_name = index_name.replace(f"idx_{table_name}_", "")
        return f"CREATE INDEX {index_name} ON {table_name}({column_name})"
    
    def test_data_integrity(self) -> Dict[str, Any]:
        """Test data integrity and constraints"""
        tests = []
        
        try:
            with self.connect_database() as conn:
                # Test 1: Check for orphaned records
                cursor = conn.execute("""
                    SELECT COUNT(*) as orphaned_logs
                    FROM verification_logs v
                    LEFT JOIN websites w ON v.website_id = w.website_id
                    WHERE w.website_id IS NULL
                """)
                orphaned_logs = cursor.fetchone()[0]
                
                tests.append({
                    "test": "orphaned_verification_logs",
                    "status": "PASS" if orphaned_logs == 0 else "FAIL",
                    "count": orphaned_logs,
                    "description": "Verification logs without corresponding websites"
                })
                
                # Test 2: Check for duplicate API keys
                cursor = conn.execute("""
                    SELECT api_key, COUNT(*) as count
                    FROM websites
                    GROUP BY api_key
                    HAVING COUNT(*) > 1
                """)
                duplicate_keys = cursor.fetchall()
                
                tests.append({
                    "test": "duplicate_api_keys",
                    "status": "PASS" if len(duplicate_keys) == 0 else "FAIL",
                    "count": len(duplicate_keys),
                    "description": "Duplicate API keys in websites table"
                })
                
                # Test 3: Check data types and ranges
                cursor = conn.execute("""
                    SELECT COUNT(*) as invalid_confidence
                    FROM verification_logs
                    WHERE confidence < 0 OR confidence > 1
                """)
                invalid_confidence = cursor.fetchone()[0]
                
                tests.append({
                    "test": "confidence_range",
                    "status": "PASS" if invalid_confidence == 0 else "FAIL",
                    "count": invalid_confidence,
                    "description": "Confidence values outside valid range (0-1)"
                })
                
                # Test 4: Check for future timestamps
                cursor = conn.execute("""
                    SELECT COUNT(*) as future_timestamps
                    FROM verification_logs
                    WHERE timestamp > datetime('now')
                """)
                future_timestamps = cursor.fetchone()[0]
                
                tests.append({
                    "test": "future_timestamps",
                    "status": "PASS" if future_timestamps == 0 else "FAIL",
                    "count": future_timestamps,
                    "description": "Timestamps in the future"
                })
                
        except Exception as e:
            tests.append({
                "test": "data_integrity_check",
                "status": "FAIL",
                "error": str(e),
                "description": "Failed to run data integrity tests"
            })
        
        return {
            "tests": tests,
            "passed": sum(1 for t in tests if t["status"] == "PASS"),
            "failed": sum(1 for t in tests if t["status"] == "FAIL"),
            "total": len(tests)
        }
    
    def generate_sample_data(self, num_websites: int = 5, num_logs: int = 100) -> bool:
        """Generate sample data for testing"""
        try:
            with self.connect_database() as conn:
                # Generate sample websites
                for i in range(num_websites):
                    website_data = {
                        "website_id": f"test_website_{i+1}",
                        "website_name": f"Test Website {i+1}",
                        "website_url": f"https://test{i+1}.example.com",
                        "admin_email": f"admin{i+1}@test.com",
                        "api_key": f"test_api_key_{i+1}_{int(time.time())}",
                        "secret_key": f"test_secret_{i+1}_{int(time.time())}",
                        "created_at": datetime.utcnow().isoformat(),
                        "status": "active"
                    }
                    
                    conn.execute("""
                        INSERT OR REPLACE INTO websites 
                        (website_id, website_name, website_url, admin_email, api_key, secret_key, created_at, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        website_data["website_id"],
                        website_data["website_name"],
                        website_data["website_url"],
                        website_data["admin_email"],
                        website_data["api_key"],
                        website_data["secret_key"],
                        website_data["created_at"],
                        website_data["status"]
                    ))
                
                # Generate sample verification logs
                import random
                
                for i in range(num_logs):
                    website_id = f"test_website_{random.randint(1, num_websites)}"
                    log_data = {
                        "website_id": website_id,
                        "session_id": f"test_session_{i+1}",
                        "ip_address": f"192.168.1.{random.randint(1, 254)}",
                        "user_agent": "Mozilla/5.0 (Test Browser)",
                        "origin": f"https://test{random.randint(1, num_websites)}.example.com",
                        "is_human": random.choice([True, False]),
                        "confidence": round(random.uniform(0.1, 0.9), 3),
                        "mouse_movement_count": random.randint(10, 100),
                        "avg_mouse_velocity": round(random.uniform(0.1, 2.0), 3),
                        "keystroke_count": random.randint(5, 50),
                        "response_time": round(random.uniform(0.1, 1.0), 3),
                        "timestamp": (datetime.utcnow() - timedelta(hours=random.randint(1, 720))).isoformat()
                    }
                    
                    conn.execute("""
                        INSERT INTO verification_logs 
                        (website_id, session_id, ip_address, user_agent, origin, is_human, confidence,
                         mouse_movement_count, avg_mouse_velocity, keystroke_count, response_time, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        log_data["website_id"],
                        log_data["session_id"],
                        log_data["ip_address"],
                        log_data["user_agent"],
                        log_data["origin"],
                        log_data["is_human"],
                        log_data["confidence"],
                        log_data["mouse_movement_count"],
                        log_data["avg_mouse_velocity"],
                        log_data["keystroke_count"],
                        log_data["response_time"],
                        log_data["timestamp"]
                    ))
                
                conn.commit()
                logger.info(f"Generated {num_websites} websites and {num_logs} verification logs")
                return True
                
        except Exception as e:
            logger.error(f"Failed to generate sample data: {e}")
            return False
    
    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run comprehensive database validation"""
        logger.info("Starting comprehensive database validation...")
        
        # Schema validation
        schema_results = self.validate_schema()
        
        # Data integrity tests
        integrity_results = self.test_data_integrity()
        
        # Create missing tables if needed
        creation_results = self.create_missing_tables()
        
        # Compile summary
        schema_passed = sum(1 for r in schema_results if r.status == "PASS")
        schema_failed = sum(1 for r in schema_results if r.status in ["FAIL", "MISSING"])
        
        summary = {
            "schema_validation": {
                "total_tables": len(schema_results),
                "passed": schema_passed,
                "failed": schema_failed,
                "success_rate": schema_passed / len(schema_results) if schema_results else 0,
                "detailed_results": [
                    {
                        "table": r.table_name,
                        "status": r.status,
                        "issues": r.issues or [],
                        "suggestions": r.suggestions or []
                    }
                    for r in schema_results
                ]
            },
            "data_integrity": integrity_results,
            "table_creation": creation_results,
            "database_path": self.db_path,
            "validation_timestamp": datetime.utcnow().isoformat()
        }
        
        return summary

def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Database Schema Validator")
    parser.add_argument("--db", help="Database path")
    parser.add_argument("--output", default="database_validation_report.json", help="Output file")
    parser.add_argument("--create-missing", action="store_true", help="Create missing tables")
    parser.add_argument("--generate-sample", type=int, help="Generate sample data (specify number of logs)")
    args = parser.parse_args()
    
    # Create validator
    validator = DatabaseValidator(db_path=args.db)
    
    # Generate sample data if requested
    if args.generate_sample:
        success = validator.generate_sample_data(num_logs=args.generate_sample)
        print(f"Sample data generation: {'✓' if success else '✗'}")
    
    # Run validation
    summary = validator.run_comprehensive_validation()
    
    # Save report
    with open(args.output, 'w') as f:
        json.dump(summary, f, indent=2)
    
    # Print summary
    print(f"\nDatabase Validation Summary:")
    print(f"Schema Tables: {summary['schema_validation']['total_tables']}")
    print(f"Schema Passed: {summary['schema_validation']['passed']}")
    print(f"Schema Failed: {summary['schema_validation']['failed']}")
    print(f"Schema Success Rate: {summary['schema_validation']['success_rate']:.2%}")
    print(f"Data Integrity Tests: {summary['data_integrity']['total']}")
    print(f"Data Integrity Passed: {summary['data_integrity']['passed']}")
    print(f"Data Integrity Failed: {summary['data_integrity']['failed']}")
    
    # Show issues
    failed_tables = [r for r in summary['schema_validation']['detailed_results'] if r['status'] != 'PASS']
    if failed_tables:
        print(f"\nSchema Issues:")
        for table in failed_tables:
            print(f"  {table['table']} ({table['status']}):")
            for issue in table['issues']:
                print(f"    - {issue}")
    
    print(f"\nDetailed report saved to: {args.output}")
    
    # Exit with error code if validation failed
    exit_code = 0 if summary['schema_validation']['failed'] == 0 and summary['data_integrity']['failed'] == 0 else 1
    sys.exit(exit_code)

if __name__ == "__main__":
    main()