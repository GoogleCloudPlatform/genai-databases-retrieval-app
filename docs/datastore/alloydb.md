# Setup and configure AlloyDB

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
    gcloud services enable alloydb.googleapis.com \
                           compute.googleapis.com \
                           cloudresourcemanager.googleapis.com \
                           servicenetworking.googleapis.com \
                           vpcaccess.googleapis.com \
                           aiplatform.googleapis.com
    ```

1. [Install python][install-python] and set up a python [virtual environment][venv].

1. Make sure you have python version 3.11+ installed.

    ```bash
    python -V
    ```

1. Download and install [postgres-client cli (`psql`)][install-psql].

[install-python]: https://cloud.google.com/python/docs/setup#installing_python
[venv]: https://cloud.google.com/python/docs/setup#installing_and_using_virtualenv
[install-psql]: https://www.timescale.com/blog/how-to-install-psql-on-mac-ubuntu-debian-windows/


## Enable private services access

In this step, we will enable Private Services Access so that AlloyDB is able to
connect to your VPC. You should only need to do this once per VPC (per project).

1. Set environment variables:

    ```bash
    export RANGE_NAME=my-allocated-range-default
    export DESCRIPTION="peering range for alloydb-service"
    ```

1. Create an allocated IP address range:

    ```bash
    gcloud compute addresses create $RANGE_NAME \
        --global \
        --purpose=VPC_PEERING \
        --prefix-length=16 \
        --description="$DESCRIPTION" \
        --network=default
    ```

1. Create a private connection:

    ```bash
    gcloud services vpc-peerings connect \
        --service=servicenetworking.googleapis.com \
        --ranges="$RANGE_NAME" \
        --network=default
    ```


## Create a AlloyDB cluster

1. Set environment variables. For security reasons, use a different password for
   `$DB_PASS` and note it for future use:

    ```bash
    export CLUSTER=my-alloydb-cluster
    export DB_PASS=my-alloydb-pass
    export INSTANCE=my-alloydb-instance
    export REGION=us-central1
    ```

1. Create an AlloyDB cluster:

    ```bash
    gcloud alloydb clusters create $CLUSTER \
        --password=$DB_PASS\
        --network=default \
        --region=$REGION \
        --project=$PROJECT_ID
    ```

1. Create a primary instance:

    ```bash
    gcloud alloydb instances create $INSTANCE \
        --instance-type=PRIMARY \
        --cpu-count=8 \
        --region=$REGION \
        --cluster=$CLUSTER \
        --project=$PROJECT_ID \
        --ssl-mode=ALLOW_UNENCRYPTED_AND_ENCRYPTED
    ```

1. Get AlloyDB IP address:

    ```bash
    export ALLOYDB_IP=$(gcloud alloydb instances describe $INSTANCE \
        --cluster=$CLUSTER \
        --region=$REGION \
        --format 'value(ipAddress)')
    ```

1. Note the AlloyDB IP address for later use:

    ```bash
    echo $ALLOYDB_IP
    ```

## Set up connection to AlloyDB

AlloyDB supports network connectivity through private, internal IP addresses
only. For this section, we will create a Google Cloud Engine VM in the same VPC as the
AlloyDB cluster. We can use this VM to connect to our AlloyDB cluster using
Private IP.

1. Set environment variables:

    ```bash
    export ZONE=us-central1-a
    export PROJECT_NUM=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
    export VM_INSTANCE=alloydb-proxy-vm
    ```

1. Create a Compute Engine VM:

    ```bash
    gcloud compute instances create $VM_INSTANCE \
        --project=$PROJECT_ID \
        --zone=$ZONE \
        --machine-type=e2-medium \
        --network-interface=network-tier=PREMIUM,stack-type=IPV4_ONLY,subnet=default \
        --maintenance-policy=MIGRATE \
        --provisioning-model=STANDARD \
        --service-account=$PROJECT_NUM-compute@developer.gserviceaccount.com \
        --scopes=https://www.googleapis.com/auth/cloud-platform \
        --create-disk=auto-delete=yes,boot=yes,device-name=$VM_INSTANCE,image-family=ubuntu-2004-lts,image-project=ubuntu-os-cloud,mode=rw,size=10,type=projects/$PROJECT_ID/zones/$ZONE/diskTypes/pd-balanced \
        --no-shielded-secure-boot \
        --shielded-vtpm \
        --shielded-integrity-monitoring \
        --labels=goog-ec-src=vm_add-gcloud \
        --reservation-affinity=any
    ```

1. Create an SSH tunnel through your GCE VM using port forwarding. This will
   listen to `127.0.0.1:5432` and forward through the GCE VM to your AlloyDB
   instance:

    ```bash
    gcloud compute ssh --project=$PROJECT_ID --zone=$ZONE $VM_INSTANCE \
                       -- -NL 5432:$ALLOYDB_IP:5432
    ```

    You will need to allow this command to run while you are connecting to
    AlloyDB. You may wish to open a new terminal to connect with.

1. Verify you can connect to your instance with the `psql` tool. Enter
   password for AlloyDB (`$DB_PASS` environment variable set above) when prompted:

    ```bash
    psql -h 127.0.0.1 -U postgres
    ```

## Initialize data in AlloyDB

1. While connected using `psql`, create a database and switch to it:

    ```bash
    CREATE DATABASE assistantdemo;
    \c assistantdemo
    ```

1. Install [`pgvector`][pgvector] extension in the database:

    ```bash
    CREATE EXTENSION vector;
    ```

1. Exit from `psql`:

    ```bash
    exit
    ```

1. Change into the retrieval service directory:

    ```bash
    cd genai-database-retrieval-app/retrieval_service
    ```

1. Install requirements:

    ```bash
    pip install -r requirements.txt
    ```

1. Make a copy of `example-config.yml` and name it `config.yml`.

    ```bash
    cp example-config.yml config.yml
    ```

1. Update `config.yml` with your database information. Keep using `127.0.0.1` as the datastore host IP address for port forwarding.

    ```bash
    host: 0.0.0.0
    datastore:
      # Example for postgres.py provider
      kind: "postgres"
      host: 127.0.0.1
      port: 5432
      # Update this with the database name
      database: "assistantdemo"
      # Update with database user, the default is `postgres`
      user: "postgres"
      # Update with database user password
      password: "my-alloydb-pass"
    ```

1. Populate data into database:

    ```bash
    python run_database_init.py
    ```

[pgvector]: https://github.com/pgvector/pgvector
