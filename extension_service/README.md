# Setting up datastore

1. Make a copy of `example-config.yml` and name it `config.yml`.
2. Update `config.yml` with your database information.
3. The `datastore/provider` folder consist of code for different providers (e.g. postgres, cloudsql, alloydb…).
4. Configs that are required for each provider is listed in `class Config` within each provider file (e.g. postgres.py). Make sure those configs are added in `config.yml`.
5. (Optional) If add more functions or endpoints to the extension:
    - Add new function for provider in `datastore/provider/postgres.py`.
    - Add base Client class function in `datastore/datastore.py`.
    - Add new route in `app/routes.py`.
    - Add necessary unit tests in `app/app_test.py` and `datastore/provider/postgres_test.py`.
6. Run `python run_database_init.py` to populate data into your database.
