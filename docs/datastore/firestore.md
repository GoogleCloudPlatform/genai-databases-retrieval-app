# Setup and configure Firestore

## Before you begin

1. Make sure you have a GoogleCloud project and billing is enabled.

1. Install required dependencies:
    ```bash
    cd extension_service
    pip install -r requirements.txt
    ```

## Create a Cloud Firestore database

1. In the [Firebase console](https://console.firebase.google.com), click `Add project`, then follow the on-screen instructions to create a Firebase project or to add Firebase services to an existing GCP project.

1. Navigate to the Cloud Firestore section of the Firebase console. You'll be prompted to select an existing Firebase project. Follow the database creation workflow.

## Initialize data in Firestore

1. Create or edit your existing `extension_service/config.yml`:

    ```bash
    host: 0.0.0.0
    datastore:
        kind: "firestore"
        projectId: <YOUR_GCP_PROJECT_ID> # (Optional) default to env variable `GCLOUD_PROJECT`
    ```

1. Change to the `extension_service` directory:

    ```bash
    cd extension_service
    ```

1. Populate your Firestore database with the command below. It will take several minutes to run:

    ```bash
    python run_database_init.py
    ```