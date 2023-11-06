# Init Database with Cloud Run Job

Use a Cloud Run Job to connect to AlloyDB within your
VPC Network.

1. [Before you begin](./alloydb.md#before-you-begin)
1. [Setup your AlloyDB](./alloydb.md#create-a-alloydb-cluster)

1. Set environment variables:

    ```
    export DB_HOST=$(gcloud alloydb instances describe $INSTANCE --cluster $CLUSTER --region $REGION --format 'value(ipAddress)')
    export DB_NAME=assistantdemo
    export DB_USER=postgres
    ```

1. Create a Cloud Run job to:

    ```
    gcloud alpha run jobs deploy database-init-job --source . \
        --set-env-vars=DB_HOST=$DB_HOST \
        --set-env-vars=DB_NAME=$DB_NAME \
        --set-env-vars=DB_USER=$DB_USER \
        --set-env-vars=DB_PASS=$DB_PASS \
        --region $REGION \
        --network=default \
        --subnet=default
    ```

1. Execute the Cloud Run job:

    ```
    gcloud run jobs execute database-init-job
    ```