# Deploy the Extension Service to Cloud Run

## Before you begin

1. Make sure you've [setup and initialized your
   Database](../README.md#setting-up-your-database).

1. You must have the following APIs Enabled:

    ```bash
    gcloud services enable cloudrun.googleapis.com \
                           cloudbuild.googleapis.com \
                           artifactregistry.googleapis.com \
                           iam.googleapis.com
    ```

1. To create an IAM account, you must have the following IAM permissions (or
   roles):
    - Create Service Account role (roles/iam.serviceAccountCreator)

1. To deploy from source, you must have ONE of the following IAM permission:
    - Owner role
    - Editor role
    - The following set of roles:
        - Cloud Build Editor role (roles/cloudbuild.builds.editor)
        - Artifact Registry Admin role (roles/artifactregistry.admin)
        - Storage Admin role  (roles/storage.admin)
        - Cloud Run Admin role (roles/run.admin)
        - Service Account User role (roles/iam.serviceAccountUser)

Notes:
* If you are under a domain restriction organization policy
  [restricting](https://cloud.google.com/run/docs/authenticating/public#domain-restricted-sharing)
  unauthenticated invocations for your project, you will need to access your
  deployed service as described under [Testing private
  services](https://cloud.google.com/run/docs/triggering/https-request#testing-private).
* If you are using VPC based datastore, make sure your Cloud Run service and datastore are in the same VPC network. 

## Create a service account

1. Create a backend service account if you don't already have one:

    ```bash
    gcloud iam service-accounts create extension-identity
    ```

## Deploy to Cloud Run

1. From the root `database-query-extension` directory, deploy the extension
   service to Cloud Run using the following command:

    * For AlloyDB:

        ```bash
        gcloud run deploy extension-service \
            --source=./extension_service/\
            --no-allow-unauthenticated \
            --service-account extension-identity \
            --region us-central1 \
            # The follow flags are optional if you aren't using a VPC 
            --network=default \ 
            --subnet=default
        ```

## Connecting to Cloud Run

Next, we will use gcloud to authenticate requests to our Cloud Run instance:

1. Run the `run services proxy` to proxy connections to Cloud Run: 
    ```bash
        gcloud run services proxy my-service --port=8080
    ```

1. Finally, use `curl` to verify the endpoint works:
    
    ```bash
        curl http://127.0.0.1:8080
    ```