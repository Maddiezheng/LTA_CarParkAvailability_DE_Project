output "bucket_name" {
  value       = google_storage_bucket.carpark_bucket.name
  description = "The GCS bucket name"
}

output "raw_dataset" {
  value       = google_bigquery_dataset.raw_dataset.dataset_id
  description = "BigQuery raw dataset ID"
}

output "processed_dataset" {
  value       = google_bigquery_dataset.processed_dataset.dataset_id
  description = "BigQuery processed dataset ID"
}