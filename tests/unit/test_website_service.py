"""
Unit Tests for Website Service
Comprehensive testing of website management functionality
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../backend'))

from datetime import datetime
import json
import redis

# Mock dependencies before importing
sys.modules['app.database'] = Mock()
sys.modules['app.script_token_manager'] = Mock()

from app.services.website_service import (
    WebsiteService, WebsiteData, WebsiteStatus, IntegrationStatus
)


class TestWebsiteService(unittest.TestCase):
    """Test cases for WebsiteService"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_redis = Mock(spec=redis.Redis)
        self.service = WebsiteService(self.mock_redis)
        
        # Mock database session
        self.mock_session = Mock()
        self.mock_db_patcher = patch('app.services.website_service.get_db_session')
        self.mock_get_db = self.mock_db_patcher.start()
        self.mock_get_db.return_value = self.mock_session
        
        # Mock script token manager
        self.mock_token_manager_patcher = patch('app.services.website_service.get_script_token_manager')
        self.mock_get_token_manager = self.mock_token_manager_patcher.start()
        self.mock_token_manager = Mock()
        self.mock_get_token_manager.return_value = self.mock_token_manager
        
        # Mock current_app
        self.mock_app_patcher = patch('app.services.website_service.current_app')
        self.mock_app = self.mock_app_patcher.start()
        self.mock_app.logger = Mock()
    
    def tearDown(self):
        """Clean up test fixtures"""
        self.mock_db_patcher.stop()
        self.mock_token_manager_patcher.stop()
        self.mock_app_patcher.stop()
    
    def test_website_data_creation(self):
        """Test WebsiteData object creation and serialization"""
        now = datetime.utcnow()
        website = WebsiteData(
            id="test-id",
            name="Test Website",
            url="https://test.com",
            status=WebsiteStatus.ACTIVE,
            created_at=now,
            updated_at=now,
            total_verifications=100,
            human_rate=85.5,
            avg_confidence=0.92
        )
        
        # Test object creation
        self.assertEqual(website.id, "test-id")
        self.assertEqual(website.name, "Test Website")
        self.assertEqual(website.status, WebsiteStatus.ACTIVE)
        
        # Test serialization
        data_dict = website.to_dict()
        self.assertEqual(data_dict['id'], "test-id")
        self.assertEqual(data_dict['status'], "active")
        self.assertEqual(data_dict['total_verifications'], 100)
        self.assertEqual(data_dict['human_rate'], 85.5)
    
    def test_get_all_websites_success(self):
        """Test successful retrieval of all websites"""
        # Mock database query result
        mock_website = Mock()
        mock_website.website_id = "test-id"
        mock_website.website_name = "Test Website"
        mock_website.website_url = "https://test.com"
        mock_website.status = "active"
        mock_website.created_at = datetime.utcnow()
        mock_website.updated_at = datetime.utcnow()
        
        self.mock_session.query.return_value.order_by.return_value.all.return_value = [mock_website]
        
        # Mock analytics data
        with patch.object(self.service, '_get_website_analytics') as mock_analytics:
            mock_analytics.return_value = {
                'total_verifications': 100,
                'human_rate': 85.0,
                'avg_confidence': 0.92,
                'last_activity': datetime.utcnow()
            }
            
            # Mock integration status
            with patch.object(self.service, '_get_integration_status') as mock_integration:
                mock_integration.return_value = {
                    'status': IntegrationStatus.ACTIVE,
                    'has_token': True,
                    'token_info': {'token': 'test-token'}
                }
                
                # Execute test
                websites = self.service.get_all_websites()
                
                # Assertions
                self.assertEqual(len(websites), 1)
                self.assertEqual(websites[0].id, "test-id")
                self.assertEqual(websites[0].name, "Test Website")
                self.assertEqual(websites[0].total_verifications, 100)
                self.assertEqual(websites[0].integration_status, IntegrationStatus.ACTIVE)
    
    def test_create_website_success(self):
        """Test successful website creation"""
        # Mock UUID generation
        with patch('app.services.website_service.uuid.uuid4') as mock_uuid:
            mock_uuid.return_value.hex = 'test-uuid'
            
            # Mock website model
            with patch('app.services.website_service.Website') as mock_website_class:
                mock_website = Mock()
                mock_website_class.return_value = mock_website
                
                # Execute test
                result = self.service.create_website("Test Site", "https://test.com", "Description")
                
                # Assertions
                self.assertIsInstance(result, WebsiteData)
                self.assertEqual(result.name, "Test Site")
                self.assertEqual(result.integration_status, IntegrationStatus.NOT_INTEGRATED)
                
                # Verify database operations
                self.mock_session.add.assert_called_once()
                self.mock_session.commit.assert_called_once()
    
    def test_create_website_database_error(self):
        """Test website creation with database error"""
        # Mock database exception
        self.mock_session.add.side_effect = Exception("Database error")
        
        # Execute test and expect exception
        with self.assertRaises(Exception):
            self.service.create_website("Test Site", "https://test.com")
    
    def test_get_website_analytics_with_cache(self):
        """Test analytics retrieval with Redis cache"""
        # Mock cached data
        cached_data = {
            'total_verifications': 50,
            'human_rate': 80.0,
            'avg_confidence': 0.88
        }
        self.mock_redis.get.return_value = json.dumps(cached_data).encode()
        
        # Execute test
        result = self.service._get_website_analytics("test-id", self.mock_session)
        
        # Assertions
        self.assertEqual(result, cached_data)
        self.mock_redis.get.assert_called_once()
    
    def test_get_website_analytics_without_cache(self):
        """Test analytics calculation without cache"""
        # Mock no cache
        self.mock_redis.get.return_value = None
        
        # Mock verification logs
        mock_logs = []
        for i in range(10):
            log = Mock()
            log.timestamp = datetime.utcnow()
            log.confidence = 0.9
            log.is_human = i % 2 == 0  # 50% human
            mock_logs.append(log)
        
        self.mock_session.query.return_value.filter.return_value.all.return_value = mock_logs
        
        # Execute test
        result = self.service._get_website_analytics("test-id", self.mock_session)
        
        # Assertions
        self.assertEqual(result['total_verifications'], 10)
        self.assertEqual(result['human_rate'], 50.0)  # 50% human rate
        self.assertEqual(result['avg_confidence'], 0.9)
        
        # Verify cache was set
        self.mock_redis.setex.assert_called_once()
    
    def test_update_website_success(self):
        """Test successful website update"""
        # Mock existing website
        mock_website = Mock()
        mock_website.website_name = "Old Name"
        mock_website.website_url = "https://old.com"
        
        self.mock_session.query.return_value.filter.return_value.first.return_value = mock_website
        
        # Execute test
        result = self.service.update_website("test-id", name="New Name", url="https://new.com")
        
        # Assertions
        self.assertTrue(result)
        self.assertEqual(mock_website.website_name, "New Name")
        self.assertEqual(mock_website.website_url, "https://new.com")
        self.mock_session.commit.assert_called_once()
    
    def test_update_website_not_found(self):
        """Test updating non-existent website"""
        # Mock no website found
        self.mock_session.query.return_value.filter.return_value.first.return_value = None
        
        # Execute test
        result = self.service.update_website("non-existent", name="New Name")
        
        # Assertions
        self.assertFalse(result)
        self.mock_session.commit.assert_not_called()
    
    def test_delete_website_success(self):
        """Test successful website deletion"""
        # Mock existing website
        mock_website = Mock()
        mock_website.website_name = "Test Website"
        
        self.mock_session.query.return_value.filter.return_value.first.return_value = mock_website
        
        # Execute test
        result = self.service.delete_website("test-id")
        
        # Assertions
        self.assertTrue(result)
        self.mock_session.delete.assert_called_once_with(mock_website)
        self.mock_session.commit.assert_called_once()
        self.mock_token_manager.revoke_token.assert_called_once_with("test-id")
    
    def test_toggle_website_status(self):
        """Test website status toggling"""
        # Mock existing website
        mock_website = Mock()
        mock_website.status = "active"
        
        self.mock_session.query.return_value.filter.return_value.first.return_value = mock_website
        
        # Execute test
        result = self.service.toggle_website_status("test-id")
        
        # Assertions
        self.assertEqual(result, WebsiteStatus.INACTIVE)
        self.assertEqual(mock_website.status, "inactive")
        self.mock_session.commit.assert_called_once()
    
    def test_get_website_statistics(self):
        """Test website statistics calculation"""
        # Mock database queries
        self.mock_session.query.return_value.count.return_value = 10  # total websites
        self.mock_session.query.return_value.filter.return_value.count.return_value = 7  # active websites
        self.mock_session.query.return_value.scalar.return_value = 1000  # total verifications
        
        # Mock token manager stats
        self.mock_token_manager.get_token_stats.return_value = {
            'total_tokens': 5,
            'active_tokens': 3,
            'pending_tokens': 1
        }
        
        # Execute test
        stats = self.service.get_website_statistics()
        
        # Assertions
        self.assertEqual(stats['total_websites'], 10)
        self.assertEqual(stats['active_websites'], 7)
        self.assertEqual(stats['inactive_websites'], 3)
        self.assertEqual(stats['total_verifications'], 1000)
        self.assertEqual(stats['integration_stats']['total_tokens'], 5)
    
    def test_cache_operations(self):
        """Test Redis cache operations"""
        # Test cache clearing
        self.mock_redis.scan_iter.return_value = ['website:key1', 'website:key2']
        
        self.service._clear_website_cache()
        
        # Verify cache clearing
        self.mock_redis.scan_iter.assert_called_once()
        self.assertEqual(self.mock_redis.delete.call_count, 2)
    
    def test_integration_status_mapping(self):
        """Test script integration status mapping"""
        # Mock script token with different statuses
        mock_token = Mock()
        mock_token.status = Mock()
        mock_token.to_dict.return_value = {'token': 'test-token'}
        
        # Test active status
        from app.services.website_service import TokenStatus
        mock_token.status = TokenStatus.ACTIVE
        
        result = self.service._get_integration_status("test-id", self.mock_token_manager)
        self.mock_token_manager.get_website_token.return_value = mock_token
        
        result = self.service._get_integration_status("test-id", self.mock_token_manager)
        self.assertEqual(result['status'], IntegrationStatus.ACTIVE)
        self.assertTrue(result['has_token'])


if __name__ == '__main__':
    # Configure logging for tests
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Run tests
    unittest.main(verbosity=2)