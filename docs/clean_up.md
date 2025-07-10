# Clean up

The fastest way to clean up is to delete the entire Google Cloud project. Follow
the steps below if you want to keep the project but delete resources created
through this demo.

## Before you begin

1. Set your `PROJECT_ID` environment variable:

    ```bash
    export PROJECT_ID=<YOUR_PROJECT_ID>
    ```

## Deleting Cloud Run deployment resources

1. Delete the Cloud Run service deployed:

    ```bash
    gcloud run services delete toolbox
    ```

1. Delete service account:

    ```bash
    gcloud iam service-accounts delete \
        toolbox-identity@$PROJECT_ID.iam.gserviceaccount.com
    ```

## Delete datastore resources

* **[AlloyDB for PostgreSQL](https://cloud.google.com/alloydb/docs/quickstart/create-and-connect#clean-up)**
* **[Cloud SQL for PostgreSQL](https://cloud.google.com/sql/docs/postgres/connect-instance-cloud-shell#clean-up)**
* **[Cloud SQL for MySQL](https://cloud.google.com/sql/docs/mysql/connect-instance-cloud-shell#clean-up)**
* **[Cloud SQL for SQL Server](https://cloud.google.com/sql/docs/sqlserver/connect-instance-cloud-shell#clean-up)**
* **[BigQuery](https://cloud.google.com/bigquery/docs/quickstarts/load-data-console#clean-up)**
* **[Spanner](https://cloud.google.com/spanner/docs/create-query-database-console#clean-up)**
