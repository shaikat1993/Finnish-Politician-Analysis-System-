import sys
print(f"Python version: {sys.version}")
try:
    import neo4j
    print(f"Neo4j package found at: {neo4j.__file__}")
    print(f"Neo4j version: {getattr(neo4j, '__version__', 'unknown')}")
    
    from neo4j import AsyncGraphDatabase
    print("AsyncGraphDatabase import successful")
except ImportError as e:
    print(f"Import failed: {e}")
    if 'neo4j' in locals():
        print(f"Dir neo4j: {dir(neo4j)}")
except Exception as e:
    print(f"Unexpected error: {e}")
