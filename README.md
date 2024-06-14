# Apache Airflow Setup with Docker Compose

## Prerequisites
- Docker installed on your machine
- Docker Compose installed on your machine
- Basic knowledge of command-line interface (CLI) operations

## Step-by-Step Guide

### Step 1: Set Up Your Project Directory
Ensure your project directory contains the following files and structure:
```
airflow-docker/
├── dags/
├── logs/
├── plugins/
├── docker-compose.yaml
├── Dockerfile
└── requirements.txt
```

### Step 2: Understand the `docker-compose.yaml` File
The `docker-compose.yaml` file sets up the necessary services for Airflow:

- **Postgres**: The database service for Airflow.
- **Airflow-init**: Initializes the Airflow database and creates the first admin user.
- **Webserver**: Runs the Airflow web interface.
- **Scheduler**: Schedules the Airflow tasks.

Important environment variables in the `docker-compose.yaml`:
- `AIRFLOW__CORE__SQL_ALCHEMY_CONN`: Connection string for the Postgres database.
- `AIRFLOW__CORE__FERNET_KEY`: Used for encrypting sensitive data in the database.
- `AIRFLOW__WEBSERVER__SECRET_KEY`: Secret key for the webserver.

### Step 3: Build the Docker Image
The `Dockerfile` installs any additional Python packages your DAGs might need. Ensure the `requirements.txt` file lists all required packages.

### Step 4: Create Directories
Create directories for DAGs, logs, and plugins if they don't already exist:

```bash
mkdir -p dags logs plugins
```
### Step 5: Initialize the Airflow Database
Run the following command to initialize the Airflow database and create the admin user:

bash
```bash
docker-compose up airflow-init
```

### Step 6: Start Airflow Services
Start the Airflow webserver and scheduler services:

```bash
docker-compose up
```

### Step 7: Access the Airflow Web Interface
Open your browser and navigate to http://localhost:8080. Log in using the default credentials:
```
Username: admin
Password: admin
```

### Step 8: Verify the Setup
Ensure that you can see the Airflow dashboard and access the DAGs. You can place your DAG files in the dags directory.
