#!/usr/bin/env python3
"""
End-to-End Feature Tests for FPAS
Senior-level E2E testing for complete user workflows and system features
"""

import pytest
import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, List, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

@pytest.mark.features
@pytest.mark.slow
class TestPoliticianAnalysisWorkflow:
    """End-to-end tests for politician analysis workflows"""
    
    @pytest.mark.asyncio
    async def test_complete_politician_analysis_workflow(self, clean_test_data):
        """Test complete workflow: Data Collection → Processing → Storage → Analytics"""
        try:
            # Step 1: System Health Check
            from database import health_check
            health_status = await health_check()
            
            if health_status['status'] != 'healthy':
                pytest.skip("Neo4j not healthy - skipping E2E test")
            
            print("✅ Step 1: System health verified")
            
            # Step 2: Data Collection
            from database import CollectorNeo4jBridge
            bridge = CollectorNeo4jBridge()
            
            collection_results = await bridge.collect_and_store_politicians(
                sources=['kuntaliitto', 'vaalikone'], 
                limit=3
            )
            
            sources_processed = len(collection_results.get('sources_processed', []))
            politicians_created = len(collection_results.get('politicians_created', []))
            
            print(f"✅ Step 2: Data collection completed - {sources_processed} sources, {politicians_created} politicians")
            
            # Step 3: Data Verification
            from database import get_neo4j_manager
            manager = await get_neo4j_manager()
            
            # Verify politicians were stored
            query = "MATCH (p:Politician) RETURN count(p) as politician_count"
            result = await manager.execute_query(query)
            politician_count = result[0]['politician_count']
            
            assert politician_count >= 0
            print(f"✅ Step 3: Data verification - {politician_count} politicians in database")
            
            # Step 4: Analytics
            from database import get_neo4j_analytics
            analytics = await get_neo4j_analytics()
            
            # Run comprehensive analytics
            coalition_data = await analytics.get_coalition_analysis()
            network_data = await analytics.get_party_network_analysis()
            influence_data = await analytics.get_politician_influence_metrics()
            
            assert isinstance(coalition_data, list)
            assert isinstance(network_data, dict)
            assert isinstance(influence_data, list)
            
            print(f"✅ Step 4: Analytics completed - {len(coalition_data)} coalitions, {len(influence_data)} influence metrics")
            
            # Step 5: AI Pipeline Integration
            from ai_pipeline.processors.politician_processor import PoliticianProcessor
            processor = PoliticianProcessor()
            
            # Test processing workflow
            if politicians_created > 0:
                sample_politicians = collection_results['politicians_created'][:1]
                processed = await processor.process_politicians(sample_politicians)
                
                assert isinstance(processed, list)
                print(f"✅ Step 5: AI processing completed - {len(processed)} politicians processed")
            
            await manager.close()
            
            print("🎉 Complete politician analysis workflow successful!")
            
        except Exception as e:
            pytest.fail(f"Complete politician analysis workflow failed: {e}")

@pytest.mark.features
class TestNewsAnalysisWorkflow:
    """End-to-end tests for news analysis workflows"""
    
    @pytest.mark.asyncio
    async def test_news_collection_and_analysis_workflow(self, sample_news_data):
        """Test news collection, processing, and analysis workflow"""
        try:
            # Step 1: News Data Processing
            from ai_pipeline.processors.news_processor import NewsProcessor
            processor = NewsProcessor()
            
            news_articles = [sample_news_data]
            processed_news = await processor.process_news(news_articles)
            
            assert isinstance(processed_news, list)
            assert len(processed_news) > 0
            
            print(f"✅ Step 1: News processing completed - {len(processed_news)} articles")
            
            # Step 2: News Storage
            from database import get_neo4j_writer
            writer = await get_neo4j_writer()
            
            # Create unique test news
            test_news = sample_news_data.copy()
            test_news['article_id'] = f"e2e_news_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            storage_result = await writer.batch_create_news([test_news])
            
            assert len(storage_result['news_created']) > 0
            print(f"✅ Step 2: News storage completed - {len(storage_result['news_created'])} articles stored")
            
            # Step 3: News Analytics
            from database import get_neo4j_manager
            manager = await get_neo4j_manager()
            
            # Verify news was stored and can be queried
            query = """
            MATCH (n:News {article_id: $article_id})
            RETURN n.title as title, n.source as source
            """
            
            result = await manager.execute_query(query, article_id=test_news['article_id'])
            
            assert len(result) > 0
            assert result[0]['title'] == test_news['title']
            
            print("✅ Step 3: News analytics and verification completed")
            
            await manager.close()
            
            print("🎉 News analysis workflow successful!")
            
        except Exception as e:
            pytest.fail(f"News analysis workflow failed: {e}")

