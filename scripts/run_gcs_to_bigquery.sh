#!/bin/bash
export GOOGLE_APPLICATION_CREDENTIALS="/Users/maddiezheng/Documents/LTA_CarParkAvailability_DE_Project/terraform/keys/lta-caravailability-a3190b400d81.json"
python "$(dirname "$0")/gcs_to_bigquery.py"