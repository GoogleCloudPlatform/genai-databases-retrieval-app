# Run the Demo Application

The demo application can be run [locally](#running-the-application-locally) or deployed to [Cloud Run](#deploying-the-application).

## Pre-reqs

1. [Setting up your Database](./datastore/alloydb.md)

1. [Deploying your Extension](./cloudrun_deployment.md)

1. Retrieve extension URL:

    ```bash
    export EXTENSION_URL=$(gcloud run services describe extension-service --format 'value(status.url)')
    ```

## Running the application locally

1. Set up [Application Default Credentials](https://cloud.google.com/docs/authentication/application-default-credentials#GAC):

    ```bash
    export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
    ```

1. Change into the demo directory:

    ```bash
    cd langchain_tools_demo
    ```

1. To run the app using uvicorn, execute the following:

    ```bash
    python main.py
    ```

    Note: for hot reloading of the app use: `uvicorn main:app --host 0.0.0.0 --reload`

1. View app at `http://localhost:8080/`

## Deploying the application

1. Create a frontend service account if you don't already have one:

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

1. Deploy to Cloud Run:

    ```bash
    gcloud run deploy demo-service \
        --source ./langchain_tools-demos/ \
        --allow-unauthenticated \
        --set-env-vars=BASE_URL=$EXTENSION_URL \
        --service-account demo-identity
    ```

    Note: Your organization may not allow unauthenticated requests. Deploy with `--no-allow-unauthenticated` and use the proxy to view the frontend: `gcloud run services proxy demo-service`.
