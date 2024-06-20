# Setup and configure Cloud SQL for MySQL

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

1. Download and install [mysql-client cli (`mysql`)][install-mysql].

1. Install the [Cloud SQL Auth Proxy client][install-cloudsql-proxy].

[install-python]: https://cloud.google.com/python/docs/setup#installing_python
[venv]: https://cloud.google.com/python/docs/setup#installing_and_using_virtualenv
[install-mysql]: https://dev.mysql.com/doc/mysql-installation-excerpt/8.0/en/
[install-cloudsql-proxy]: https://cloud.google.com/sql/docs/mysql/connect-auth-proxy


## Create a Cloud SQL for MySQL instance

1. Set environment variables. For security reasons, use a different password for
   `$DB_PASS` and note it for future use:

    ```bash
    export DB_PASS=my-cloudsql-pass
    export DB_USER=root
    export INSTANCE=my-cloudsql-instance
    export REGION=us-central1
    ```

1. Create a MySQL instance with vector enabled:

    ```bash
    gcloud sql instances create $INSTANCE \
        --database-version=MYSQL_8_0_36 \
        --cpu=4 \
        --memory=16GB \
        --region=$REGION \
        --database-flags=cloudsql_vector=ON
    ```

1. Set password for mysql user:

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

1. Verify you can connect to your instance with the `mysql` tool. Enter
   password for Cloud SQL (`$DB_PASS` environment variable set above) when prompted:

    ```bash
    mysql "host=127.0.0.1 port=3306 sslmode=disable user=$DB_USER"
    ```

## Update config

Update `config.yml` with your database information.

```bash
host: 0.0.0.0
datastore:
    # Example for cloudsql_mysql.py provider
    kind: "cloudsql-mysql"
    # Update this with your project ID
    project: <PROJECT_ID>
    region: us-central1
    instance: my-cloudsql-instance
    # Update this with the database name
    database: "assistantdemo"
    # Update with database user, the default is `mysql`
    user: "root"
    # Update with database user password
    password: "my-cloudsql-pass"
```

## Initialize data

1. While connected using `mysql`, create a database and switch to it:

    ```bash
    CREATE DATABASE assistantdemo;
    \c assistantdemo
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

1. Populate data into database:

    ```bash
    python run_database_init.py
    ```

## Clean up resources

Clean up after completing the demo.

1. Delete the Cloud SQL instance:

    ```bash
    gcloud sql instances delete my-cloudsql-instance
    ```

## Developer information

This section is for developers that want to develop and run the app locally.

### Test Environment Variables

Set environment variables:

```bash
export DB_USER=""
export DB_PASS=""
export DB_PROJECT=""
export DB_REGION=""
export DB_INSTANCE=""
```

### Run tests

Run retrieval service unit tests:

```bash
gcloud builds submit --config retrieval_service/cloudsql-mysql.tests.cloudbuild.yaml \
    --substitutions _DATABASE_NAME=$DB_NAME,_DATABASE_USER=$DB_USER,_CLOUDSQL_REGION=$DB_REGION,_CLOUDSQL_INSTANCE=$DB_INSTANCE
```

Where `$DB_NAME`,`$DB_USER`,`$DB_REGION`,`$DB_CLUSTER`,`$DB_INSTANCE` are environment variables with your database values.