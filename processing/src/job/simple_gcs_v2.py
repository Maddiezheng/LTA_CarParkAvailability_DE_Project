from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import StreamTableEnvironment, EnvironmentSettings
import os

def main():
    env = StreamExecutionEnvironment.get_execution_environment()
    settings = EnvironmentSettings.new_instance().in_streaming_mode().build()
    t_env = StreamTableEnvironment.create(env, settings)
    
    # 设置全局GCS配置
    t_env.get_config().get_configuration().set_string("fs.gs.impl", "com.google.cloud.hadoop.fs.gcs.GoogleHadoopFileSystem")
    t_env.get_config().get_configuration().set_string("fs.AbstractFileSystem.gs.impl", "com.google.cloud.hadoop.fs.gcs.GoogleHadoopFS")
    t_env.get_config().get_configuration().set_string("fs.gs.auth.type", "SERVICE_ACCOUNT_JSON_KEYFILE")
    t_env.get_config().get_configuration().set_string("fs.gs.auth.service.account.json.keyfile", "/opt/flink/gcp-credentials.json")
    t_env.get_config().get_configuration().set_string("fs.allowed-fallback-filesystems", "gs")
    
    # 创建Kafka源表
    t_env.execute_sql("""
    CREATE TABLE carpark_source (
        CarParkID STRING,
        Area STRING,
        Development STRING,
        AvailableLots INT,
        LotType STRING,
        Agency STRING,
        `timestamp` TIMESTAMP(3),
        Latitude DOUBLE,
        Longitude DOUBLE,
        proctime AS PROCTIME()
    ) WITH (
        'connector' = 'kafka',
        'topic' = 'carpark-availability',
        'properties.bootstrap.servers' = 'carpark-redpanda:29092',
        'properties.group.id' = 'carpark-consumer-group',
        'scan.startup.mode' = 'earliest-offset',
        'format' = 'json',
        'json.fail-on-missing-field' = 'false',
        'json.ignore-parse-errors' = 'true'
    )
    """)
    
    # 创建GCS接收表 - 使用Hadoop连接器
    t_env.execute_sql("""
    CREATE TABLE carpark_gcs_sink (
        CarParkID STRING,
        Area STRING,
        Development STRING,
        AvailableLots INT,
        LotType STRING,
        Agency STRING,
        `timestamp` TIMESTAMP(3),
        Latitude DOUBLE,
        Longitude DOUBLE
    ) WITH (
        'connector' = 'filesystem',
        'path' = 'gs://lta-carpark/carpark-data',
        'sink.rolling-policy.file-size' = '128MB',
        'sink.rolling-policy.rollover-interval' = '60 min',
        'sink.rolling-policy.check-interval' = '1 min',
        'format' = 'json',
        'json.encode.decimal-as-plain-number' = 'true'
    )
    """)

    # 执行查询
    t_env.execute_sql("""
        INSERT INTO carpark_gcs_sink
        SELECT 
            CarParkID,
            Area,
            Development,
            AvailableLots,
            LotType,
            Agency,
            `timestamp`,
            Latitude,
            Longitude
        FROM carpark_source
    """)

if __name__ == "__main__":
    main()
