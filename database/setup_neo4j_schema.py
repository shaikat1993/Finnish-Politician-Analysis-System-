#!/usr/bin/env python3
"""
Neo4j Schema Setup Script
Initializes the optimized Neo4j schema for Finnish Political Analysis System
"""

import asyncio
import logging
import os
from typing import Dict, Any
from neo4j import AsyncGraphDatabase
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class Neo4jSchemaSetup:
    """Setup and initialize Neo4j schema"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.driver = None
        
        # Neo4j connection parameters
        self.uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
        self.user = os.getenv('NEO4J_USER', 'neo4j')
        self.password = os.getenv('NEO4J_PASSWORD', 'password')
        self.database = os.getenv('NEO4J_DATABASE', 'neo4j')
    
    async def connect(self) -> bool:
        """Connect to Neo4j database"""
        try:
            self.driver = AsyncGraphDatabase.driver(
                self.uri, 
                auth=(self.user, self.password)
            )
            
            # Test connection
            async with self.driver.session(database=self.database) as session:
                result = await session.run("RETURN 1 as test")
                await result.single()
            
            self.logger.info(f"Successfully connected to Neo4j at {self.uri}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to Neo4j: {str(e)}")
            return False
    
    async def load_schema_file(self) -> str:
        """Load the optimized schema from file"""
        try:
            schema_path = os.path.join(os.path.dirname(__file__), 'neo4j_schema.cypher')
            
            if not os.path.exists(schema_path):
                raise FileNotFoundError(f"Schema file not found: {schema_path}")
            
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_content = f.read()
            
            self.logger.info(f"Loaded schema from {schema_path}")
            return schema_content
            
        except Exception as e:
            self.logger.error(f"Failed to load schema file: {str(e)}")
            raise
    
    async def execute_schema_commands(self, schema_content: str) -> Dict[str, Any]:
        """Execute schema commands from the loaded content"""
        results = {
            'constraints_created': 0,
            'indexes_created': 0,
            'errors': [],
            'success': True
        }
        
        try:
            # Split schema into individual commands
            commands = [
                cmd.strip() 
                for cmd in schema_content.split(';') 
                if cmd.strip() and not cmd.strip().startswith('//')
            ]
            
            async with self.driver.session(database=self.database) as session:
                for command in commands:
                    if not command:
                        continue
                    
                    try:
                        self.logger.debug(f"Executing: {command[:100]}...")
                        await session.run(command)
                        
                        # Count what we created
                        if 'CREATE CONSTRAINT' in command.upper():
                            results['constraints_created'] += 1
                        elif 'CREATE INDEX' in command.upper():
                            results['indexes_created'] += 1
                            
                    except Exception as e:
                        error_msg = f"Error executing command: {str(e)}"
                        self.logger.warning(error_msg)
                        results['errors'].append(error_msg)
            
            self.logger.info(f"Schema setup completed: {results['constraints_created']} constraints, "
                           f"{results['indexes_created']} indexes created")
            
            if results['errors']:
                self.logger.warning(f"Encountered {len(results['errors'])} errors during setup")
                results['success'] = False
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to execute schema commands: {str(e)}")
            results['success'] = False
            results['errors'].append(str(e))
            return results
    
    async def verify_schema(self) -> Dict[str, Any]:
        """Verify that schema was created successfully"""
        verification = {
            'constraints': [],
            'indexes': [],
            'success': True,
            'errors': []
        }
        
        try:
            async with self.driver.session(database=self.database) as session:
                # Check constraints
                constraints_result = await session.run("SHOW CONSTRAINTS")
                constraints = []
                async for record in constraints_result:
                    constraints.append({
                        'name': record.get('name', ''),
                        'type': record.get('type', ''),
                        'entity_type': record.get('entityType', ''),
                        'properties': record.get('properties', [])
                    })
                
                verification['constraints'] = constraints
                
                # Check indexes
                indexes_result = await session.run("SHOW INDEXES")
                indexes = []
                async for record in indexes_result:
                    indexes.append({
                        'name': record.get('name', ''),
                        'state': record.get('state', ''),
                        'type': record.get('type', ''),
                        'entity_type': record.get('entityType', ''),
                        'properties': record.get('properties', [])
                    })
                
                verification['indexes'] = indexes
                
                self.logger.info(f"Schema verification: {len(constraints)} constraints, "
                               f"{len(indexes)} indexes found")
                
        except Exception as e:
            error_msg = f"Schema verification failed: {str(e)}"
            self.logger.error(error_msg)
            verification['success'] = False
            verification['errors'].append(error_msg)
        
        return verification
    
    async def setup_complete_schema(self) -> Dict[str, Any]:
        """Complete schema setup process"""
        self.logger.info("Starting Neo4j schema setup...")
        
        setup_results = {
            'connection_success': False,
            'schema_loaded': False,
            'schema_executed': False,
            'verification_success': False,
            'summary': {},
            'errors': []
        }
        
        try:
            # Step 1: Connect to Neo4j
            self.logger.info("Step 1: Connecting to Neo4j...")
            connection_success = await self.connect()
            setup_results['connection_success'] = connection_success
            
            if not connection_success:
                setup_results['errors'].append("Failed to connect to Neo4j")
                return setup_results
            
            # Step 2: Load schema file
            self.logger.info("Step 2: Loading schema file...")
            schema_content = await self.load_schema_file()
            setup_results['schema_loaded'] = True
            
            # Step 3: Execute schema commands
            self.logger.info("Step 3: Executing schema commands...")
            execution_results = await self.execute_schema_commands(schema_content)
            setup_results['schema_executed'] = execution_results['success']
            setup_results['summary'] = execution_results
            
            if execution_results['errors']:
                setup_results['errors'].extend(execution_results['errors'])
            
            # Step 4: Verify schema
            self.logger.info("Step 4: Verifying schema...")
            verification_results = await self.verify_schema()
            setup_results['verification_success'] = verification_results['success']
            
            if verification_results['errors']:
                setup_results['errors'].extend(verification_results['errors'])
            
            # Final summary
            if setup_results['verification_success']:
                self.logger.info("✅ Neo4j schema setup completed successfully!")
                self.logger.info(f"   📊 Constraints: {len(verification_results['constraints'])}")
                self.logger.info(f"   📊 Indexes: {len(verification_results['indexes'])}")
            else:
                self.logger.error("❌ Schema setup completed with errors")
            
            return setup_results
            
        except Exception as e:
            error_msg = f"Schema setup failed: {str(e)}"
            self.logger.error(error_msg)
            setup_results['errors'].append(error_msg)
            return setup_results
        
        finally:
            await self.close()
    
    async def close(self):
        """Close database connection"""
        if self.driver:
            await self.driver.close()
            self.logger.info("Neo4j connection closed")

# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

async def setup_neo4j_schema() -> Dict[str, Any]:
    """
    Convenience function to setup Neo4j schema
    
    Returns:
        Dictionary with setup results
    """
    setup = Neo4jSchemaSetup()
    return await setup.setup_complete_schema()

async def verify_neo4j_schema() -> Dict[str, Any]:
    """
    Convenience function to verify existing Neo4j schema
    
    Returns:
        Dictionary with verification results
    """
    setup = Neo4jSchemaSetup()
    
    try:
        connection_success = await setup.connect()
        if not connection_success:
            return {'success': False, 'error': 'Failed to connect to Neo4j'}
        
        verification = await setup.verify_schema()
        return verification
        
    finally:
        await setup.close()

# =============================================================================
# MAIN EXECUTION
# =============================================================================

async def main():
    """Main execution function"""
    print("🚀 Neo4j Schema Setup for Finnish Political Analysis System")
    print("=" * 60)
    
    # Run complete schema setup
    results = await setup_neo4j_schema()
    
    print("\n📊 SETUP RESULTS:")
    print(f"   Connection: {'✅' if results['connection_success'] else '❌'}")
    print(f"   Schema Loaded: {'✅' if results['schema_loaded'] else '❌'}")
    print(f"   Schema Executed: {'✅' if results['schema_executed'] else '❌'}")
    print(f"   Verification: {'✅' if results['verification_success'] else '❌'}")
    
    if 'summary' in results and results['summary']:
        summary = results['summary']
        print(f"   Constraints Created: {summary.get('constraints_created', 0)}")
        print(f"   Indexes Created: {summary.get('indexes_created', 0)}")
    
    if results['errors']:
        print(f"\n⚠️ ERRORS ({len(results['errors'])}):")
        for error in results['errors']:
            print(f"   • {error}")
    
    print(f"\n{'✅ Setup completed successfully!' if results['verification_success'] else '❌ Setup completed with errors'}")

if __name__ == "__main__":
    asyncio.run(main())
