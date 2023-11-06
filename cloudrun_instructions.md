# Deploy to Cloud Run

## Pre-reqs

* Google Cloud Project
* Enabled APIs:
    * Cloud Run
    * Vertex AI
    * Cloud SQL or AlloyDB
    * Compute
    * Cloud Build
    * Artifact Registry
    * Service Networking
* Cloud SQL PostgreSQL instance or AlloyDB cluster and primary instance

## Deployment

1. For easier deployment, set environment variables:

    ```bash
    export PROJECT_ID=<YOUR_PROJECT_ID>
    ```

1. Create a backend service account:

    ```bash
    gcloud iam service-accounts create extension-identity
    ```

1. Grant permissions to access Cloud SQL and/or AlloyDB:

    ```bash
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member serviceAccount:extension-identity@$PROJECT_ID.iam.gserviceaccount.com \
        --role roles/cloudsql.client
    ```

    ```bash
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member serviceAccount:extension-identity@$PROJECT_ID.iam.gserviceaccount.com \
        --role roles/alloydb.client
    ```

1. Change into the service directory:

    ```bash
    cd extension_service
    ```

1. Deploy backend service to Cloud Run:

    * For Cloud SQL:

        ```bash
        gcloud run deploy extension-service \
            --source . \
            --no-allow-unauthenticated \
            --service-account extension-identity \
            --region us-central1 \
            --add-cloudsql-instances <PROJECT_ID:REGION:CLOUD_SQL_INSTANCE_NAME>
        ```

    * For AlloyDB:

        ```bash
        gcloud alpha run deploy extension-service \
            --source . \
            --no-allow-unauthenticated \
            --service-account extension-identity \
            --region us-central1 \
            --network=default \
            --subnet=default
        ```

1. Retrieve extension URL:

    ```bash
    export EXTENSION_URL=$(gcloud run services describe extension-service --format 'value(status.url)')
    ```

1. Create a frontend service account:

    ```bash
    gcloud iam service-accounts create demo-identity
    ```

1. Grant the service account access to invoke the backend service and VertexAI API:

    ```bash
    gcloud run services add-iam-policy-binding extension-service \
        --member serviceAccount:demo-identity@$PROJECT_ID.iam.gserviceaccount.com \
        --role roles/run.invoker
    ```
    ```bash
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member serviceAccount:demo-identity@$PROJECT_ID.iam.gserviceaccount.com \
        --role roles/aiplatform.user
    ```

1. Change into the service directory:

    ```bash
    cd langchain_tools-demos
    ```

1. Deploy to Cloud Run:

    ```bash
    gcloud run deploy demo-service \
        --source . \
        --allow-unauthenticated \
        --set-env-vars=BASE_URL=$EXTENSION_URL \
        --service-account demo-identity
    ```

    Note: Your organization may not allow unauthenticated requests. Deploy with `--no-allow-unauthenticated` and use the proxy to view the frontend: `gcloud run services proxy demo-service`.
