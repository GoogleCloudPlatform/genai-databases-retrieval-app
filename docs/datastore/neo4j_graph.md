# Setup and configure Neo4j

## Before you begin

1. Make sure you have a GoogleCloud project and billing is enabled.

1. Set your `PROJECT_ID` environment variable:

    ```bash
    export PROJECT_ID=<YOUR_PROJECT_ID>
    ```

1. [Install](https://cloud.google.com/sdk/docs/install) the gcloud CLI.

1. Set gcloud project:

    ```bash
    gcloud config set project $PROJECT_ID
    ```

1. Make sure you have python version 3.11+ installed.

    ```bash
    python -V
    ```

1. [Install python][install-python] and set up a python [virtual environment][venv].

1. Install required dependencies:
    ```bash
    cd retrieval_service
    pip install -r requirements.txt
    ```

## Create a Neo4j database

1. Important: Enabling Neo4j Aura in Google Cloud Marketplace does not permit the use of `Free-tier` instances. It will provision a `Professional-tier` instance, which incurs additional monthly costs.

1. Enable Neo4j AuraDB in GCP Marketplace [Neo4j console](https://console.cloud.google.com/marketplace/product/endpoints/prod.n4gcp.neo4j.io?authuser=2). After enabling it, a `Manage on Provider` button will appear. Click on it to proceed.


1. In the [Neo4j console](https://console.neo4j.io/?ref=aura-lp&mpp=4bfb2414ab973c741b6f067bf06d5575&mpid=%24device%3A19050fa4558249-004c1750b934b6-6a3f4f73-18f258-19050fa4558249&_gl=1*9tzqtf*_ga*NzM2MTEwNTQ4LjE3MTk1MDkyNTA.*_ga_DZP8Z65KK4*MTcyNDA5OTc0OS44NC4xLjE3MjQxMDMwMTkuMC4wLjA.*_gcl_aw*R0NMLjE3MjQxMDMwMTkuQ2owS0NRancyb3UyQmhDQ0FSSXNBTkF3TTJIWGhNang4U3l3VEJDYVh6NWZHSWd6Y2VmTHN0dTJoTjJnTXpKd2ZEN1B1U2J1RDdLNFA0OGFBbVRjRUFMd193Y0I.*_gcl_au*MTY0NDkyNTM4OS4xNzE5NTA5MjUwLjE4NjQyNTUxNDguMTcyMTM3NDE3NS4xNzIxMzc0MTc0*_ga_DL38Q8KGQC*MTcyNDA5OTc0OS43OC4xLjE3MjQxMDMwMjAuMC4wLjA.), click `New Instance`, then choose `Professional Tier`. Finally follow the on-screen instructions to download the credentials as a .txt file

## Update config

Update `config.yml` with your database information.

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

1. Change to the `retrieval_service` directory:

    ```bash
    cd retrieval_service
    ```

2. Populate your Neo4j database with the command below. It will take several minutes to run:

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
