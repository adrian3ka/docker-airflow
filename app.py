import os
import datetime
import pysftp
import psycopg2
import schedule
import time

# SFTP configuration
sftp_host = os.getenv('SFTP_HOST', 'sftp')
sftp_port = int(os.getenv('SFTP_PORT', 22))
sftp_username = os.getenv('SFTP_USERNAME', 'sftpuser')
sftp_password = os.getenv('SFTP_PASSWORD', 'password')
sftp_directory = '/upload'
report_directory = '/upload/reports'

# PostgreSQL configuration
postgres_host = os.getenv('POSTGRES_HOST', 'postgres')
postgres_port = int(os.getenv('POSTGRES_PORT', 5432))
postgres_user = os.getenv('POSTGRES_USER', 'postgres')
postgres_password = os.getenv('POSTGRES_PASSWORD', 'postgres')
postgres_db = os.getenv('POSTGRES_DB', 'mydatabase')

# Disable host key checking
cnopts = pysftp.CnOpts()
cnopts.hostkeys = None

def generate_daily_report():
    conn = psycopg2.connect(
        host=postgres_host,
        port=postgres_port,
        user=postgres_user,
        password=postgres_password,
        dbname=postgres_db
    )
    cursor = conn.cursor()

    # Example: Generate daily loan summary report
    report_content = f"Daily Loan Summary Report - {datetime.date.today()}\n\n"

    # Query loan statistics by category
    cursor.execute(
        """
        SELECT category, COUNT(*), AVG(loan_amount), AVG(interest_rate)
        FROM loans
        GROUP BY category
        ORDER BY category
        """
    )
    results = cursor.fetchall()

    # Format the report content with the query results
    for row in results:
        category = row[0]
        count = row[1]
        avg_loan_amount = row[2]
        avg_interest_rate = row[3]

        report_content += f"Category: {category}\n"
        report_content += f"  Total Loans: {count}\n"
        report_content += f"  Average Loan Amount: ${avg_loan_amount:.2f}\n"
        report_content += f"  Average Interest Rate: {avg_interest_rate:.2f}%\n\n"

    # Write the report to a file
    report_filename = f"loan_summary_report_{datetime.date.today()}.txt"
    report_path = os.path.join('/tmp', report_filename)
    with open(report_path, 'w') as f:
        print(report_content)
        f.write(report_content)

    cursor.close()
    conn.close()

    # Upload report to SFTP
    upload_report_to_sftp(report_path)

def upload_report_to_sftp(report_path):
    # Connect to SFTP server and upload the report
    with pysftp.Connection(host=sftp_host, port=sftp_port, username=sftp_username, password=sftp_password, cnopts=cnopts) as sftp:
        sftp.cwd(report_directory)
        sftp.put(report_path)

def create_report_directory():
    with pysftp.Connection(host=sftp_host, port=sftp_port, username=sftp_username, password=sftp_password, cnopts=cnopts) as sftp:
        try:
            # Ensure the upload directory exists
            if not sftp.exists(sftp_directory):
                sftp.mkdir(sftp_directory)
                print(f"Created directory: {sftp_directory}")

            # Ensure the processed directory exists
            if not sftp.exists(report_directory):
                sftp.mkdir(report_directory)
                print(f"Created directory: {report_directory}")
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

if __name__ == "__main__":
    create_postgres_table()
    create_report_directory()
    # schedule.every().day.at("01:00").do(generate_daily_report)
    schedule.every(1).minutes.do(generate_daily_report)

    # Loop to run the scheduler continuously
    while True:
        schedule.run_pending()
        time.sleep(60) 
