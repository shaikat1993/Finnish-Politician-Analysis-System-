#!/bin/bash
set -e

DUMP_FILE="/import/fpas-database.dump"
DB_NAME="fpas-database"

echo "🚀 Neo4j Database Initialization"

if [ -d "/data/databases/$DB_NAME" ]; then
    echo "✅ Database '$DB_NAME' already exists. Skipping load."
else
    if [ -f "$DUMP_FILE" ]; then
        echo "📦 Loading dump from $DUMP_FILE..."
        neo4j-admin database load "$DB_NAME" \
            --from-path=/import \
            --overwrite-destination \
            --verbose
        echo "✅ Database '$DB_NAME' loaded successfully."
    else
        echo "⚠️ No dump file found at $DUMP_FILE. Starting empty database."
    fi
fi

# Start Neo4j
echo "🚀 Starting Neo4j..."
exec /startup/docker-entrypoint.sh neo4j