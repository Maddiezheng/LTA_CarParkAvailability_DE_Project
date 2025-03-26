from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import StreamTableEnvironment, EnvironmentSettings
import os

def main():
    # Set up the execution environment
    env = StreamExecutionEnvironment.get_execution_environment()
    settings = EnvironmentSettings.new_instance() \
                                 .in_streaming_mode() \
                                 .build()
    t_env = StreamTableEnvironment.create(env, settings)

    # 添加 GCS 配置，明确设置
    t_env.get_config().get_configuration().set_string("fs.gs.impl", "com.google.cloud.hadoop.fs.gcs.GoogleHadoopFileSystem")
    t_env.get_config().get_configuration().set_string("fs.AbstractFileSystem.gs.impl", "com.google.cloud.hadoop.fs.gcs.GoogleHadoopFS")
    t_env.get_config().get_configuration().set_string("fs.gs.auth.type", "SERVICE_ACCOUNT_JSON_KEYFILE")
    t_env.get_config().get_configuration().set_string("fs.allowed-fallback-filesystems", "gs")
    
    # 保持您原有的配置
    t_env.get_config().get_configuration().set_string("classloader.resolve-order", "parent-first")
    t_env.get_config().get_configuration().set_string("classloader.check-leaked-classloader", "false")

    # 其余部分保持不变...
    
    # 创建 Kafka 源表
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
    
    # 创建 GCS 接收表
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