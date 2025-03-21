.PHONY: up down terraform-init terraform-apply extract flink kestra

# 启动PostgreSQL和PgAdmin
up:
	docker-compose up -d

# 关闭所有容器
down:
	docker-compose down
	cd processing && docker-compose down
	cd orchestration && docker-compose down

# Terraform初始化
terraform-init:
	cd terraform && terraform init

# Terraform应用配置
terraform-apply:
	cd terraform && terraform apply

# 启动实时处理组件(Flink和Redpanda)
flink:
	cd processing && docker-compose up -d

# 启动Kestra编排服务
kestra:
	cd orchestration && docker-compose up -d

# 提交Flink作业
flink-job:
	cd processing && docker-compose exec jobmanager bash -c "./bin/flink run -py /opt/src/carpark_job.py --pyFiles /opt/src -d"

# 测试API
test-api:
	docker-compose run --rm python python extraction/test_api.py