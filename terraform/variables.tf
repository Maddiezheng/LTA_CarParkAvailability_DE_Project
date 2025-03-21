variable "credentials" {
    description = "GCP Credentials"
    default = "./keys/credentials.json"
}

variable "project" {
    description = "GCP Project ID"
    # 替换成你的项目ID
    default = "your-project-id"
}

variable "region" {
    description = "GCP Region"
    # 选择新加坡区域
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
    # 替换成你想要的桶名
    default = "your-project-id-carpark-data"
}

variable "gcs_storage_class" {
    description = "Bucket Storage Class"
    default = "STANDARD"
}