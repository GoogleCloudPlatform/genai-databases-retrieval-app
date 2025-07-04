# DEVELOPER.md

## Before you begin

1. Make sure you've [setup Toolbox](./README.md#toolbox-setup).

1. Install Python 3.11+

1. Install dependencies. We recommend using a virtualenv:

    ```bash
    pip install -r requirements.txt
    ```

1. Install test dependencies:

    ```bash
    pip install -r requirements-test.txt
    ```

## Run the App Locally

### Setup Database

To setup the datasource to run with Toolbox locally, follow [these
steps](./README.md#database-setup).

### Run Agent App

1. Set the `TOOLBOX_URL` environment variable to point to your running MCP
   Toolbox server:
    ```bash
    export TOOLBOX_URL="http://localhost:8080"
    ```

1. To use a live retrieval service on Cloud Run:

    1. Set Google user credentials:

        ```bash
        gcloud auth login
        ```

    1. Set `TOOLBOX_URL` environment variable:

        ```bash
        export TOOLBOX_URL=$(gcloud run services describe toolbox-service --format 'value(status.url)')
        ```

    1. Allow your account to invoke the Cloud Run service by granting the [role Cloud Run invoker][invoker]

1. [Optional] Turn on debugging by setting the `DEBUG` environment variable:

    ```bash
    export DEBUG=True
    ```

1. To run the app using uvicorn, execute the following:

    ```bash
    python run_app.py
    ```

    > [!TIP]
    > For hot-reloading during development, use the `--reload` flag:
    > ```bash
    > `python run_app.py --reload`
    > ```

1. View the app in your browser at http://localhost:8081.

## Testing

### Run tests locally

1. The unit tests for this application mock the API calls to the MCP Toolbox, so
   you do not need a live database or a running Toolbox instance to run them.
    ```bash
    pytest
    ```

### CI Platform Setup

Cloud Build is used to run tests against Google Cloud resources in test project:
`extension-demo-testing`.

Each test has a corresponding Cloud Build trigger, see [all triggers][triggers].

#### Trigger Setup
Create a Cloud Build trigger via the UI or `gcloud` with the following specs:

* Event: Pull request
* Region:
    * `us-central1` - for AlloyDB to connect to private pool in VPC
    * `global` - for default worker pools
* Source:
  * Generation: 1st gen
  * Repo: GoogleCloudPlatform/genai-databases-retrieval-app (GitHub App)
  * Base branch: `^main$`
* Comment control: Required except for owners and collaborators
* Filters: add directory filter
* Config: Cloud Build configuration file
  * Location: Repository (add path to file)
* Substitution variables:
  * Add `_DATABASE_HOST` for non-cloud postgres
* Service account: set for demo service to enable ID token creation to use to
  authenticated services

#### Project Setup

1. Follow instructions to setup the test project:
    * [Set up and configure database](./README.md#database-setup)
    * [Instructions for Toolbox setup](./README.md#toolbox-setup)
1. Setup Cloud Build triggers ([above](#trigger-setup))

##### Setup for Toolbox

1. Create a Cloud Build private pool
1. Enable Secret Manager API
1. Create secret, `db_user` and `db_pass`, with your database user and database password defined [here](https://googleapis.github.io/genai-toolbox/resources/sources/).

1. Allow Cloud Build to access secret
1. Add role Vertex AI User (`roles/aiplatform.user`) to Cloud Build Service
   account. Needed to run database init script.

##### Setup for Agent App

1. Add roles `Cloud Run Admin`, `Service Account User`, `Log Writer`, and
   `Artifact Registry Admin` to the demo service's Cloud Build trigger service
   account.

#### Run tests with Cloud Build

* Run integration test:

    ```bash
    gcloud builds submit --config integration.cloudbuild.yaml
    ```

    > [!NOTE]
    > Make sure to setup secrets describe in [Setup for
    > Toolbox](#setup-for-toolbox)

#### Trigger

To run Cloud Build tests on GitHub from external contributors, ie RenovateBot,
comment: `/gcbrun`.

#### Code Coverage
Please make sure your code is fully tested.

## LLM Evaluation

[Optional] Export detailed metric table with row-specific scores by setting the `EXPORT_CSV` envrionment variable:

```bash
export EXPORT_CSV=True
```

Set `CLIENT_ID` to run evaluation that require authentication:

```bash
export CLIENT_ID=<retrieve CLIENT_ID from GCP credentials>
```

To run LLM system evaluation, execute the following:

```bash
python run_evaluation.py
```

To view metrics, visit [GCP dashboard][vertex-ai-experiments].

## Versioning

This app will be released based on version number `MAJOR.MINOR.PATCH`:

- `MAJOR`: Breaking change is made, requiring user to redeploy all or some of the app.
- `MINOR`: Backward compatible feature change or addition that doesn't require redeploying.
- `PATCH`: Backward compatible bug fixes and minor updates

[alloydb-proxy]: https://cloud.google.com/alloydb/docs/auth-proxy/connect
[cloudsql-proxy]: https://cloud.google.com/sql/docs/mysql/sql-proxy
[tunnel]: https://github.com/GoogleCloudPlatform/genai-databases-retrieval-app/blob/main/docs/datastore/alloydb.md#set-up-connection-to-alloydb
[config]: https://github.com/GoogleCloudPlatform/genai-databases-retrieval-app/blob/main/docs/datastore/alloydb.md#initialize-data-in-alloydb
[triggers]: https://console.cloud.google.com/cloud-build/triggers?e=13802955&project=extension-demo-testing
[invoker]: https://cloud.google.com/run/docs/securing/managing-access#add-principals
[vertex-ai-experiments]: https://pantheon.corp.google.com/vertex-ai/experiments/experiments
