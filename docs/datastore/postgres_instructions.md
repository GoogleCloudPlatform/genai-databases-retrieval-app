# Postgres Datastore Setup

## Database Setup

### Before you begin

1. Make sure you have a Google Cloud project and billing is enabled.

1. Set PROJECT_ID environment variable:

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
    gcloud services enable alloydb.googleapis.com compute.googleapis.com cloudresourcemanager.googleapis.com servicenetworking.googleapis.com vpcaccess.googleapis.com
    ```

### Enable private services access

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

2. Create a private connection:

    ```bash
    gcloud services vpc-peerings connect \
        --service=servicenetworking.googleapis.com \
        --ranges=$RANGE_NAME \
        --network=default
    ```


### Create a AlloyDB cluster and its primary instance

1. Set environment variables. For security reasons, use a different password for DB_PASS:

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

1. Create the primary instance:

    ```bash
    gcloud alloydb instances create $INSTANCE \
        --instance-type=PRIMARY \
        --cpu-count=8 \
        --region=$REGION \
        --cluster=$CLUSTER \
        --project=$PROJECT_ID
    ```

1. Get AlloyDB IP address:

    ```bash
    export ALLOY_IP=$(gcloud alloydb instances describe $INSTANCE \
        --cluster=$CLUSTER \
        --region=$REGION \
        --format=json | jq \
        --raw-output ".ipAddress")
    ```

1. Note the AlloyDB IP address for later use:

    ```bash
    echo $ALLOY_IP
    ```

### Connect to psql client and create a database

1. Set environment variables:

    ```bash
    export ZONE=us-central1-a
    export PROJECT_NUM=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
    export VM_INSTANCE=alloydb-vm-instance
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
        --create-disk=auto-delete=yes,boot=yes,device-name=$VM_INSTANCE,image=projects/ubuntu-os-cloud/global/images/ubuntu-2004-focal-v20231025,mode=rw,size=10,type=projects/$PROJECT_ID/zones/$ZONE/diskTypes/pd-balanced \
        --no-shielded-secure-boot \
        --shielded-vtpm \
        --shielded-integrity-monitoring \
        --labels=goog-ec-src=vm_add-gcloud \
        --reservation-affinity=any
    ```

1. SSH into the VM:

    ```bash
    gcloud compute ssh --project=$PROJECT_ID --zone=$ZONE $VM_INSTANCE
    ```

1. Install psql client from the package manager:

    ```bash
    sudo apt-get update
    sudo apt-get install --yes postgresql-client
    ```
1. Connect to your instance with the psql client tool:

    ```bash
    psql -h $ALLOY_IP -U postgres
    ```

1. Enter password for AlloyDB when prompted. If forgot, password could be found by the following command:

    ```bash
    echo $DB_PASS
    ```

1. Create a database:

    ```bash
    CREATE DATABASE assistantdemo;
    ```

1. Select database:

    ```bash
    \c assistantdemo
    ```

1. Install vector in database:

    ```bash
    CREATE EXTENSION vector;
    ```

1. Exit from psql and VM:

    ```bash
    exit
    ```

## Datastore Setup

### Before you begin

1. Enable APIs:

    ```bash
    gcloud services enable aiplatform.googleapis.com
    ```

1. Clone the repository:

    ```bash
    git clone git@github.com:GoogleCloudPlatform/database-query-extension.git
    ```

1. Download the [AlloyDB Auth Proxy
   client](https://cloud.google.com/alloydb/docs/auth-proxy/connect#install)

1. Get connection URIs for the AlloyDB instances:

    ```bash
    export CONN_URI=(projects/$PROJECT_ID/locations/$REGION/clusters/$CLUSTER/instances/$INSTANCE)
    ```

1. Start the auth proxy client:

    ```bash
    ./alloydb-auth-proxy $CONN_URI
    ```

### Populate data into database

1. Use a new terminal, change into the service directory:

    ```bash
    cd database-query-extension/extension_service
    ```
1. Make a copy of `example-config.yml` and name it `config.yml`.

    ```bash
    cp example-config.yml config.yml
    ```

1. Update `config.yml` with your database information.

    ```bash
    host: 0.0.0.0
    datastore:
      # Example for postgres.py provider
      kind: "postgres"
      # if not using AlloyDB auth proxy, update host with private IP
      # no change is needed if deployed to Cloud Run
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
