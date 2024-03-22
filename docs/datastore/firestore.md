# Setup and configure Firestore

## Before you begin

1. Make sure you have a GoogleCloud project and billing is enabled.

1. Install required dependencies:
    ```bash
    cd retrieval_service
    pip install -r requirements.txt
    ```

## Create a Cloud Firestore database

1. In the [Firebase console](https://console.firebase.google.com), click `Add project`, then follow the on-screen instructions to create a Firebase project or to add Firebase services to an existing GCP project.

1. Navigate to the Cloud Firestore section of the Firebase console. You'll be prompted to select an existing Firebase project. Follow the database creation workflow.

## Initialize data in Firestore

1. Create or edit your existing `retrieval_service/config.yml`:

    ```bash
    host: 0.0.0.0
    datastore:
        kind: "firestore"
        projectId: <YOUR_GCP_PROJECT_ID> # (Optional) default to env variable `GCLOUD_PROJECT`
    ```

1. Change to the `retrieval_service` directory:

    ```bash
    cd retrieval_service
    ```

1. Populate your Firestore database with the command below.

    * To populate only some rows into database quickly, run:

        ```bash
        python run_database_init.py
        ```

    * To load all the data for a complete experience, run:

        ```bash
        python run_database_init.py --load-all-data
        ```

        Note: This may take up to 5-10 min and will result in a higher DB write cost

## Clean up resources

Clean up after completing the demo.

1. Delete the default firestore database:

    ```bash
    gcloud alpha firestore databases delete --database='(default)'
    ```
