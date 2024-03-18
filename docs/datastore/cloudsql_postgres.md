# Setup and configure Cloud SQL for Postgres

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
    gcloud services enable sqladmin.googleapis.com \
                           aiplatform.googleapis.com
    ```

1. [Install python][install-python] and set up a python [virtual environment][venv].

1. Make sure you have python version 3.11+ installed.

    ```bash
    python -V
    ```

1. Download and install [postgres-client cli (`psql`)][install-psql].

1. Install the [Cloud SQL Auth Proxy client][install-cloudsql-proxy].

[install-python]: https://cloud.google.com/python/docs/setup#installing_python
[venv]: https://cloud.google.com/python/docs/setup#installing_and_using_virtualenv
[install-psql]: https://www.timescale.com/blog/how-to-install-psql-on-mac-ubuntu-debian-windows/
[install-cloudsql-proxy]: https://cloud.google.com/sql/docs/postgres/connect-instance-auth-proxy#install-proxy


## Create a Cloud SQL for PostgreSQL instance

1. Set environment variables. For security reasons, use a different password for
   `$DB_PASS` and note it for future use:

    ```bash
    export DB_PASS=my-cloudsql-pass
    export DB_USER=postgres
    export INSTANCE=my-cloudsql-instance
    export REGION=us-central1
    ```

1. Create a PostgreSQL instance:

    ```bash
    gcloud sql instances create $INSTANCE \
        --database-version=POSTGRES_14 \
        --cpu=4 \
        --memory=16GB \
        --region=$REGION
    ```

1. Set password for postgres user:

    ```bash
    gcloud sql users set-password $DB_USER \
        --instance=$INSTANCE \
        --password=$DB_PASS
    ```


## Connect to the Cloud SQL instance

1. Connect to instance using cloud sql proxy:

    ```bash
    ./cloud-sql-proxy $PROJECT_ID:$REGION:$INSTANCE
    ```

1. Verify you can connect to your instance with the `psql` tool. Enter
   password for Cloud SQL (`$DB_PASS` environment variable set above) when prompted:

    ```bash
    psql "host=127.0.0.1 port=5432 sslmode=disable user=$DB_USER"
    ```

## Initialize data

1. While connected using `psql`, create a database and switch to it:

    ```bash
    CREATE DATABASE assistantdemo;
    \c assistantdemo
    ```

1. Install [`pgvector`][pgvector] extension in the database:

    ```bash
    CREATE EXTENSION vector;
    ```

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
      # Example for cloudsql_postgres.py provider
      kind: "cloudsql-postgres"
      # Update this with your project ID
      project: <PROJECT_ID>
      region: us-central1
      instance: my-cloudsql-instance
      # Update this with the database name
      database: "assistantdemo"
      # Update with database user, the default is `postgres`
      user: "postgres"
      # Update with database user password
      password: "my-cloudsql-pass"
    ```

1. Populate data into database. Note: This may take up to 5 minutes.

    ```bash
    python run_database_init.py
    ```

[pgvector]: https://github.com/pgvector/pgvector

## Clean up resources

Clean up after completing the demo.

1. Delete the Cloud SQL instance:

    ```bash
    gcloud sql instances delete my-cloudsql-instance
    ```
