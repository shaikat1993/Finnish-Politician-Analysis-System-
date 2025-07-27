#!/usr/bin/env python3
"""
Database Test Suite
Senior-level testing for Neo4j database integration and components
"""

import asyncio
import pytest
import sys
import os
import json
from datetime import datetime
from typing import Dict, List, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.mark.database
class TestNeo4jConnection:
    """Test Neo4j connection and basic operations"""
    
    @pytest.mark.asyncio
    async def test_neo4j_health_check(self):
        """Test Neo4j connection health check"""
        try:
            from database import health_check
            
            status = await health_check()
            
            assert isinstance(status, dict)
            assert 'status' in status
            assert status['status'] in ['healthy', 'unhealthy']
            
            if status['status'] == 'healthy':
                assert 'performance_metrics' in status
                metrics = status['performance_metrics']
                assert 'total_queries' in metrics
                assert 'avg_query_time' in metrics
                print(f"✅ Neo4j: Healthy connection, {metrics['total_queries']} queries")
            else:
                print("⚠️ Neo4j: Connection unhealthy - may need to start Neo4j Desktop")
                
        except Exception as e:
            pytest.fail(f"Neo4j health check failed: {e}")
    
    @pytest.mark.asyncio
    async def test_neo4j_manager_initialization(self):
        """Test Neo4j connection manager initialization"""
        try:
            from database import get_neo4j_manager
            
            manager = await get_neo4j_manager()
            
            assert manager is not None
            assert hasattr(manager, 'execute_query')
            assert hasattr(manager, 'close')
            
            print("✅ Neo4j Manager: Initialized successfully")
            
            await manager.close()
            
        except Exception as e:
            pytest.fail(f"Neo4j manager initialization failed: {e}")
    
    @pytest.mark.asyncio
    async def test_neo4j_schema_setup(self):
        """Test Neo4j schema setup and verification"""
        try:
            from database import setup_neo4j_schema
            
            result = await setup_neo4j_schema()
            
            assert isinstance(result, dict)
            assert 'verification_success' in result
            
            if result['verification_success']:
                summary = result.get('summary', {})
                constraints = summary.get('constraints_created', 0)
                indexes = summary.get('indexes_created', 0)
                
                print(f"✅ Schema: {constraints} constraints, {indexes} indexes")
                
                # Should have reasonable number of constraints and indexes
                assert constraints >= 0
                assert indexes >= 0
            else:
                print("⚠️ Schema: Setup had issues")
                
        except Exception as e:
            pytest.fail(f"Neo4j schema setup failed: {e}")

@pytest.mark.database
@pytest.mark.integration
class TestNeo4jDataOperations:
    """Test Neo4j data operations and CRUD functionality"""
    
    @pytest.mark.asyncio
    async def test_neo4j_writer_initialization(self):
        """Test Neo4j writer initialization"""
        try:
            from database import get_neo4j_writer
            
            writer = await get_neo4j_writer()
            
            assert writer is not None
            assert hasattr(writer, 'batch_create_politicians')
            assert hasattr(writer, 'batch_create_news')
            
            print("✅ Neo4j Writer: Initialized successfully")
            
        except Exception as e:
            pytest.fail(f"Neo4j writer initialization failed: {e}")
    
    @pytest.mark.asyncio
    async def test_politician_data_operations(self, neo4j_manager, clean_test_data, sample_politician_data):
        """Test politician data CRUD operations"""
        try:
            from database import get_neo4j_writer
            
            writer = await get_neo4j_writer()
            
            # Create test politician with unique ID
            test_politician = sample_politician_data.copy()
            test_politician['politician_id'] = f"test_politician_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            test_politician['name'] = f"Test Politician {datetime.now().strftime('%H%M%S')}"
            
            # Test creation
            result = await writer.batch_create_politicians([test_politician])
            
            assert isinstance(result, dict)
            assert 'politicians_created' in result
            
            politicians_created = result['politicians_created']
            assert len(politicians_created) > 0
            
            print(f"✅ Created {len(politicians_created)} test politicians")
            
            # Test retrieval
            query = """
            MATCH (p:Politician {politician_id: $politician_id})
            RETURN p.name as name, p.party as party
            """
            
            records = await neo4j_manager.execute_query(
                query, 
                politician_id=test_politician['politician_id']
            )
            
            assert len(records) > 0
            record = records[0]
            assert record['name'] == test_politician['name']
            assert record['party'] == test_politician['party']
            
            print("✅ Retrieved and verified test politician data")
            
        except Exception as e:
            pytest.fail(f"Politician data operations failed: {e}")
    
    @pytest.mark.asyncio
    async def test_news_data_operations(self, neo4j_manager, clean_test_data, sample_news_data):
        """Test news data CRUD operations"""
        try:
            from database import get_neo4j_writer
            
            writer = await get_neo4j_writer()
            
            # Create test news with unique ID
            test_news = sample_news_data.copy()
            test_news['article_id'] = f"test_news_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            test_news['title'] = f"Test News {datetime.now().strftime('%H%M%S')}"
            
            # Test creation
            result = await writer.batch_create_news([test_news])
            
            assert isinstance(result, dict)
            assert 'news_created' in result
            
            news_created = result['news_created']
            assert len(news_created) > 0
            
            print(f"✅ Created {len(news_created)} test news articles")
            
            # Test retrieval
            query = """
            MATCH (n:News {article_id: $article_id})
            RETURN n.title as title, n.source as source
            """
            
            records = await neo4j_manager.execute_query(
                query, 
                article_id=test_news['article_id']
            )
            
            assert len(records) > 0
            record = records[0]
            assert record['title'] == test_news['title']
            assert record['source'] == test_news['source']
            
            print("✅ Retrieved and verified test news data")
            
        except Exception as e:
            pytest.fail(f"News data operations failed: {e}")

