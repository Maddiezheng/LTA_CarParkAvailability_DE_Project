#!/bin/bash

# Configuration variable
PROJECT_ID="lta-caravailability"
REGION="asia-southeast1"
JOB_NAME="carpark-kafka-to-gcs-$(date +%Y%m%d-%H%M%S)"  # Add a timestamp to avoid duplicate names.
BUCKET_NAME="lta-carpark"
KAFKA_SERVER="localhost:9092"  # Local Kafka address

# Set authentication credentials
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/terraform/keys/lta-caravailability-a3190b400d81.json"

# Ensure Apache Beam installed 
pip install apache-beam[gcp] apache-beam[interactive] confluent-kafka

# Start Dataflow job
python3 processing/dataflow/kafka_to_gcs_pipeline.py \
  --project=$PROJECT_ID \
  --region=$REGION \
  --job_name=$JOB_NAME \
  --runner=DataflowRunner \
  --temp_location=gs://$BUCKET_NAME/temp \
  --staging_location=gs://$BUCKET_NAME/staging \
  --kafka_bootstrap_servers=$KAFKA_SERVER \
  --kafka_topic=carpark-availability \
  --output_path=gs://$BUCKET_NAME/carpark-data \
  --window_size=60 \
  --setup_file=./setup.py