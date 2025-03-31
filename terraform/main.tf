terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "6.19.0"
    }
  }
}

provider "google" {
  credentials = file(var.credentials)
  project     = var.project
  region      = var.region
}

# GCS Data Lake Storage Bucket
resource "google_storage_bucket" "carpark_bucket" {
  name          = var.gcs_bucket_name
  location      = var.location
  force_destroy = true

  lifecycle_rule {
    condition {
      age = 30  # Keep for 30 days
    }
    action {
      type = "AbortIncompleteMultipartUpload"
    }
  }
}

# Create a directory for temporary files of Dataflow
resource "google_storage_bucket_object" "dataflow_temp_folder" {
  name    = "temp/"
  content = "temp folder for dataflow"
  bucket  = google_storage_bucket.carpark_bucket.name
}

# Create a directory for Dataflow staging files
resource "google_storage_bucket_object" "dataflow_staging_folder" {
  name    = "staging/"
  content = "staging folder for dataflow"
  bucket  = google_storage_bucket.carpark_bucket.name
}

# BigQuery Dataset - Raw Data
resource "google_bigquery_dataset" "raw_dataset" {
  dataset_id = var.raw_dataset_name
  location   = var.location
}

# BigQuery Dataset - Processed Data
resource "google_bigquery_dataset" "processed_dataset" {
  dataset_id = var.processed_dataset_name
  location   = var.location
}

# BigQuery raw data table
resource "google_bigquery_table" "carpark_availability_table" {
  dataset_id = google_bigquery_dataset.raw_dataset.dataset_id
  table_id   = "carpark_availability"
  deletion_protection = false

  time_partitioning {
    type  = "DAY"
    field = "timestamp"
  }

  schema = <<EOF
[
  {
    "name": "timestamp",
    "type": "TIMESTAMP",
    "mode": "REQUIRED"
  },
  {
    "name": "CarParkID",
    "type": "STRING",
    "mode": "REQUIRED"
  },
  {
    "name": "Area",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "Development",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "Location",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "Latitude",
    "type": "FLOAT",
    "mode": "NULLABLE"
  },
  {
    "name": "Longitude",
    "type": "FLOAT",
    "mode": "NULLABLE"
  },
  {
    "name": "AvailableLots",
    "type": "INTEGER",
    "mode": "NULLABLE"
  },
  {
    "name": "LotType",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "Agency",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "ingestion_time",
    "type": "TIMESTAMP",
    "mode": "REQUIRED"
  },
  {
    "name": "processing_time",
    "type": "TIMESTAMP",
    "mode": "REQUIRED"
  }
]
EOF
}

# Load Dataflow job script into GCS
resource "google_storage_bucket_object" "dataflow_job_file" {
  name   = "jobs/kafka_to_gcs_pipeline.py"
  bucket = google_storage_bucket.carpark_bucket.name
  source = "../processing/dataflow/kafka_to_gcs_pipeline.py"
}