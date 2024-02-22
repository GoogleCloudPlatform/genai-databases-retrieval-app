# DEVELOPER.md

## LangSmith Tracing setup

### Enable LLM Tracing

1. Create an account and API key - https://docs.smith.langchain.com/setup
2. Set environment variables to enable LLM tracing.

```bash
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_API_KEY=<Your API Key>
```

3. After starting/deploying application and sending several prompts, open LangSmith website to explore LLM traces - https://smith.langchain.com

### Running the frontend

1. Change into the demo directory:

    ```bash
    cd langchain_tools_demo
    ```

1. To use a live retrieval service on Cloud Run:

    1. Set Google user credentials:

        ```bash
        gcloud auth login
        ```

    1. Set `BASE_URL` environment variable:

        ```bash
        export BASE_URL=$(gcloud run services describe retrieval-service --format 'value(status.url)')
        ```

    1. Allow your account to invoke the Cloud Run service by granting the [role Cloud Run invoker][invoker]

1. [Optional] Turn on debugging by setting the `DEBUG` environment variable:

    ```bash
    export DEBUG=True
    ```

1. To run the app using uvicorn, execute the following:

    ```bash
    python main.py
    ```

    Note: for hot reloading of the app use: `uvicorn main:app --host 0.0.0.0 --reload --port 8081`

1. View app at `http://localhost:8081/`

## Cloud Run

### Deployment to Cloud Run

Note: LangSmith API key is passed as environment variable for testing/demo purposes only.
For production applications, you need to store sensitive information, like API keys, in Secrets Manager.


```bash
export BASE_URL=$(gcloud  run services list --filter="(retrieval-service)" --format="value(URL)")

gcloud alpha run deploy assistant-app \
    --source=. \
    --allow-unauthenticated \
    --service-account compute-aip \
    --region us-central1 \
    --network=default \
    --set-env-vars DEBUG=true,BASE_URL=$BASE_URL,LANGCHAIN_TRACING_V2=true,LANGCHAIN_API_KEY=YOUR_API_KEY \
    --quiet
```
