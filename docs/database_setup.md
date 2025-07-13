# Database Setup Guide

This guide provides detailed instructions for setting up and configuring the
supported databases for Cymbal Air. This setup is required to populate the
database with the necessary data for the application to use.

> [!NOTE]
> This setup is only compatible with tools that support the `execute-sql`
> command. If you have already set up your own databases and they are populated
> with the required data, you may skip this step.

## Setup Instructions

Follow the steps below for the database of your choice.

### **1. Create Your Database Instance**

First, you need to create an instance of your chosen database. For detailed
instructions, select the appropriate guide below. If you already have an
instance, you can proceed to the next step.

* **[AlloyDB for PostgreSQL](https://cloud.google.com/alloydb/docs/quickstart)**
* **[Cloud SQL for PostgreSQL](https://cloud.google.com/sql/docs/postgres/quickstart)**
* **[Cloud SQL for MySQL](https://cloud.google.com/sql/docs/mysql/quickstart)**
* **[Cloud SQL for SQL Server](https://cloud.google.com/sql/docs/sqlserver/quickstart)**
* **[BigQuery](https://cloud.google.com/bigquery/docs/quickstarts/load-data-console)**
* **[Spanner](https://cloud.google.com/spanner/docs/quickstart-console)**
* **[PostgreSQL](https://www.postgresql.org/download/)**


### **2. Configure Environment Variables**

Next, configure the necessary environment variables in your terminal. These
variables are used by the MCP Toolbox to connect to your database for the
initial data load.

<br>

<details>
<summary><b>AlloyDB for PostgreSQL</b></summary>

```bash
export ALLOYDB_POSTGRES_PROJECT="<PROJECT_ID>"
export ALLOYDB_POSTGRES_REGION="<REGION>"
export ALLOYDB_POSTGRES_CLUSTER="<CLUSTER_NAME>"
export ALLOYDB_POSTGRES_INSTANCE="<INSTANCE_NAME>"
export ALLOYDB_POSTGRES_DATABASE="<DATABASE_NAME>"
export ALLOYDB_POSTGRES_USER="<USERNAME>"
export ALLOYDB_POSTGRES_PASSWORD="<PASSWORD>"
```
</details>
<details>
<summary><b>Cloud SQL for PostgreSQL</b></summary>

```bash
export CLOUD_SQL_POSTGRES_PROJECT="<PROJECT_ID>"
export CLOUD_SQL_POSTGRES_REGION="<REGION>"
export CLOUD_SQL_POSTGRES_INSTANCE="<INSTANCE_ID>"
export CLOUD_SQL_POSTGRES_DATABASE="<DATABASE_NAME>"
export CLOUD_SQL_POSTGRES_USER="<USER_ID>"
export CLOUD_SQL_POSTGRES_PASSWORD="<PASSWORD>"
```
</details>
<details>
<summary><b>Cloud SQL for MySQL</b></summary>

```bash
export CLOUD_SQL_MYSQL_PROJECT="<PROJECT_ID>"
export CLOUD_SQL_MYSQL_REGION="<REGION>"
export CLOUD_SQL_MYSQL_INSTANCE="<INSTANCE_ID>"
export CLOUD_SQL_MYSQL_DATABASE="<DATABASE_NAME>"
export CLOUD_SQL_MYSQL_USER="<USER_ID>"
export CLOUD_SQL_MYSQL_PASSWORD="<PASSWORD>"
```
</details>
<details>
<summary><b>Cloud SQL for SQL Server</b></summary>

```bash
export CLOUD_SQL_MSSQL_PROJECT="<PROJECT_ID>"
export CLOUD_SQL_MSSQL_REGION="<REGION>"
export CLOUD_SQL_MSSQL_INSTANCE="<INSTANCE_ID>"
export CLOUD_SQL_MSSQL_DATABASE="<DATABASE_NAME>"
export CLOUD_SQL_MSSQL_IP_ADDRESS="<IP_ADDRESS>"
export CLOUD_SQL_MSSQL_USER="<USER_ID>"
export CLOUD_SQL_MSSQL_PASSWORD="<PASSWORD>"
```
</details>
<details>
<summary><b>BigQuery</b></summary>

```bash
export BIGQUERY_PROJECT="<PROJECT_ID>"
```
</details>
<details>
<summary><b>Spanner</b></summary>

```bash
export SPANNER_PROJECT="<PROJECT_ID>"
export SPANNER_INSTANCE="<INSTANCE_NAME>"
export SPANNER_DATABASE="<DATABASE_NAME>"
```
</details>
<details>
<summary><b>PostgreSQL</b></summary>

```bash
export POSTGRES_HOST="<HOST>"
export POSTGRES_PORT="<PORT>"
export POSTGRES_DATABASE="<DATABASE_NAME>"
export POSTGRES_USER="<USERNAME>"
export POSTGRES_PASSWORD="<PASSWORD>"
```
</details>

### **3. Run Toolbox for Data Initialization**

With the environment variables set, run the MCP Toolbox with the `--prebuilt`
flag corresponding to your chosen database. This will start a temporary server
to allow for data initialization.

* **For AlloyDB for Postgres:**
  ```bash
  ./toolbox --prebuilt alloydb-postgres
  ```

* **For CloudSQL for Posgres:**
  ```bash
  ./toolbox --prebuilt cloud-sql-postgres
  ```

* **For Cloud SQL for MySQL:**
  ```bash
  ./toolbox --prebuilt cloud-sql-mysql
  ```

* **For Cloud SQL for SQL Server:**
  ```bash
  ./toolbox --prebuilt cloud-sql-mssql
  ```

* **For BigQuery:**
  ```bash
  ./toolbox --prebuilt bigquery
  ```

* **For Spanner:**
  ```bash
  ./toolbox --prebuilt spanner
  ```

* **For PostgreSQL:**
  ```bash
  ./toolbox --prebuilt postgres
  ```

### **4. Initialize the Database**

While Toolbox is running, open a new terminal and execute the database
initialization script. This will populate your database with the Cymbal Air
data.

```bash
python data/run_database_init.py
```

> [!TIP]
> You can also run `data/run_database_export.py` to export all data from your
> database to CSV.

### **5. Create the Final Toolbox Configuration**

Once the database is initialized, stop the temporary Toolbox server (with
`Cmd+C` or `Ctrl+C`). Now, create a `tools.yaml` file to define the data
sources, authentication, and tools for the agentic app.

Your `tools.yaml` file must contain the following sections:

* **A `sources` section**: Configure this section with a data source named
  `my-pg-instance` according to the **[official guide on configuring data
  sources](https://googleapis.github.io/genai-toolbox/resources/sources/)**.

* **[Optional] An `authServices` section**: To set it up, add a service named
  `my_google_service` by following the **[authServices configuration
  guide](https://googleapis.github.io/genai-toolbox/resources/authservices/)**.
  > [!NOTE]
  > This is section is only required if you want to enable ticket-related
  > features like booking or viewing a user's ticket history.

  > [!TIP]
  > You will need to **[create a Client
  > ID](https://support.google.com/cloud/answer/6158849)** for your app.

* **The `tools` and `toolsets` sections**: You don't need to write these from
  scratch. Simply copy the `tools` and `toolsets` sections directly from the
  [`tools.yaml`](../tools.yaml) file located in the root of this repository and
  paste them into your new configuration file.

### **6. Launch the Toolbox**

Finally, restart the Toolbox with your new `tools.yaml` config:

```bash
./toolbox --tools-file=PATH/TO/YOUR/tools.yaml
```

With these steps, your database is now set up and ready to be used with Cymbal
Air.
