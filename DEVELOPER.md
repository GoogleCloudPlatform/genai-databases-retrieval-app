# DEVELOPER.md

## Pre-reqs

See [Pre-reqs](./cloudrun_instructions.md).

## Setup

We recommend using Python 3.11+ and installing the requirements into a virtualenv:
```bash
pip install -r extension_service/requirements.txt -r langchain_tools_demo/requirements.txt
```

If you are developing or otherwise running tests, install the test requirements as well:
```bash
pip install -r extension_service/requirements-test.txt -r langchain_tools_demo/requirements-test.txt
```

## Run the app locally
### Running the extension service

1. Change into the service directory:

    ```bash
    cd extension_service
    ```

1. Create your database config:

    ```bash
    cp example-config.yml config.yml
    ```

1. Add your database config to `config.yml`:

1. Start the Cloud SQL Proxy or AlloyDB SSH tunnel.

1. To run the app using uvicorn, execute the following:

    ```bash
    python run_app.py
    ```

### Running the frontend

1. [Optional] Set up [Application Default Credentials](https://cloud.google.com/docs/authentication/application-default-credentials#GAC):

    ```bash
    export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
    ```

1. Change into the demo directory:

    ```bash
    cd langchain_tools_demo
    ```

1. Set the server port:

    ```bash
    export PORT=9090
    ```

1. [Optional] Set `BASE_URL` environment variable:

    ```bash
    export BASE_URL=<EXTENSION_SERVICE_URL>
    ```

1. [Optional] Set `DEBUG` environment variable:

    ```bash
    export DEBUG=True
    ```

1. To run the app using uvicorn, execute the following:

    ```bash
    python main.py
    ```

    Note: for hot reloading of the app use: `uvicorn main:app --host 0.0.0.0 --port 9090 --reload`

1. View app at `http://localhost:9090/`

## Testing

1. Set environment variables:

    ```bash
    export DB_USER=""
    export DB_PASS=""
    export DB_NAME=""
    export DB_HOST=""
    ```

1. Start the Cloud SQL Proxy or AlloyDB SSH tunnel.

1. Run pytest to automatically run all tests:

    ```bash
    pytest
    ```
