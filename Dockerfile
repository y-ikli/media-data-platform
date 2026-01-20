FROM apache/airflow:2.9.3-python3.11

# Copy requirements
COPY requirements.txt /requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r /requirements.txt

# Copy source code
COPY src /opt/airflow/src
COPY dags /opt/airflow/dags

WORKDIR /opt/airflow
