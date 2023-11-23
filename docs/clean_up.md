# Clean up

## Before you begin

1. Set your PROJECT_ID environment variable:

    ```bash
    export PROJECT_ID=<YOUR_PROJECT_ID>
    ```

## Deleting Cloud Run deployment resources

1. Delete the Cloud Run service deployed:

    ```bash
    gcloud run services delete retrieval-service
    ```

1. Delete service account:

    ```bash
    gcloud iam service-accounts delete \
        retrieval-identity@$PROJECT_ID.iam.gserviceaccount.com
    ```

## Delete AlloyDB resources

1. Set environment variables:

    ```bash
    export VM_INSTANCE=alloydb-proxy-vm
    export CLUSTER=my-alloydb-cluster
    export REGION=us-central1
    export RANGE_NAME=my-allocated-range-default
    ```

1. Delete Compute Engine VM:

    ```bash
    gcloud compute instances delete $VM_INSTANCE
    ```

1. Delete AlloyDB cluster that contains instances:

    ```bash
    gcloud alloydb clusters delete $CLUSTER \
        --force \
        --region=$REGION \
        --project=$PROJECT_ID
    ```

1. Delete an allocated IP address range:

    ```bash
    gcloud compute addresses delete $RANGE_NAME \
        --global
    ```

## Delete Cloud Firestore resources

1. Go to your [project settings][firebase-settings] in the Firebase console.

1. At the bottom of the General settings page, click Delete project.

1. Select each checkbox to acknowledge the effects of deleting your project.

1. Click Delete project.

[firebase-settings]:https://console.firebase.google.com/project/_/settings/general/
