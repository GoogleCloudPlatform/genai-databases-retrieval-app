# DEVELOPER.md

## Before you begin

1. Make sure you've [setup and initialized your
   Database](../README.md#setting-up-your-database).

1. Install Python 3.11+

1. Install dependencies. We recommend using a virtualenv:

    ```bash
    pip install -r retrieval_service/requirements.txt -r llm_demo/requirements.txt
    ```

1. Install test dependencies:

    ```bash
    pip install -r retrieval_service/requirements-test.txt -r llm_demo/requirements-test.txt
    ```

## Run the app locally

### Running the retrieval service

1. Change into the service directory:

    ```bash
    cd retrieval_service
    ```

1. Open a local connection to your database by starting the [AlloyDB Auth Proxy][alloydb-proxy] or [Cloud SQL Auth Proxy][cloudsql-proxy] or a [SSH tunnel][tunnel] to your AlloyDB instance (for non-cloud postgres such as AlloyDB Omni).

1. You should already have a [`config.yml` created with your database config][config]. Continue to use `host: 127.0.0.1` and `port: 5432`, unless you instruct the proxy to listen or the SSH tunnel to forward to a different address.


1. To run the app using uvicorn, execute the following:

    ```bash
    python run_app.py
    ```

### Running the frontend

1. Change into the demo directory:

    ```bash
    cd llm_demo
    ```

1. To use a live retrieval service on Cloud Run:

    1. Set Google user credentials:

        ```bash
        gcloud auth login
        ```

    1. Set `BASE_URL` environment variable:

        ```bash
        export BASE_URL=$(gcloud run services describe retrieval-service --format 'value(status.url)')
        ```

    1. Allow your account to invoke the Cloud Run service by granting the [role Cloud Run invoker][invoker]

1. [Optional] Turn on debugging by setting the `DEBUG` environment variable:

    ```bash
    export DEBUG=True
    ```

1. Set orchestration type environment variable:

    | orchestration-type            | Description                                 |
    |-------------------------------|---------------------------------------------|
    | langchain-tools               | LangChain tools orchestrator.               |
    | vertexai-function-calling     | VertexAI Function Calling orchestrator.     |

    ```bash
    export ORCHESTRATION_TYPE=<orchestration-type>
    ```

1. To run the app using uvicorn, execute the following:

    ```bash
    python run_app.py
    ```

    Note: for hot reloading of the app use: `python run_app.py --reload`

1. View app at `http://localhost:8081/`

## Testing

### Run tests locally

1. Change into the `retrieval_service` directory
1. Open a local connection to your database by starting the [AlloyDB Auth Proxy][alloydb-proxy] or [Cloud SQL Auth Proxy][cloudsql-proxy] or a [SSH tunnel][tunnel] to your AlloyDB instance (for non-cloud postgres such as AlloyDB Omni).
1. Set environment variables (different provider requires different environment variables):

    | Datastore                               |
    |----------------------------------------|
    | [AlloyDB](./docs/datastore/alloydb.md#test-environment-variables) |
    | [Cloud SQL for Postgres](./docs/datastore/cloudsql_postgres.md#test-environment-variables) |
    | [Cloud SQL for MySQL](./docs/datastore/cloudsql_mysql.md#test-environment-variables) |
    | [Non-cloud Postgres (e.g. AlloyDB Omni)](./docs/datastore/postgres.md#test-environment-variables) |

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
  * Repo: GoogleCloudPlatform/genai-databases-retrieval-app (GitHub App)
  * Base branch: `^main$`
* Comment control: Required except for owners and collaborators
* Filters: add directory filter
* Config: Cloud Build configuration file
  * Location: Repository (add path to file)
* Substitution variables:
  * Add `_DATABASE_HOST` for non-cloud postgres
* Service account: set for demo service to enable ID token creation to use to authenticated services

#### Project Setup

1. Follow instructions to setup the test project:
    * [Set up and configure database](./README.md#setting-up-your-database)
    * [Instructions for deploying the retrieval service](./docs/deploy_retrieval_service.md)
1. Setup Cloud Build triggers (above)

##### Setup for retrieval service

1. Create a Cloud Build private pool
1. Enable Secret Manager API
1. Create secret, `db_user` and `db_pass`, with your database user and database password defined here:

    | provider                               |
    |----------------------------------------|
    | [AlloyDB](./docs/datastore/alloydb.md#create-a-alloydb-cluster) |
    | [Cloud SQL for Postgres](./docs/datastore/cloudsql_postgres.md#create-a-cloud-sql-for-postgresql-instance) |
    | [Cloud SQL for MySQL](./docs/datastore/cloudsql_mysql.md#create-a-cloud-sql-for-mysql-instance) |
    | [Non-cloud Postgres (e.g. AlloyDB Omni)](./docs/datastore/postgres.md#create-a-alloydb-cluster) |

1. Allow Cloud Build to access secret
1. Add role Vertex AI User (roles/aiplatform.user) to Cloud Build Service account. Needed to run database init script.

##### Setup for demo service tests

1. Add roles Cloud Run Admin, Service Account User, Log Writer, and Artifact Registry Admin to the demo service's Cloud Build trigger service account.

#### Run tests with Cloud Build

* Run Demo Service integration test:

    ```bash
    gcloud builds submit --config llm_demo/int.tests.cloudbuild.yaml
    ```

* Run retrieval service unit tests:

    | provider                               |
    |----------------------------------------|
    | [AlloyDB](./docs/datastore/alloydb.md#run-tests) |
    | [Cloud SQL for Postgres](./docs/datastore/cloudsql_postgres.md#run-tests) |
    | [Cloud SQL for MySQL](./docs/datastore/cloudsql_mysql.md#run-tests) |
    | [Non-cloud Postgres (e.g. AlloyDB Omni)](./docs/datastore/postgres.md#run-tests) |

    Note: Make sure to setup secrets describe in [Setup for retrieval service](#setup-for-retrieval-service)

#### Trigger

To run Cloud Build tests on GitHub from external contributors, ie RenovateBot, comment: `/gcbrun`.

#### Code Coverage
Please make sure your code is fully tested. The Cloud Build integration tests are run with the `pytest-cov` code coverage plugin. They fail for PRs with a code coverage less than the threshold specified in `retrieval_service/coverage/.<test>-coveragerc`.  If your file is inside the main module and should be ignored by code coverage check, add it to the `omit` section of `retrieval_service/coverage/.<test>-coveragerc`.

Check for code coverage report any Cloud Build integration test log.
Here is a breakdown of the report:
- `Stmts`:  lines of executable code (statements).
- `Miss`: number of lines not covered by tests.
- `Branch`: branches of executable code (e.g an if-else clause may count as 1 statement but 2 branches; test for both conditions to have both branches covered).
- `BrPart`: number of branches not covered by tests.
- `Cover`: average coverage of files.
- `Missing`: lines that are not covered by tests.

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
python llm_demo/run_evaluation.py
```

To view metrics, visit [GCP dashboard][vertex-ai-experiments].

## Versioning

This app will be released based on version number MAJOR.MINOR.PATCH:

- MAJOR: Breaking change is made, requiring user to redeploy all or some of the app.
- MINOR: Backward compatible feature change or addition that doesn't require redeploying.
- PATCH: Backward compatible bug fixes and minor updates

[alloydb-proxy]: https://cloud.google.com/alloydb/docs/auth-proxy/connect
[cloudsql-proxy]: https://cloud.google.com/sql/docs/mysql/sql-proxy
[tunnel]: https://github.com/GoogleCloudPlatform/genai-databases-retrieval-app/blob/main/docs/datastore/alloydb.md#set-up-connection-to-alloydb
[config]: https://github.com/GoogleCloudPlatform/genai-databases-retrieval-app/blob/main/docs/datastore/alloydb.md#initialize-data-in-alloydb
[triggers]: https://console.cloud.google.com/cloud-build/triggers?e=13802955&project=extension-demo-testing
[invoker]: https://cloud.google.com/run/docs/securing/managing-access#add-principals
[vertex-ai-experiments]: https://pantheon.corp.google.com/vertex-ai/experiments/experiments
