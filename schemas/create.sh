#!/bin/bash

if [ -z $PROJECT_ID ]; then
    echo "No project ID specified"
    exit
fi

if [ -z $DATASTORES ]; then
    DATASTORES="airports amenities flights policies tickets"
fi

for ds in $DATASTORES; do
    curl -X POST \
    -H "Authorization: Bearer $(gcloud auth print-access-token)" \
    -H "Content-Type: application/json" \
    -H "X-Goog-User-Project: $PROJECT_ID" \
    "https://discoveryengine.googleapis.com/v1/projects/$PROJECT_ID/locations/global/collections/default_collection/dataStores?dataStoreId=cymbal-air-$ds" \
    -d "{
        \"displayName\": \"Cymbal Air $ds\",
        \"industryVertical\": \"GENERIC\"
    }"

    curl -X PATCH \
    -H "Authorization: Bearer $(gcloud auth print-access-token)" \
    -H "Content-Type: application/json" \
    "https://discoveryengine.googleapis.com/v1beta/projects/$PROJECT_ID/locations/global/collections/default_collection/dataStores/cymbal-air-$ds/schemas/default_schema" \
    -d @$ds.json
done