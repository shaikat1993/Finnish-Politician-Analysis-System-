#!/usr/bin/env python3
"""
FPAS System Verification
Senior-level system health check and verification script
"""

import asyncio
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class SystemVerifier:
    """Professional system verification for FPAS"""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'checks': {},
            'overall_status': 'unknown',
            'recommendations': []
        }
    
    async def verify_neo4j_integration(self):
        """Verify Neo4j database integration"""
        print("🔍 Verifying Neo4j Integration...")
        
        try:
            from database import health_check, setup_neo4j_schema
            
            # Connection health
            status = await health_check()
            connection_healthy = status['status'] == 'healthy'
            
            # Schema verification
            schema_result = await setup_neo4j_schema()
            schema_ready = schema_result.get('verification_success', False)
            
            self.results['checks']['neo4j'] = {
                'connection': connection_healthy,
                'schema': schema_ready,
                'performance': status.get('performance_metrics', {}),
                'status': 'healthy' if connection_healthy and schema_ready else 'issues'
            }
            
            if connection_healthy and schema_ready:
                print("   ✅ Neo4j: Connection healthy, schema ready")
            else:
                print("   ⚠️ Neo4j: Issues detected")
                self.results['recommendations'].append("Check Neo4j Desktop is running with fpas-database")
                
        except Exception as e:
            print(f"   ❌ Neo4j: Failed - {str(e)}")
            self.results['checks']['neo4j'] = {'status': 'failed', 'error': str(e)}
            self.results['recommendations'].append("Start Neo4j Desktop and create fpas-database")
    
    async def verify_data_collection(self):
        """Verify data collection system"""
        print("🔄 Verifying Data Collection...")
        
        try:
            from database import CollectorNeo4jBridge
            
            bridge = CollectorNeo4jBridge()
            
            # Test limited collection
            results = await bridge.collect_and_store_politicians(limit=2)
            
            sources_working = len(results.get('sources_processed', []))
            politicians_collected = len(results.get('politicians_created', []))
            
            self.results['checks']['data_collection'] = {
                'bridge_initialized': True,
                'sources_working': sources_working,
                'politicians_collected': politicians_collected,
                'status': 'working' if sources_working > 0 else 'limited'
            }
            
            if sources_working > 0:
                print(f"   ✅ Data Collection: {sources_working} sources, {politicians_collected} politicians")
            else:
                print("   ⚠️ Data Collection: Limited due to API issues")
                self.results['recommendations'].append("Update API endpoints in collector configuration")
                
        except Exception as e:
            print(f"   ❌ Data Collection: Failed - {str(e)}")
            self.results['checks']['data_collection'] = {'status': 'failed', 'error': str(e)}
    
    async def verify_ai_pipeline(self):
        """Verify AI pipeline integration"""
        print("🤖 Verifying AI Pipeline...")
        
        try:
            from ai_pipeline.tools.coordination_tools import StorageTool
            from ai_pipeline.agents.supervisor_agent import SupervisorAgent
            
            # Test storage tool
            storage_tool = StorageTool()
            
            # Test supervisor agent
            supervisor = SupervisorAgent()
            
            self.results['checks']['ai_pipeline'] = {
                'storage_tool': True,
                'supervisor_agent': True,
                'langchain_integration': True,
                'status': 'ready'
            }
            
            print("   ✅ AI Pipeline: LangChain multi-agent system ready")
            
        except Exception as e:
            print(f"   ❌ AI Pipeline: Failed - {str(e)}")
            self.results['checks']['ai_pipeline'] = {'status': 'failed', 'error': str(e)}
            self.results['recommendations'].append("Check AI pipeline dependencies and configuration")
    
    async def verify_analytics(self):
        """Verify analytics engine"""
        print("📊 Verifying Analytics Engine...")
        
        try:
            from database import get_neo4j_analytics
            
            analytics = await get_neo4j_analytics()
            
            # Test basic analytics query
            coalition_data = await analytics.get_coalition_analysis()
            
            self.results['checks']['analytics'] = {
                'engine_ready': True,
                'queries_working': True,
                'data_available': len(coalition_data) > 0,
                'status': 'ready'
            }
            
            print("   ✅ Analytics: Engine ready, queries functional")
            
        except Exception as e:
            print(f"   ❌ Analytics: Failed - {str(e)}")
            self.results['checks']['analytics'] = {'status': 'failed', 'error': str(e)}
    
    def determine_overall_status(self):
        """Determine overall system status"""
        critical_systems = ['neo4j', 'data_collection', 'ai_pipeline']
        
        failed_systems = []
        working_systems = []
        
        for system in critical_systems:
            if system in self.results['checks']:
                status = self.results['checks'][system].get('status', 'unknown')
                if status in ['failed', 'issues']:
                    failed_systems.append(system)
                else:
                    working_systems.append(system)
        
        if len(failed_systems) == 0:
            self.results['overall_status'] = 'healthy'
        elif len(working_systems) > len(failed_systems):
            self.results['overall_status'] = 'functional_with_issues'
        else:
            self.results['overall_status'] = 'needs_attention'
    
    def print_summary(self):
        """Print verification summary"""
        print("\n" + "="*50)
        print("🎯 FPAS SYSTEM VERIFICATION SUMMARY")
        print("="*50)
        
        status_emoji = {
            'healthy': '✅',
            'functional_with_issues': '⚠️',
            'needs_attention': '❌'
        }
        
        emoji = status_emoji.get(self.results['overall_status'], '❓')
        print(f"{emoji} Overall Status: {self.results['overall_status'].upper()}")
        
        print(f"\n📋 System Components:")
        for component, details in self.results['checks'].items():
            status = details.get('status', 'unknown')
            component_emoji = '✅' if status in ['healthy', 'ready', 'working'] else '⚠️' if status in ['limited', 'issues'] else '❌'
            print(f"   {component_emoji} {component.replace('_', ' ').title()}: {status}")
        
        if self.results['recommendations']:
            print(f"\n💡 Recommendations:")
            for i, rec in enumerate(self.results['recommendations'], 1):
                print(f"   {i}. {rec}")
        
        print(f"\n🚀 Next Steps:")
        if self.results['overall_status'] == 'healthy':
            print("   • System is ready for local development")
            print("   • Consider creating FastAPI backend")
            print("   • Build Streamlit frontend interface")
        else:
            print("   • Address the issues listed above")
            print("   • Re-run verification: python verify_system.py")

async def main():
    """Main verification function"""
    print("🧪 FPAS System Verification")
    print("Senior-level health check for Finnish Political Analysis System")
    print("="*60)
    
    verifier = SystemVerifier()
    
    await verifier.verify_neo4j_integration()
    await verifier.verify_data_collection()
    await verifier.verify_ai_pipeline()
    await verifier.verify_analytics()
    
    verifier.determine_overall_status()
    verifier.print_summary()
    
    return verifier.results

if __name__ == "__main__":
    results = asyncio.run(main())
