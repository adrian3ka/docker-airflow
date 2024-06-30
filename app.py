import os
import pysftp
import pandas as pd
import psycopg2
import paramiko

# SFTP configuration
sftp_host = os.getenv('SFTP_HOST', 'sftp')
sftp_port = int(os.getenv('SFTP_PORT', 22))
sftp_username = os.getenv('SFTP_USERNAME', 'sftpuser')
sftp_password = os.getenv('SFTP_PASSWORD', 'password')
sftp_directory = '/upload'
sftp_processed_directory = '/upload/processed'

# PostgreSQL configuration
postgres_host = os.getenv('POSTGRES_HOST', 'postgres')
postgres_port = int(os.getenv('POSTGRES_PORT', 5432))
postgres_user = os.getenv('POSTGRES_USER', 'postgres')
postgres_password = os.getenv('POSTGRES_PASSWORD', 'postgres')
postgres_db = os.getenv('POSTGRES_DB', 'mydatabase')

# Disable host key checking
cnopts = pysftp.CnOpts()
cnopts.hostkeys = None

def list_files_in_sftp():
    with pysftp.Connection(host=sftp_host, port=sftp_port, username=sftp_username, password=sftp_password, cnopts=cnopts) as sftp:
        sftp.cwd(sftp_directory)
        files = sftp.listdir()
    return files

def ingest_csv_to_postgresql(file_name):
    print(f"this function will ingest {file_name}")
    #TODO: create postgres ingestion system
    return 

def create_processed_directory():
    with pysftp.Connection(host=sftp_host, port=sftp_port, username=sftp_username, password=sftp_password, cnopts=cnopts) as sftp:
        try:
            # Ensure the upload directory exists
            if not sftp.exists(sftp_directory):
                sftp.mkdir(sftp_directory)
                print(f"Created directory: {sftp_directory}")

            # Ensure the processed directory exists
            if not sftp.exists(sftp_processed_directory):
                sftp.mkdir(sftp_processed_directory)
                print(f"Created directory: {sftp_processed_directory}")
        except Exception as e:
            print(f"Error creating directory on SFTP server: {e}")

def create_postgres_table():
    
    conn = psycopg2.connect(
        host=postgres_host,
        port=postgres_port,
        user=postgres_user,
        password=postgres_password,
        dbname=postgres_db
    )
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE loans ( loan_id INT PRIMARY KEY, borrower_name VARCHAR(255), loan_amount NUMERIC, interest_rate NUMERIC, loan_date DATE, category VARCHAR(255) );
        """
    )
    
    conn.commit()
    cursor.close()
    conn.close()

def main():
    create_postgres_table()
    create_processed_directory()
    files = list_files_in_sftp()
    for file in files:
        if file.endswith('.csv'):
            ingest_csv_to_postgresql(file)

if __name__ == "__main__":
    main()
