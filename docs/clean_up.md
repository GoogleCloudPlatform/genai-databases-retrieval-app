# Clean up

The fastest way to clean up is to delete the entire Google Cloud project. Follow
the steps below if you want to keep the project but delete resources created
through this demo.

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

## Delete datastore resources

* [Clean up Alloydb](./datastore/alloydb.md#clean-up-resources)
* [Clean up Firestore](./datastore/firestore.md#clean-up-resources)
* [Clean up Cloud SQL for Postgres](./datastore/cloudsql_postgres.md#clean-up-resources)
* [Clean up Cloud SQL for MySQL](./datastore/cloudsql_mysqls.md#clean-up-resources)
