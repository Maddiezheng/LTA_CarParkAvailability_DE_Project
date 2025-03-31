.PHONY: up down terraform-init terraform-apply extract flink kestra

# Start PostgreSQL and PgAdmin
up:
	docker-compose up -d

# Close all containers
down:
	docker-compose down
	cd processing && docker-compose down
	cd orchestration && docker-compose down

# Terraform Initialization
terraform-init:
	cd terraform && terraform init

# Terraform Application Configuration
terraform-apply:
	cd terraform && terraform apply

# Start Real-time Processing Components (Flink and Redpanda)
flink:
	cd processing && docker-compose up -d

# Start Kestra orchestration service
kestra:
	cd orchestration && docker-compose up -d

Submit Flink job
flink-job:
	cd processing && docker-compose exec jobmanager bash -c "./bin/flink run -py /opt/src/carpark_job.py --pyFiles /opt/src -d"

# Test API
test-api:
	docker-compose run --rm python python extraction/test_api.py