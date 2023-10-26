#!/bin/bash
# Script for Cloud Run Job to initialize AlloyDB data
export PGPASSWORD=$DB_PASS
export PGUSER=$DB_USER
echo "Connecting to $DB_HOST"

createdb -h $DB_HOST -p 5432 $DB_NAME

# List all database
psql -h $DB_HOST -l

echo "Enabling pgvector"
psql -h $DB_HOST -d $DB_NAME -c 'CREATE EXTENSION vector;'

# Change into extension service directory
cd extension_service
# Create a config for the extension service
cp example-config.yml config.yml

sed -i "s/DB_HOST/${DB_HOST}/g" config.yml
sed -i "s/DB_NAME/${DB_NAME}/g" config.yml
sed -i "s/DB_USER/${DB_USER}/g" config.yml
sed -i "s/PASSWORD/${DB_PASS}/g" config.yml

python run_database_init.py
