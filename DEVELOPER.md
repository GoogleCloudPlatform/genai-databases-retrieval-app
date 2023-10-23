# DEVELOPER.md

## Pre-reqs

* Google Cloud Project
* Enabled APIs:
    * Cloud Run
    * Vertex AI
    * Cloud SQL
* Cloud SQL PostgreSQL instance or AlloyDB cluster

## Local Development
### Setup

We recommend using Python 3.11+ and installing the requirements into a virtualenv:
```bash
pip install -r extension_service/requirements.txt -r langchain_tools_demo/requirements.txt
```

If you are developing or otherwise running tests, install the test requirements as well:
```bash
pip install -r extension_service/requirements-test.txt -r langchain_tools_demo/requirements-test.txt
```

 <!-- TODO: Add database setup -->

### Running the server

1. Change into the service directory:

    ```bash
    cd extension_service
    ```

1. Create your database config:

    ```bash
    cp example-config.yml config.yml
    ```

1. Add your values to `config.yml`

1. Start the Cloud SQL Proxy

1. To run the app using uvicorn, execute the following:

    ```bash
    python run_app.py
    ```

## Running the frontend

1. Set up Application Default Credentials

1. Change into the demo directory:

    ```bash
    cd langchain_tools_demo
    ```

1. Set the server port:

    ```bash
    export PORT=9090
    ```

1. [Optional] Set `BASE_URL` environment variable:

    ```bash
    export BASE_URL=<EXTENSION_SERVICE_URL>
    ```

1. [Optional] Set `DEBUG` environment variable:

    ```bash
    export DEBUG=True
    ```

1. To run the app using uvicorn, execute the following:

    ```bash
    python main.py
    ```

    Note: for hot reloading of the app use: `uvicorn main:app --host 0.0.0.0 --port 9090 --reload`

1. View app at `http://localhost:9090/`

# Testing

1. Set environment variables:

    ```bash
    export DB_USER=""
    export DB_PASS=""
    export DB_NAME=""
    ```

1. Run pytest to automatically run all tests:

    ```bash
    pytest
    ```

# Deployment

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

    ```bash
    gcloud run deploy extension-service \
        --source . \
        --no-allow-unauthenticated \
        --service-account extension-identity \
        --add-cloudsql-instances <PROJECT_ID:REGION:CLOUD_SQL_INSTANCE_NAME> \
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