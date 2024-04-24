# Setup and configure Spanner

## Before you begin

1. Make sure you have a Google Cloud project and billing is enabled.

1. Set your `PROJECT_ID` environment variable:

    ```bash
    export PROJECT_ID=<YOUR_PROJECT_ID>
    ```

1. [Install](https://cloud.google.com/sdk/docs/install) the gcloud CLI.

1. Set gcloud project:

    ```bash
    gcloud config set project $PROJECT_ID
    ```

1. Enable APIs:

    ```bash
    gcloud services enable spanner.googleapis.com
    ```

1. [Install python][install-python] and set up a python [virtual environment][venv].

1. Make sure you have python version 3.11+ installed.

    ```bash
    python -V
    ```
[install-python]: https://cloud.google.com/python/docs/setup#installing_python
[venv]: https://cloud.google.com/python/docs/setup#installing_and_using_virtualenv

## Create a Cloud Spanner instance

1. Set environment variables.

    ```bash
    export INSTANCE=my-spanner-instance
    export DATABASE=my-spanner-database
    export REGION=regional-us-central1
    ```

1. Create a Cloud Spanner instance:

    ```bash
    gcloud spanner instances create $INSTANCE \
        --config=$REGION \
        --nodes=1 \
        --description="My Spanner Instance"
    ```
1. Create a database within the Cloud Spanner instance:

    ```bash
    gcloud spanner databases create $DATABASE --instance=$INSTANCE
    ```
1. Verify the database created with the `gcloud` tool:

    ```bash
    gcloud spanner databases execute-sql $DATABASE \
        --instance=$INSTANCE \
        --sql="SELECT 1"
    ```
## Initialize data

1. Change into the retrieval service directory:

    ```bash
    cd genai-databases-retrieval-app/retrieval_service
    ```

1. Install requirements:

    ```bash
    pip install -r requirements.txt
    ```

1. Make a copy of `example-config.yml` and name it `config.yml`.

    ```bash
    cp example-config.yml config.yml
    ```

1. Update `config.yml` with your database information.

    ```bash
      host: 0.0.0.0
      datastore:
        # Example for Spanner
        kind: "spanner-gsql"
        project: <YOUR_PROJECT_ID>
        instance: <YOUR_INSTANCE>
        database: <YOUR_DATABASE>
        service_account_key_file: <PATH_TO_SERVICE_ACCOUNTS_CREDENTIALS>
    ```

1. Populate data into database:

    ```bash
    python run_database_init.py
    ```

## Clean up resources

Clean up after completing the demo.

1. Delete the Cloud Spanner instance:

    ```bash
    gcloud spanner instances delete $INSTANCE
    ```