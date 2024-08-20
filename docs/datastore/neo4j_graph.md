# Setup and configure Neo4j

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
    gcloud services enable aiplatform.googleapis.com
    ```

1. [Install python][install-python] and set up a python [virtual environment][venv].

[install-python]: https://cloud.google.com/python/docs/setup#installing_python
[venv]: https://cloud.google.com/python/docs/setup#installing_and_using_virtualenv

1. Make sure you have python version 3.11+ installed.

    ```bash
    python -V
    ```

1. Install required dependencies:
    ```bash
    cd retrieval_service
    pip install -r requirements.txt
    ```

### Create a Neo4j Database

### Neo4j AuraDB on GCP

1. ⚠️**Important**: Enabling [Neo4j Aura in Google Cloud Marketplace](https://pantheon.corp.google.com/marketplace/product/endpoints/prod.n4gcp.neo4j.io) does not permit the use of `Free-tier` instances. It will provision a `Professional-tier` instance, which incurs additional monthly costs. Learn more at [Neo4j AuraDB overview](https://neo4j.com/docs/aura/auradb/?utm_source=gcp).

2. Enable Neo4j Aura in the GCP Marketplace by visiting the [Google Cloud Marketplace](https://console.cloud.google.com/marketplace/product/endpoints/prod.n4gcp.neo4j.io?hl=es-419). After enabling it, a `Manage on Provider` button will appear. Click on it to proceed.

3. In the Neo4j console, click `New Instance`, then choose `Professional Tier`. 

4. Follow the on-screen instructions to complete the setup and download the credentials as a `.txt` file.

### Neo4j Aura (Free)

1. To set up a free-tier Neo4j database, go to the [Neo4j Console](https://console.neo4j.io/).

2. Sign in or create a new account.

3. Once logged in, click `New Instance`, then choose the `Aura Free` tier.

4. Follow the on-screen instructions to complete the setup and download the credentials as a `.txt` file.


## Update config

1. Make a copy of `example-config.yml` and name it `config.yml`.

    ```bash
    cp example-config.yml config.yml
    ```

1. Update `config.yml` with your database information.

```bash
host: 0.0.0.0
datastore:
  kind: "neo4j"
  uri: "neo4j_url"
  auth:
    username: "neo4j_user"
    password: "neo4j_password"
```


## Initialize data in Neo4j

1. Populate your Neo4j database with the command below. It will take several minutes to run:

    ```bash
    python run_database_init.py
    ```

## Developer information

This section is for developers that want to develop and run the app locally.

### Test Environment Variables

Set environment variables:

```bash
export DB_URI=""
export DB_USER=""
export DB_PASSWORD=""
```

Run retrieval service unit tests:

```bash
gcloud builds submit --config retrieval_service/neo4j_graph.test.cloudbuild.yaml \
    --substitutions _DATABASE_URI=$DB_URI
```

Where `$DB_URI`are environment variables with your database values.