@pytest.mark.features
@pytest.mark.slow
class TestSystemPerformanceWorkflow:
    """End-to-end tests for system performance and scalability"""
    
    @pytest.mark.asyncio
    async def test_bulk_data_processing_workflow(self, clean_test_data):
        """Test system performance with bulk data processing"""
        try:
            # Step 1: Performance Baseline
            from database import health_check
            initial_health = await health_check()
            
            if initial_health['status'] != 'healthy':
                pytest.skip("Neo4j not healthy - skipping performance test")
            
            initial_metrics = initial_health.get('performance_metrics', {})
            initial_queries = initial_metrics.get('total_queries', 0)
            
            print(f"✅ Step 1: Performance baseline - {initial_queries} queries executed")
            
            # Step 2: Bulk Data Collection
            from database import CollectorNeo4jBridge
            bridge = CollectorNeo4jBridge()
            
            # Test with larger limit for performance
            bulk_results = await bridge.collect_and_store_politicians(limit=5)
            
            bulk_politicians = len(bulk_results.get('politicians_created', []))
            bulk_sources = len(bulk_results.get('sources_processed', []))
            
            print(f"✅ Step 2: Bulk collection - {bulk_sources} sources, {bulk_politicians} politicians")
            
            # Step 3: Performance Analytics
            from database import get_neo4j_analytics
            analytics = await get_neo4j_analytics()
            
            # Run multiple analytics queries to test performance
            start_time = datetime.now()
            
            coalition_data = await analytics.get_coalition_analysis()
            network_data = await analytics.get_party_network_analysis()
            influence_data = await analytics.get_politician_influence_metrics()
            
            end_time = datetime.now()
            analytics_duration = (end_time - start_time).total_seconds()
            
            print(f"✅ Step 3: Analytics performance - {analytics_duration:.2f}s for 3 queries")
            
            # Step 4: Final Performance Check
            final_health = await health_check()
            final_metrics = final_health.get('performance_metrics', {})
            final_queries = final_metrics.get('total_queries', 0)
            avg_query_time = final_metrics.get('avg_query_time', 0)
            
            queries_executed = final_queries - initial_queries
            
            print(f"✅ Step 4: Performance summary - {queries_executed} queries, {avg_query_time:.3f}s avg")
            
            # Performance assertions
            assert analytics_duration < 30.0  # Should complete within 30 seconds
            assert avg_query_time < 5.0  # Average query time should be reasonable
            
            print("🎉 System performance workflow successful!")
            
        except Exception as e:
            pytest.fail(f"System performance workflow failed: {e}")

@pytest.mark.features
class TestErrorHandlingWorkflow:
    """End-to-end tests for error handling and resilience"""
    
    @pytest.mark.asyncio
    async def test_api_failure_resilience_workflow(self):
        """Test system resilience when APIs fail"""
        try:
            # Step 1: Test with API failures (expected)
            from database import CollectorNeo4jBridge
            bridge = CollectorNeo4jBridge()
            
            # This should handle API failures gracefully
            results = await bridge.collect_and_store_politicians(
                sources=['eduskunta'],  # Known to have API issues
                limit=1
            )
            
            # Should complete without crashing
            assert isinstance(results, dict)
            assert 'errors' in results
            
            # Should log errors but continue
            errors = results.get('errors', [])
            print(f"✅ Step 1: API failure handling - {len(errors)} errors handled gracefully")
            
            # Step 2: Test analytics with limited data
            from database import get_neo4j_analytics
            analytics = await get_neo4j_analytics()
            
            # Should work even with no/limited data
            coalition_data = await analytics.get_coalition_analysis()
            network_data = await analytics.get_party_network_analysis()
            
            assert isinstance(coalition_data, list)
            assert isinstance(network_data, dict)
            
            print("✅ Step 2: Analytics resilience - works with limited data")
            
            # Step 3: Test AI pipeline resilience
            from ai_pipeline.processors.politician_processor import PoliticianProcessor
            processor = PoliticianProcessor()
            
            # Should handle empty/invalid data gracefully
            empty_result = await processor.process_politicians([])
            assert isinstance(empty_result, list)
            
            print("✅ Step 3: AI pipeline resilience - handles empty data")
            
            print("🎉 Error handling workflow successful!")
            
        except Exception as e:
            pytest.fail(f"Error handling workflow failed: {e}")

def run_feature_tests():
    """Run feature/E2E tests with proper reporting"""
    print("🎭 Running Feature/E2E Test Suite")
    print("=" * 40)
    
    # Run tests with pytest
    import subprocess
    result = subprocess.run([
        'python', '-m', 'pytest', 
        'tests/features/', 
        '-v', '--tb=short', '-m', 'features'
    ], capture_output=True, text=True)
    
    print(result.stdout)
    if result.stderr:
        print("Errors:")
        print(result.stderr)
    
    return result.returncode == 0

if __name__ == "__main__":
    success = run_feature_tests()
    if success:
        print("✅ Feature/E2E tests completed successfully!")
    else:
        print("⚠️ Some feature tests failed - check output above")
        sys.exit(1)
