FROM apache/airflow:2.6.3

# Install any necessary Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
