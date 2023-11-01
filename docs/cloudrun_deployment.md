# Deploy the Extension Service to Cloud Run #

## Before you begin: ##

1. In the Google Cloud console, on the project selector page, select or [create a Google Cloud project](https://cloud.google.com/resource-manager/docs/creating-managing-projects).\
2. [Make sure that billing is enabled for your Google Cloud project](https://cloud.google.com/billing/docs/how-to/verify-billing-enabled#console).
3. [Install](https://cloud.google.com/sdk/docs/install) the Google Cloud CLI.
4. To [initialize](https://cloud.google.com/sdk/docs/initializing) the gcloud CLI, run the following command:
```
gcloud init
```
5. To set the default project for your Cloud Run service:

```
gcloud config set project
```
6. If you are under a domain restriction organization policy [restricting](https://cloud.google.com/run/docs/authenticating/public#domain-restricted-sharing) unauthenticated invocations for your project, you will need to access your deployed service as described under [Testing private services](https://cloud.google.com/run/docs/triggering/https-request#testing-private).
7. If you are using VPC based datastore, make sure your Cloud Run service and datastore are in the same VPC network.

&nbsp;
&nbsp;

## Permissions required to deploy: ##

To create a service account, you must have the following IAM permission:
- Create Service Account role (roles/iam.serviceAccountCreator)


To deploy from source, you must have ONE of the following IAM permission:
- Owner role
- Editor role
- The following set of roles:
  - Cloud Build Editor role (roles/cloudbuild.builds.editor)
  - Artifact Registry Admin role (roles/artifactregistry.admin)
  - Storage Admin role  (roles/storage.admin)
  - Cloud Run Admin role (roles/run.admin)
  - Service Account User role (roles/iam.serviceAccountUser)

You must have the following APIs Enabled:
- Enabled APIs:
  - Cloud Run
  - Vertex AI
  - Compute
  - Cloud Build
  - Artifact Registry
  - Service Networking

```bash
    # Command to enable APIs
    gcloud services enable cloudrun.googleapis.com \
                           vertexai.googleapis.com \
                           compute.googleapis.com \
                           cloudbuild.googleapis.com \
                           artifactregistry.googleapis.com \
                           servicenetworking.googleapis.com
```
You must have a Cloud SQL PostgreSQL instance or [AlloyDB cluster and primary instance](datastore/alloydb.md); have your config.yaml set up to connect to your database accordingly.


## Deployment: ##

1. Create a backend service account if you don't already have one:

    ```bash
    gcloud iam service-accounts create extension-identity
    ```


1. In the database-query-extension directory, deploy the extension service to Cloud Run using the following command:

    * For Cloud SQL:

        ```bash
        gcloud run deploy extension-service \
            --source=./extension_service/ \
            --no-allow-unauthenticated \
            --service-account extension-identity \
            --region us-central1 \
            --add-cloudsql-instances <PROJECT_ID:REGION:CLOUD_SQL_INSTANCE_NAME>
        ```

    * For AlloyDB:

        ```bash
        gcloud alpha run deploy extension-service \
            --source=./extension_service/\
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