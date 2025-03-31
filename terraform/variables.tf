variable "credentials" {
    description = "GCP Credentials"
    # Replace with your credential path
    default = "./keys/lta-caravailability-a3190b400d81.json"
}

variable "project" {
    description = "GCP Project ID"
    # Replace with your project ID
    default = "lta-caravailability"
}

variable "region" {
    description = "GCP Region"
    # Replace with your location
    default = "asia-southeast1"
}

variable "location" {
    description = "Data Location"
    default = "asia-southeast1"
}

variable "raw_dataset_name" {
  description = "BigQuery Raw Dataset Name"
  default     = "carpark_raw"
}

variable "processed_dataset_name" {
  description = "BigQuery Processed Dataset Name"
  default     = "carpark_processed"
}

variable "gcs_bucket_name" {
    description = "Data Lake Bucket Name"
    # bucket name
    default = "lta-carpark"
}

variable "gcs_storage_class" {
    description = "Bucket Storage Class"
    default = "STANDARD"
}

variable "dataproc_cluster_name" {
  description = "Dataproc Cluster Name"
  default     = "carpark-flink-cluster"
}

variable "dataproc_machine_type" {
  description = "Machine type for Dataproc cluster nodes"
  default     = "n1-standard-2"
}

variable "dataproc_image_version" {
  description = "Dataproc image version"
  default     = "2.1-debian10"
}