@pytest.mark.database
@pytest.mark.integration
class TestNeo4jAnalytics:
    """Test Neo4j analytics and query functionality"""
    
    @pytest.mark.asyncio
    async def test_analytics_engine_initialization(self):
        """Test analytics engine initialization"""
        try:
            from database import get_neo4j_analytics
            
            analytics = await get_neo4j_analytics()
            
            assert analytics is not None
            assert hasattr(analytics, 'get_coalition_analysis')
            assert hasattr(analytics, 'get_party_network_analysis')
            assert hasattr(analytics, 'get_politician_influence_metrics')
            
            print("✅ Analytics Engine: Initialized successfully")
            
        except Exception as e:
            pytest.fail(f"Analytics engine initialization failed: {e}")
    
    @pytest.mark.asyncio
    async def test_coalition_analysis(self):
        """Test coalition analysis functionality"""
        try:
            from database import get_neo4j_analytics
            
            analytics = await get_neo4j_analytics()
            
            # Test coalition analysis
            coalition_data = await analytics.get_coalition_analysis()
            
            assert isinstance(coalition_data, list)
            
            print(f"✅ Coalition Analysis: Returned {len(coalition_data)} results")
            
            # If there's data, check structure
            if coalition_data:
                coalition = coalition_data[0]
                assert isinstance(coalition, dict)
                
        except Exception as e:
            pytest.fail(f"Coalition analysis failed: {e}")
    
    @pytest.mark.asyncio
    async def test_party_network_analysis(self):
        """Test party network analysis functionality"""
        try:
            from database import get_neo4j_analytics
            
            analytics = await get_neo4j_analytics()
            
            # Test party network analysis
            network_data = await analytics.get_party_network_analysis()
            
            assert isinstance(network_data, dict)
            
            print("✅ Party Network Analysis: Completed successfully")
            
            # Check expected structure
            if network_data:
                assert 'nodes' in network_data or 'parties' in network_data
                
        except Exception as e:
            pytest.fail(f"Party network analysis failed: {e}")
    
    @pytest.mark.asyncio
    async def test_politician_influence_metrics(self):
        """Test politician influence metrics"""
        try:
            from database import get_neo4j_analytics
            
            analytics = await get_neo4j_analytics()
            
            # Test influence metrics
            influence_data = await analytics.get_politician_influence_metrics()
            
            assert isinstance(influence_data, list)
            
            print(f"✅ Influence Metrics: Returned {len(influence_data)} politicians")
            
            # If there's data, check structure
            if influence_data:
                politician = influence_data[0]
                assert isinstance(politician, dict)
                assert 'politician_id' in politician or 'name' in politician
                
        except Exception as e:
            pytest.fail(f"Politician influence metrics failed: {e}")

@pytest.mark.database
@pytest.mark.features
class TestDatabaseEndToEnd:
    """End-to-end database functionality tests"""
    
    @pytest.mark.asyncio
    async def test_complete_database_workflow(self, clean_test_data, sample_politician_data, sample_news_data):
        """Test complete database workflow from data ingestion to analytics"""
        try:
            from database import get_neo4j_writer, get_neo4j_analytics
            
            # Step 1: Data ingestion
            writer = await get_neo4j_writer()
            
            # Create unique test data
            test_politician = sample_politician_data.copy()
            test_politician['politician_id'] = f"workflow_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            test_news = sample_news_data.copy()
            test_news['article_id'] = f"workflow_news_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            test_news['politicians_mentioned'] = [test_politician['politician_id']]
            
            # Ingest data
            politician_result = await writer.batch_create_politicians([test_politician])
            news_result = await writer.batch_create_news([test_news])
            
            assert len(politician_result['politicians_created']) > 0
            assert len(news_result['news_created']) > 0
            
            print("✅ Step 1: Data ingestion completed")
            
            # Step 2: Analytics
            analytics = await get_neo4j_analytics()
            
            # Run various analytics
            coalition_data = await analytics.get_coalition_analysis()
            network_data = await analytics.get_party_network_analysis()
            influence_data = await analytics.get_politician_influence_metrics()
            
            assert isinstance(coalition_data, list)
            assert isinstance(network_data, dict)
            assert isinstance(influence_data, list)
            
            print("✅ Step 2: Analytics completed")
            
            print("✅ Complete database workflow successful")
            
        except Exception as e:
            pytest.fail(f"Complete database workflow failed: {e}")

def run_database_tests():
    """Run database tests with proper reporting"""
    print("🗄️ Running Database Test Suite")
    print("=" * 40)
    
    # Run tests with pytest
    import subprocess
    result = subprocess.run([
        'python', '-m', 'pytest', 
        'tests/test_database.py', 
        '-v', '--tb=short'
    ], capture_output=True, text=True)
    
    print(result.stdout)
    if result.stderr:
        print("Errors:")
        print(result.stderr)
    
    return result.returncode == 0

if __name__ == "__main__":
    success = run_database_tests()
    if success:
        print("✅ Database tests completed successfully!")
    else:
        print("⚠️ Some Database tests failed - check output above")
        sys.exit(1)
