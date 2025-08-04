#!/usr/bin/env python3
"""
Province Data Initialization Script
Populates Neo4j database with official Finnish province data from Statistics Finland
"""

import sys
import os
import asyncio
import logging
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.neo4j_integration import Neo4jConnectionManager
from data_collection.administrative.statistics_finland_collector import StatisticsFinlandCollector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ProvinceDataInitializer:
    """Initialize Neo4j database with official Finnish province data"""
    
    def __init__(self):
        self.neo4j_manager = Neo4jConnectionManager()
        self.stats_collector = StatisticsFinlandCollector()
        
    async def create_schema(self):
        """Create Neo4j schema for provinces"""
        logger.info("Creating Neo4j schema for provinces...")
        
        schema_queries = [
            # Create constraints
            "CREATE CONSTRAINT province_id_unique IF NOT EXISTS FOR (p:Province) REQUIRE p.province_id IS UNIQUE",
            
            # Create indexes
            "CREATE INDEX province_name_fi IF NOT EXISTS FOR (p:Province) ON (p.name_fi)",
            "CREATE INDEX province_name_en IF NOT EXISTS FOR (p:Province) ON (p.name_en)",
            "CREATE INDEX province_population IF NOT EXISTS FOR (p:Province) ON (p.population)",
            "CREATE INDEX province_area IF NOT EXISTS FOR (p:Province) ON (p.area_km2)"
        ]
        
        for query in schema_queries:
            try:
                await self.neo4j_manager.execute_query(query)
                logger.info(f"Executed: {query}")
            except Exception as e:
                logger.warning(f"Schema query failed (may already exist): {query} - {str(e)}")
    
    async def populate_provinces(self):
        """Populate database with official province data"""
        logger.info("Fetching official province data from Statistics Finland...")
        
        # Get official province data
        provinces = self.stats_collector.get_all_regions()
        
        if not provinces:
            logger.error("Failed to fetch province data from Statistics Finland")
            return False
        
        logger.info(f"Fetched {len(provinces)} provinces from Statistics Finland")
        
        # Insert/update provinces in Neo4j
        for province in provinces:
            query = """
            MERGE (p:Province {province_id: $province_id})
            ON CREATE SET p.created_at = datetime()
            ON MATCH SET p.updated_at = datetime()
            SET p.name_fi = $name_fi,
                p.name_sv = $name_sv,
                p.name_en = $name_en,
                p.population = $population,
                p.area_km2 = $area_km2,
                p.population_density = $population_density,
                p.capital = $capital,
                p.coordinates = $coordinates,
                p.municipalities = $municipalities,
                p.last_updated = $last_updated,
                p.source = $source,
                p.is_active = true
            RETURN p.province_id as id, p.name_fi as name
            """
            
            try:
                coords = province["coordinates"]
                if isinstance(coords, dict):
                    coords = [coords.get("lon"), coords.get("lat")]
                result = await self.neo4j_manager.execute_query(query, {
                    "province_id": province["region_id"],
                    "name_fi": province["name_fi"],
                    "name_sv": province["name_sv"],
                    "name_en": province["name_en"],
                    "population": province["population"],
                    "area_km2": province["area_km2"],
                    "population_density": province["population_density"],
                    "capital": province["capital"],
                    "coordinates": coords,
                    "municipalities": province["municipalities"],
                    "last_updated": province["last_updated"],
                    "source": province["source"]
                })
                
                if result:
                    logger.info(f"✅ Populated: {result[0]['name']} ({result[0]['id']})")
                
            except Exception as e:
                logger.error(f"Failed to populate province {province['region_id']}: {str(e)}")
        
        return True
    
    async def verify_data(self):
        """Verify province data was populated correctly"""
        logger.info("Verifying province data in Neo4j...")
        
        query = """
        MATCH (p:Province)
        RETURN p.province_id as id, p.name_fi as name_fi, p.population as population,
               p.area_km2 as area, p.capital as capital, p.source as source
        ORDER BY p.name_fi
        """
        
        results = await self.neo4j_manager.execute_query(query)
        
        if not results:
            logger.error("❌ No province data found in database")
            return False
        
        logger.info(f"✅ Found {len(results)} provinces in database:")
        
        total_population = 0
        total_area = 0
        
        for province in results:
            logger.info(f"  • {province['name_fi']} ({province['id']}) - "
                       f"Pop: {province['population']:,}, Area: {province['area']:,.0f} km², "
                       f"Capital: {province['capital']}")
            total_population += province['population']
            total_area += province['area']
        
        logger.info(f"📊 Total Finland - Pop: {total_population:,}, Area: {total_area:,.0f} km²")
        
        # Verify expected provinces are present
        expected_provinces = [
            "uusimaa", "varsinais-suomi", "satakunta", "kanta-hame", "pirkanmaa",
            "paijat-hame", "kymenlaakso", "etela-karjala", "etela-savo", "pohjois-savo",
            "pohjois-karjala", "keski-suomi", "etela-pohjanmaa", "pohjanmaa", "keski-pohjanmaa",
            "pohjois-pohjanmaa", "kainuu", "lappi", "ahvenanmaa"
        ]
        
        found_provinces = [p['id'] for p in results]
        missing_provinces = set(expected_provinces) - set(found_provinces)
        
        if missing_provinces:
            logger.warning(f"⚠️  Missing provinces: {missing_provinces}")
        else:
            logger.info("✅ All 19 expected provinces are present")
        
        return len(results) >= 19
    
    async def initialize(self):
        """Complete initialization process"""
        logger.info("🚀 Starting province data initialization...")
        
        try:
            # Step 0: Initialize Neo4j connection
            logger.info("Initializing Neo4j connection...")
            success = await self.neo4j_manager.initialize()
            if not success:
                logger.error("❌ Failed to initialize Neo4j connection")
                return False
            logger.info("✅ Neo4j connection initialized successfully")
            
            # Step 1: Create schema
            await self.create_schema()
            
            # Step 2: Populate data
            success = await self.populate_provinces()
            if not success:
                logger.error("❌ Failed to populate province data")
                return False
            
            # Step 3: Verify data
            verified = await self.verify_data()
            if not verified:
                logger.error("❌ Data verification failed")
                return False
            
            logger.info("✅ Province data initialization completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Initialization failed: {str(e)}")
            return False
        finally:
            await self.neo4j_manager.close()

async def main():
    """Main initialization function"""
    initializer = ProvinceDataInitializer()
    success = await initializer.initialize()
    
    if success:
        print("\n🎯 SUCCESS: Neo4j database populated with official Finnish province data!")
        print("📊 19 provinces with live demographics from Statistics Finland")
        print("🔗 Ready for frontend integration and API testing")
    else:
        print("\n❌ FAILED: Province data initialization unsuccessful")
        print("🔧 Check logs for details and retry")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())
