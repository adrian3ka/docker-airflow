from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.dummy import DummyOperator
from airflow.operators.bash import BashOperator
from utils.ingest import main as ingest
from utils.report import generate_daily_report
from airflow.operators.python import PythonOperator

# Define default arguments
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 6, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Define the DAG
dag = DAG(
    'example_dag',
    default_args=default_args,
    description='A simple test DAG with a print task',
    schedule_interval=timedelta(days=1),
    catchup=False,
)


ingest_task = PythonOperator(
    task_id='ingest_task',
    python_callable=ingest,
    dag=dag,
)

report_task = PythonOperator(
    task_id='report_task',
    python_callable=generate_daily_report,
    dag=dag,
)

ingest_task >> report_task