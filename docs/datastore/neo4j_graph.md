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

1. In the [Neo4j console](https://console.neo4j.io/?product=aura-db&_gl=1*mpkyd1*_ga*NzM2MTEwNTQ4LjE3MTk1MDkyNTA.*_ga_DZP8Z65KK4*MTcyMjYyNzYyOC41OC4xLjE3MjI2MzQyODMuMC4wLjA.*_gcl_aw*R0NMLjE3MjI1NTA5NTcuQ2p3S0NBanc1S3kxQmhBZ0Vpd0E1akd1anR2c0FLbVdqVXB3SXNHTE5VQkEzcjh4Zm9WSjk5ZkdXdnl1UEM4bHI4YmZGSUVmMkM4NTF4b0NVOHNRQXZEX0J3RQ..*_gcl_au*MTY0NDkyNTM4OS4xNzE5NTA5MjUwLjE4NjQyNTUxNDguMTcyMTM3NDE3NS4xNzIxMzc0MTc0*_ga_DL38Q8KGQC*MTcyMjYyNzYyOC41Mi4xLjE3MjI2MzQyODMuMC4wLjA.), click `New Instance`, then follow the on-screen instructions to download the credentials as a .txt file

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
