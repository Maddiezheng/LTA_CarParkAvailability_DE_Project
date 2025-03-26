from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import StreamTableEnvironment, EnvironmentSettings
import os

def main():
    # 设置环境
    env = StreamExecutionEnvironment.get_execution_environment()
    settings = EnvironmentSettings.new_instance().in_streaming_mode().build()
    t_env = StreamTableEnvironment.create(env, settings)
    
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
    
    # 创建本地文件系统接收表
    t_env.execute_sql("""
    CREATE TABLE carpark_local_sink (
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
        'path' = 'file:///opt/flink/output',
        'format' = 'json',
        'json.encode.decimal-as-plain-number' = 'true'
    )
    """)

    # 执行查询
    t_env.execute_sql("""
        INSERT INTO carpark_local_sink
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