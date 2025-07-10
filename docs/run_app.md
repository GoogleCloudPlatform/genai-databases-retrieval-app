# Running the Agentic App Demo

##  Before you begin

1. Make sure you are able to [run Toolbox locally](../README.md#toolbox-setup).

1. Make sure you have [setup and initialized your
   Database](../README.md#database-setup).


1. Make sure you have Python 3.11+ installed

## Setting up your Environment

1. Set up [Application Default Credentials](https://cloud.google.com/docs/authentication/application-default-credentials#GAC):

    ```bash
    gcloud auth application-default login
    ```
    > [!TIP]
    > If you are running into `403` error, check to make sure the service
    > account you are using has the `Cloud Run Invoker` IAM in the retrieval
    > service project.

1. Install the dependencies using `pip`. You may wish to do this in a virtual
   environment, e.g. [venv](https://docs.python.org/3/library/venv.html):

    ```bash
    pip install -r requirements.txt
    ```

## Running the Demo

1. Start the app with:

    ```bash
    python run_app.py
    ```

    > [!TIP]
    > For hot reloading, use the `--reload` flag
    > ```bash
    > python run_app.py --reload`
    > ```

1. View app in your browser at http://localhost:8081
