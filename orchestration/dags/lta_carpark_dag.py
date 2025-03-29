from datetime import datetime, timedelta
import os
import json
import logging
import requests
from airflow.decorators import dag, task
from airflow.operators.python import PythonOperator
from airflow.providers.google.cloud.operators.dataflow import DataflowStartFlexTemplateOperator
from airflow.providers.google.cloud.operators.bigquery import BigQueryExecuteQueryOperator
from google.cloud import storage
from airflow.models import Variable


# Default arguments
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,  # Increased retries
    'retry_delay': timedelta(minutes=5),
}

# DAG definition
@dag(
    default_args=default_args,
    description='LTA Carpark Availability Pipeline',
    schedule_interval=timedelta(minutes=5),  # Runs every 5 minutes
    start_date=datetime(2025, 3, 28),
    catchup=False,
    tags=['carpark', 'lta', 'availability'],
)
def lta_carpark_pipeline():
    """
    LTA Carpark Availability ETL Pipeline:
    1. Fetch data from API and write to GCS (data lake)
    2. Use Dataflow to load GCS data to BigQuery (data warehouse)
    3. Clean duplicate data in BigQuery
    """
    
    # Step 1: Fetch data from API and write to GCS
    @task(task_id="fetch_api_to_gcs")
    def fetch_api_to_gcs(**kwargs):
        """Fetch carpark availability data from LTA API and write to GCS"""
        import requests
        from google.cloud import storage
        import json
        from datetime import datetime
        import uuid
        
        # API parameters
        base_url = 'https://datamall2.mytransport.sg/ltaodataservice/'
        endpoint = "CarParkAvailabilityv2"
        url = base_url + endpoint
        
        # API key
        api_key = Variable.get("lta_api_key")
        
        # Prepare headers
        headers = {'AccountKey': api_key, 'accept': 'application/json'}
        
        try:
            # Send API request
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            carparks = data.get('value', [])
            
            # Add timestamp and process coordinates
            timestamp = datetime.now().isoformat()
            for carpark in carparks:
                # Add timestamp
                carpark['timestamp'] = timestamp
                
                # Parse location coordinates
                if 'Location' in carpark:
                    try:
                        lat, lng = map(float, carpark['Location'].split())
                        carpark['Latitude'] = lat
                        carpark['Longitude'] = lng
                    except (ValueError, TypeError):
                        carpark['Latitude'] = None
                        carpark['Longitude'] = None
            
            # Get current time for filename - use UTC time for consistency
            current_time = datetime.utcnow().strftime('%Y%m%d-%H%M%S')
            unique_id = str(uuid.uuid4())[:8]
            day_folder = datetime.utcnow().strftime('%Y%m%d')
            filename = f"carpark-{current_time}-{unique_id}.json"
            
            # Connect to GCS and store data - organize data with date folders
            client = storage.Client()
            bucket = client.get_bucket("lta-carpark")
            blob = bucket.blob(f"carpark-data/{day_folder}/{filename}")
            
            # Write JSON formatted data, one record per line
            json_lines = '\n'.join([json.dumps(record) for record in carparks])
            blob.upload_from_string(json_lines)
            
            logging.info(f"Successfully fetched and wrote {len(carparks)} carpark records to GCS: gs://lta-carpark/carpark-data/{day_folder}/{filename}")
            
            # Return current date folder for next task
            return day_folder
            
        except Exception as e:
            logging.error(f"API request or save to GCS failed: {str(e)}")
            raise
    
    # Step 2: Prepare JavaScript transform file
    @task(task_id="prepare_transform_script")
    def prepare_transform_script(**kwargs):
        """Prepare JavaScript transform script on GCS"""
        from google.cloud import storage
        
        # Define transform script content
        transform_script = """
        function transform(line) {
          // Parse JSON
          var carparkData = JSON.parse(line);
          
          // Keep original fields
          return JSON.stringify(carparkData);
        }
        """
        
        # Upload to GCS
        client = storage.Client()
        bucket = client.bucket("lta-carpark")
        blob = bucket.blob("scripts/transform.js")
        blob.upload_from_string(transform_script)
        
        # Create schema file
        schema_json = {
            "BigQuery Schema": [
                {"name": "timestamp", "type": "TIMESTAMP", "mode": "REQUIRED"},
                {"name": "CarParkID", "type": "STRING", "mode": "REQUIRED"},
                {"name": "Area", "type": "STRING", "mode": "NULLABLE"},
                {"name": "Development", "type": "STRING", "mode": "NULLABLE"},
                {"name": "Location", "type": "STRING", "mode": "NULLABLE"},
                {"name": "Latitude", "type": "FLOAT", "mode": "NULLABLE"},
                {"name": "Longitude", "type": "FLOAT", "mode": "NULLABLE"},
                {"name": "AvailableLots", "type": "INTEGER", "mode": "NULLABLE"},
                {"name": "LotType", "type": "STRING", "mode": "NULLABLE"},
                {"name": "Agency", "type": "STRING", "mode": "NULLABLE"}
            ]
        }
        
        # Upload schema file
        schema_blob = bucket.blob("schemas/carpark_schema.json")
        schema_blob.upload_from_string(json.dumps(schema_json))
        
        return {
            "transform_path": "gs://lta-carpark/scripts/transform.js",
            "schema_path": "gs://lta-carpark/schemas/carpark_schema.json"
        }
    
    # Step 3: Use Dataflow template to load GCS data to BigQuery
    @task(task_id="start_gcs_to_bigquery", retries=5, retry_delay=timedelta(minutes=2))
    def start_gcs_to_bigquery(script_paths, day_folder, **kwargs):
        """Start Dataflow job to load from GCS to BigQuery"""
        from airflow.providers.google.cloud.operators.dataflow import DataflowStartFlexTemplateOperator
        
        # Changed location to North America region
        gcs_to_bigquery = DataflowStartFlexTemplateOperator(
            task_id="gcs_to_bigquery_dataflow",
            project_id="lta-caravailability",
            location="northamerica-northeast2",  # Changed to North America region
            wait_until_finished=False,  # Don't wait for completion to avoid Airflow resource issues
            body={
                "launchParameter": {
                    "containerSpecGcsPath": "gs://dataflow-templates-northamerica-northeast2/latest/flex/GCS_Text_to_BigQuery_Flex",  # Updated template path
                    "jobName": f"gcs-to-bq-job-{day_folder.replace('-', '')}",
                    "parameters": {
                        "javascriptTextTransformFunctionName": "transform",
                        "javascriptTextTransformGcsPath": script_paths["transform_path"],
                        "JSONPath": script_paths["schema_path"],
                        "inputFilePattern": f"gs://lta-carpark/carpark-data/{day_folder}/*.json",  # Only process that day's data
                        "outputTable": "lta-caravailability:carpark_raw.carpark_availability",
                        "bigQueryLoadingTemporaryDirectory": "gs://lta-carpark/temp/",
                        "tempLocation": "gs://lta-carpark/temp/",
                        "numWorkers": "1",  # Use minimum workers
                        "workerMachineType": "n1-standard-1"  # Use smaller machine type
                    }
                }
            }
        )
        
        # Execute job
        return gcs_to_bigquery.execute(context=kwargs)
    
    # Step 4: Clean duplicate data in BigQuery
    @task(task_id="clean_duplicate_data", trigger_rule="all_done")
    def clean_duplicate_data(**kwargs):
        """Clean duplicate data in BigQuery"""
        # Fix deduplication query to maintain partitioning
        dedup_query = """
        -- Create a temporary table with distinct records
        CREATE OR REPLACE TEMP TABLE temp_deduped AS
        SELECT DISTINCT * FROM `lta-caravailability.carpark_raw.carpark_availability`;

        -- Delete all records from the partitioned table
        DELETE FROM `lta-caravailability.carpark_raw.carpark_availability` 
        WHERE TRUE;

        -- Insert the deduplicated records back
        INSERT INTO `lta-caravailability.carpark_raw.carpark_availability`
        SELECT * FROM temp_deduped;
        """
        
        clean_task = BigQueryExecuteQueryOperator(
            task_id="clean_duplicates_in_bigquery",
            sql=dedup_query,
            use_legacy_sql=False,
            location="asia-southeast1",  # BigQuery location remains the same
        )
        
        return clean_task.execute(context=kwargs)
    
    # Define task dependencies
    day_folder = fetch_api_to_gcs()
    transform_files = prepare_transform_script()
    load_to_bq = start_gcs_to_bigquery(transform_files, day_folder)
    clean_duplicates = clean_duplicate_data()
    
    # Set task order
    day_folder >> transform_files >> load_to_bq >> clean_duplicates

# Instantiate DAG
carpark_dag = lta_carpark_pipeline()