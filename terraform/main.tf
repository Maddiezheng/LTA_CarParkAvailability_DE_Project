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

# GCS 数据湖存储桶
resource "google_storage_bucket" "carpark_bucket" {
  name          = var.gcs_bucket_name
  location      = var.location
  force_destroy = true

  lifecycle_rule {
    condition {
      age = 30  # 保留30天
    }
    action {
      type = "AbortIncompleteMultipartUpload"
    }
  }
}

# BigQuery 数据集 - 原始数据
resource "google_bigquery_dataset" "raw_dataset" {
  dataset_id = var.raw_dataset_name
  location   = var.location
}

# BigQuery 数据集 - 处理后数据
resource "google_bigquery_dataset" "processed_dataset" {
  dataset_id = var.processed_dataset_name
  location   = var.location
}

# BigQuery 原始数据表
resource "google_bigquery_table" "carpark_availability_table" {
  dataset_id = google_bigquery_dataset.raw_dataset.dataset_id
  table_id   = "carpark_availability"
  
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
  }
]
EOF
}