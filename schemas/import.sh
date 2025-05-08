#!/bin/bash

TEST="abc def"

for i in $TEST; do
    echo $i
done

exit

if [ -z $PROJECT_ID ]; then
    echo "No project ID specified"
    exit
fi

if [ -z $ALLOYDB_PROJECT_ID ]; then
    ALLOYDB_PROJECT_ID=$PROJECT_ID
fi

if [ -z $LOCATION_ID ]; then
    echo "No location ID specified"
    exit
fi

if [ -z $CLUSTER_ID ]; then
    echo "No cluster ID specified"
    exit
fi

if [ -z $DATABASE_ID ]; then
    echo "No database ID specified"
    exit
fi

if [ -z $DATASTORES ]; then
    DATASTORES="airports amenities flights policies tickets"
fi

for ds in $DATASTORES; do
    curl -X POST \
    -H "Authorization: Bearer $(gcloud auth print-access-token)" \
    -H "Content-Type: application/json" \
    "https://discoveryengine.googleapis.com/v1/projects/$PROJECT_ID/locations/global/collections/default_collection/dataStores/cymbal-air-$ds/branches/0/documents:import" \
    -d "{
    \"alloyDbSource\": {
        \"projectId\": \"$ALLOYDB_PROJECT_ID\",
        \"locationId\": \"$LOCATION_ID\",
        \"clusterId\": \"$CLUSTER_ID\",
        \"databaseId\": \"$DATABASE_ID\",
        \"tableId\": \"$ds\",
    },
    \"reconciliationMode\": \"FULL\",
    \"autoGenerateIds\": true
    }"
done