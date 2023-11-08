# DEVELOPER.md

## Before you begin

1. Make sure you've [setup and initialized your
   Database](../README.md#setting-up-your-database).

1. Install Python 3.11+

1. Install dependencies. We recommend using a virtualenv:

    ```bash
    pip install -r extension_service/requirements.txt -r langchain_tools_demo/requirements.txt
    ```

1. Install test dependencies:

    ```bash
    pip install -r extension_service/requirements-test.txt -r langchain_tools_demo/requirements-test.txt
    ```

## Run the app locally

### Running the extension service

1. Change into the service directory:

    ```bash
    cd extension_service
    ```

1. Open a local connection to your database by starting the [Cloud SQL Auth Proxy][proxy] or a [SSH tunnel][tunnel] to your AlloyDB instance.

1. You should already have a [`config.yml` created with your database config][config]. Continue to use `host: 127.0.0.1` and `port: 5432`, unless you instruct the proxy to listen or the SSH tunnel to forward to a different address.


1. To run the app using uvicorn, execute the following:

    ```bash
    python run_app.py
    ```

### Running the frontend

1. Change into the demo directory:

    ```bash
    cd langchain_tools_demo
    ```

1. To use a live extension service on Cloud Run:

    1. Set up [Application Default Credentials][ADC]:

        ```bash
        export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
        ```

    1. Set `BASE_URL` environment variable:

        ```bash
        export BASE_URL=$(gcloud run services describe extension-service --format 'value(status.url)')
        ```

1. [Optional] Turn off debugging by setting the `DEBUG` environment variable:

    ```bash
    export DEBUG=False
    ```

1. To run the app using uvicorn, execute the following:

    ```bash
    python main.py
    ```

    Note: for hot reloading of the app use: `uvicorn main:app --host 0.0.0.0 --reload`

1. View app at `http://localhost:8081/`

## Testing

### Run tests locally

1. Change into the `extension_service` directory
1. Open a local connection to your database by starting the [Cloud SQL Auth Proxy][proxy] or a [SSH tunnel][tunnel] to your AlloyDB instance.
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

### CI Platform Setup

Cloud Build is used to run tests against Google Cloud resources in test project: extension-demo-testing.
Each test has a corresponding Cloud Build trigger, see [all triggers][triggers].

#### Trigger Setup
Create a Cloud Build trigger via the UI or `gcloud` with the following specs:

* Event: Pull request
* Region:
    * us-central1 - for AlloyDB to connect to private pool in VPC
    * global - for default worker pools
* Source:
  * Generation: 1st gen
  * Repo: GoogleCloudPlatform/database-query-extension (GitHub App)
  * Base branch: `^main$`
* Comment control: Required except for owners and collaborators
* Filters: add directory filter
* Config: Cloud Build configuration file
  * Location: Repository (add path to file)
* Substitution variables:
  * Add `_DATABASE_HOST` for AlloyDB IP address
* Service account: set for demo service to enable ID token creation to use to authenticated services

#### Project Setup

1. Follow instructions to setup the test project:
    * [Set up and configure AlloyDB](./docs/datastore/alloydb.md)
    * [Instructions for deploying the extension service](./docs/deploy_extension_service.md)
1. Setup Cloud Build triggers (above)

##### Setup for extension service - Alloy DB tests

1. Create a Cloud Build private pool
1. Enable Secret Manager API
1. Create secret, `alloy_db_pass`, with your AlloyDB password
1. Allow Cloud Build to access secret
1. Add role Vertex AI User (roles/aiplatform.user) to Cloud Build Service account. Needed to run database init script.

##### Setup for demo service tests

1. Add roles Cloud Run Admin, Service Account User, Log Writer, and Artifact Registry Admin to the demo service's Cloud Build trigger service account.

[proxy]: https://cloud.google.com/sql/docs/mysql/sql-proxy
[tunnel]: https://github.com/GoogleCloudPlatform/database-query-extension/blob/main/docs/datastore/alloydb.md#set-up-connection-to-alloydb
[config]: https://github.com/GoogleCloudPlatform/database-query-extension/blob/main/docs/datastore/alloydb.md#initialize-data-in-alloydb
[ADC]: https://cloud.google.com/docs/authentication/application-default-credentials#GAC
[triggers]: https://console.cloud.google.com/cloud-build/triggers?e=13802955&project=extension-demo-testing