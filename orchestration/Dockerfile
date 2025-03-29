FROM apache/airflow:2.8.1

# Install Google Cloud and Apache provider packages
RUN pip install --no-cache-dir \
    apache-airflow-providers-google \
    apache-airflow-providers-apache-kafka \
    apache-airflow-providers-apache-beam

COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt