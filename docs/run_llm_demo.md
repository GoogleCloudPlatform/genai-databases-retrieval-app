# Running the LLM App Demo

##  Before you begin

1. Make sure you've [setup and initialized your
   Database](../README.md#setting-up-your-database).

1. Make sure you've [deployed your retrieval service, and are running a
   connection to it locally on
   127.0.0.1:8080](../README.md#deploying-the-retrieval-service).

1. Make sure you have Python 3.11+ installed

## Setting up your Environment

1. Set up [Application Default Credentials](https://cloud.google.com/docs/authentication/application-default-credentials#GAC):

    ```bash
    gcloud auth application-default login
    ```
    * Tip: if you are running into `403` error, check to make sure the service account you are using has the `Cloud Run Invoker` IAM in the retrieval service project.

1. Change into the `llm_demo` directory:

    ```bash
    cd llm_demo 
    ```

1. Set orchestrator environment variable:

    | orchestration-type            | Description                                 |
    |-------------------------------|---------------------------------------------|
    | langchain-tools               | LangChain tools orchestrator.               |

    ```bash
    export ORCHESTRATION_TYPE=<orchestration-type>
    ```

1. Install the dependencies using `pip`. You may wish to do this in a
   [venv](https://docs.python.org/3/library/venv.html):

    ```bash
    pip install -r requirements.txt
    ```

1. [Optional] If you want to take advantage of the user authentication features, [create a Client ID](https://support.google.com/cloud/answer/6158849) for your app and save it as an environment variable:

    ```bash
    export CLIENT_ID=<Your Client ID>
    ```


## Running the Demo

1. Start the application with:

    ```bash
    python run_app.py
    ```

    Note: for hot reloading of the app use: `uvicorn main:app --host 0.0.0.0 --reload`

1. View app at `http://localhost:8081/`
