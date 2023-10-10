# DEVELOPER.md

## Setup

We recommend using Python 3.11+ and installing the requirements into a virtualenv:
```bash
pip install -r extension_service/requirements.txt -r langchain_tools_demo/requirements.txt
```

If you are developing or otherwise running tests, install the test requirements as well:
```bash
pip install -r extension_service/requirements-test.txt -r langchain_tools_demo/requirements-test.txt
```

## Running the server

Create your database config:
```bash
cd extension_service
cp example-config.yml config.yml
```

Add your values to `config.yml`

Prepare the database:
```bash
python run_database_init.py
```

To run the app using uvicorn, execute the following:
```bash
python run_app.py
```

## Running the frontend

To run the app using streamlit, execute the following:
```bash
cd langchain_tools_demo
streamlit run run_app.py
```

## Testing

Run pytest to automatically run all tests:
```bash
export DB_USER=""
export DB_PASS=""
export DB_NAME=""
pytest
```

