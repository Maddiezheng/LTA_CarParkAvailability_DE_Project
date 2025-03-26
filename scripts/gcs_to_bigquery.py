from google.cloud import bigquery
from google.cloud import storage
import os
import datetime
import json
import logging

# Set Log
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
PROJECT_ID = "lta-caravailability"
DATASET_ID = "carpark_raw"
TABLE_ID = "carpark_availability"
BUCKET_NAME = "lta-carpark"
SOURCE_FOLDER = "carpark-data"
CREDENTIALS_PATH = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", 
                               "/Users/maddiezheng/Documents/LTA_CarParkAvailability_DE_Project/terraform/keys/lta-caravailability-a3190b400d81.json")

def setup_clients():
    """Initialize BigQuery and Storage clients"""
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = CREDENTIALS_PATH
    logger.info(f"Using credentials from: {CREDENTIALS_PATH}")

    try:
        bq_client = bigquery.Client()
        storage_client = storage.Client()
        logger.info("Successfully initialized GCP clients")
        return bq_client, storage_client
    except Exception as e:
        logger.error(f"Failed to initialize clients: {e}")
        raise

def check_for_new_files(storage_client):
    """Check the new file in GCS"""
    try:
        bucket = storage_client.bucket(BUCKET_NAME)
        blobs = list(bucket.list_blobs(prefix=SOURCE_FOLDER))

        # Retrieve the list of processed files
        processed_files = get_processed_files(storage_client)

        # Filter out a new file
        new_files = [blob for blob in blobs if
                    blob.name.endswith('.json') and
                    blob.name not in processed_files]

        logger.info(f"Found {len(new_files)} new files to process")
        return new_files
    except Exception as e:
        logger.error(f"Error checking for new files: {e}")
        raise

def get_processed_files(storage_client):
    """Retrieve the list of processed files from a certain record"""
    try:
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob("processed_files.txt")
        if blob.exists():
            content = blob.download_as_text()
            processed = set(content.splitlines())
            logger.info(f"Found {len(processed)} previously processed files")
            return processed
        logger.info("No previously processed files record found")
        return set()
    except Exception as e:
        logger.error(f"Error getting processed files: {e}")
        return set()

def mark_as_processed(storage_client, filenames):
    """Mark the file as processed"""
    if not filenames:
        return

    try:
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob("processed_files.txt")

        # Retrieve the current list of processed files
        processed_files = get_processed_files(storage_client)

        # Add new file for processing
        processed_files.update(filenames)

        # Update Record
        blob.upload_from_string('\n'.join(processed_files))
        logger.info(f"Marked {len(filenames)} files as processed")
    except Exception as e:
        logger.error(f"Error marking files as processed: {e}")
        raise

def create_temp_enhanced_file(storage_client, blob):
    """Create an enhanced temporary file from the original JSON file (adding ingestion time)."""
    try:
        bucket = storage_client.bucket(BUCKET_NAME)
        content = blob.download_as_text()
        lines = content.strip().split('\n')

        # Add intake time
        now = datetime.datetime.utcnow().isoformat()
        enhanced_lines = []
        valid_lines = 0

        for line in lines:
            if line.strip():  # Skip empty lines
                try:
                    data = json.loads(line)
                    data['ingestion_time'] = now
                    enhanced_lines.append(json.dumps(data))
                    valid_lines += 1
                except json.JSONDecodeError:
                    logger.warning(f"Error parsing JSON: {line[:100]}...")

        if not enhanced_lines:
            logger.warning(f"No valid data found in {blob.name}")
            return None

        # Create a temporary enhanced file
        temp_blob_name = f"{blob.name}.enhanced"
        temp_blob = bucket.blob(temp_blob_name)
        temp_blob.upload_from_string('\n'.join(enhanced_lines))

        logger.info(f"Created enhanced file with {valid_lines} records: {temp_blob_name}")
        return temp_blob_name
    except Exception as e:
        logger.error(f"Error creating enhanced file for {blob.name}: {e}")
        return None

def load_json_to_bigquery(bq_client, source_uri):
    """JSON file load into BigQuery"""
    table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        schema=[
            bigquery.SchemaField("CarParkID", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("Area", "STRING"),
            bigquery.SchemaField("Development", "STRING"),
            bigquery.SchemaField("AvailableLots", "INTEGER"),
            bigquery.SchemaField("LotType", "STRING"),
            bigquery.SchemaField("Agency", "STRING"),
            bigquery.SchemaField("timestamp", "TIMESTAMP"),
            bigquery.SchemaField("Latitude", "FLOAT"),
            bigquery.SchemaField("Longitude", "FLOAT"),
            bigquery.SchemaField("ingestion_time", "TIMESTAMP", mode="REQUIRED")
        ],
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        ignore_unknown_values=True,
    )

    try:
        # Load data
        load_job = bq_client.load_table_from_uri(
            source_uri, table_ref, job_config=job_config
        )

        # Waiting for the task to be completed
        load_job.result()

        logger.info(f"Successfully loaded data from {source_uri} into {table_ref}")
        return True
    except Exception as e:
        logger.error(f"Error loading data into BigQuery: {e}")
        return False

def cleanup_temp_file(storage_client, temp_blob_name):
    """Clear temporary files"""
    if not temp_blob_name:
        return

    try:
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(temp_blob_name)
        blob.delete()
        logger.info(f"Deleted temporary file: {temp_blob_name}")
    except Exception as e:
        logger.warning(f"Error deleting temporary file {temp_blob_name}: {e}")

def main():
    try:
        # Set client
        bq_client, storage_client = setup_clients()

        # Obtain new file
        new_files = check_for_new_files(storage_client)

        if not new_files:
            logger.info("No new files to process")
            return

        # Process each file
        processed = []
        for blob in new_files:
            logger.info(f"Processing {blob.name}")

            # Create an enhanced file
            temp_blob_name = create_temp_enhanced_file(storage_client, blob)
            if not temp_blob_name:
                continue

            # GCS URI
            temp_uri = f"gs://{BUCKET_NAME}/{temp_blob_name}"

            # Load into BigQuery
            success = load_json_to_bigquery(bq_client, temp_uri)

            # Clear temporary files
            cleanup_temp_file(storage_client, temp_blob_name)

            if success:
                processed.append(blob.name)

        # Mark all files successfully processed
        if processed:
            mark_as_processed(storage_client, processed)
            logger.info(f"Successfully processed {len(processed)} files")

    except Exception as e:
        logger.error(f"Error in main process: {e}")
        raise

if __name__ == "__main__":
    main()
