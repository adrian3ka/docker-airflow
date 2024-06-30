import os
import pysftp
import pandas as pd
import json
import xml.etree.ElementTree as ET
import psycopg2

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
postgres_user = os.getenv('POSTGRES_USER', 'airflow')
postgres_password = os.getenv('POSTGRES_PASSWORD', 'airflow')
postgres_db = os.getenv('POSTGRES_DB', 'airflow')

# Disable host key checking
cnopts = pysftp.CnOpts()
cnopts.hostkeys = None

# Mapping of category codes to descriptions
category_mapping = {
    'P': 'Personal Loan',
    'M': 'Mortgage Loan'
    # Add more mappings as needed
}

def list_files_in_sftp():
    with pysftp.Connection(host=sftp_host, port=sftp_port, username=sftp_username, password=sftp_password, cnopts=cnopts) as sftp:
        sftp.cwd(sftp_directory)
        files = sftp.listdir()
    return files

def ingest_csv_to_postgresql(file_name):
    with pysftp.Connection(host=sftp_host, port=sftp_port, username=sftp_username, password=sftp_password, cnopts=cnopts) as sftp:
        local_file_path = os.path.join('/tmp', file_name)
        sftp.get(os.path.join(sftp_directory, file_name), local_file_path)
    
    df = pd.read_csv(local_file_path)
    os.remove(local_file_path)
    transform_and_ingest_data(df, file_name)

def ingest_json_to_postgresql(file_name):
    with pysftp.Connection(host=sftp_host, port=sftp_port, username=sftp_username, password=sftp_password, cnopts=cnopts) as sftp:
        local_file_path = os.path.join('/tmp', file_name)
        sftp.get(os.path.join(sftp_directory, file_name), local_file_path)
    
    with open(local_file_path, 'r') as json_file:
        data = json.load(json_file)
    
    os.remove(local_file_path)
    
    # Transform category_code to category_desc
    for entry in data:
        entry['category'] = category_mapping.get(entry['category_code'], 'Unknown')
    
    df = pd.json_normalize(data)
    transform_and_ingest_data(df, file_name)

def ingest_xml_to_postgresql(file_name):
    with pysftp.Connection(host=sftp_host, port=sftp_port, username=sftp_username, password=sftp_password, cnopts=cnopts) as sftp:
        local_file_path = os.path.join('/tmp', file_name)
        sftp.get(os.path.join(sftp_directory, file_name), local_file_path)
    
    tree = ET.parse(local_file_path)
    os.remove(local_file_path)
    root = tree.getroot()

    data = []
    columns = []
    for elem in root.findall('*'):
        if not columns:
            columns = list(elem.attrib.keys())
        entry = {col: elem.attrib.get(col) for col in columns}
        entry['category'] = category_mapping.get(entry['category_code'], 'Unknown')
        data.append(entry)

    df = pd.DataFrame(data, columns=columns + ['category'])
    transform_and_ingest_data(df, file_name)

def transform_and_ingest_data(df, file_name):
    conn = psycopg2.connect(
        host=postgres_host,
        port=postgres_port,
        user=postgres_user,
        password=postgres_password,
        dbname=postgres_db
    )
    cursor = conn.cursor()
    
    for index, row in df.iterrows():
        cursor.execute(
            """
            INSERT INTO loans (loan_id, borrower_name, loan_amount, interest_rate, loan_date, category) 
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (row['loan_id'], row['borrower_name'], row['loan_amount'], row['interest_rate'], row['loan_date'], row['category'])
        )
    
    conn.commit()
    cursor.close()
    conn.close()

    # Move the processed file to the 'processed' directory
    with pysftp.Connection(host=sftp_host, port=sftp_port, username=sftp_username, password=sftp_password, cnopts=cnopts) as sftp:
        sftp.rename(os.path.join(sftp_directory, file_name), os.path.join(sftp_processed_directory, file_name))

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
        CREATE TABLE IF NOT EXISTS loans ( loan_id INT PRIMARY KEY, borrower_name VARCHAR(255), loan_amount NUMERIC, interest_rate NUMERIC, loan_date DATE, category VARCHAR(255) );
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
        elif file.endswith('.json'):
            ingest_json_to_postgresql(file)
        elif file.endswith('.xml'):
            ingest_xml_to_postgresql(file)
