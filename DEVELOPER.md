# DEVELOPER.md

## Setup

We recommend using Python 3.11+ and installing the requirements into a virtualenv:
```
pip install -r requirements.text
```

If you are developing or otherwise running tests, install the test requirements as well:
```
pip install -r requirements-test.txt
```

## Running the server

To run the app using uvicorn, execute the following:
```
python run_server.py
```

## Testing

Run pytest to automatically run all tests: 
```
pytest
```