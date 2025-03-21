from pyflink.datastream import StreamExecutionEnvironment
from pyflink.table import StreamTableEnvironment, EnvironmentSettings
import os
import json

def create_kafka_source_table(t_env, kafka_servers, topic_name, table_name):
    """
    Create a Kafka source table in Flink SQL
    """
    source_ddl = f"""
    CREATE TABLE {table_name} (
        CarParkID STRING,
        Area STRING,
        Development STRING,
        Location STRING,
        AvailableLots INT,
        LotType STRING,
        Agency STRING,
        `timestamp` TIMESTAMP(3),
        Latitude DOUBLE,
        Longitude DOUBLE,
        proctime AS PROCTIME()
    ) WITH (
        'connector' = 'kafka',
        'topic' = '{topic_name}',
        'properties.bootstrap.servers' = '{kafka_servers}',
        'properties.group.id' = 'carpark-consumer-group',
        'scan.startup.mode' = 'latest-offset',
        'format' = 'json',
        'json.fail-on-missing-field' = 'false',
        'json.ignore-parse-errors' = 'true'
    )
    """
    t_env.execute_sql(source_ddl)
    print(f"Created Kafka source table: {table_name}")

def create_postgres_sink_table(t_env, jdbc_url, jdbc_driver, username, password, table_name):
    """
    Create a PostgreSQL sink table in Flink SQL
    """
    sink_ddl = f"""
    CREATE TABLE {table_name} (
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
        'connector' = 'jdbc',
        'url' = '{jdbc_url}',
        'table-name' = 'carpark_availability',
        'driver' = '{jdbc_driver}',
        'username' = '{username}',
        'password' = '{password}'
    )
    """
    t_env.execute_sql(sink_ddl)
    print(f"Created PostgreSQL sink table: {table_name}")

def main():
    # Set up the execution environment
    env = StreamExecutionEnvironment.get_execution_environment()
    settings = EnvironmentSettings.new_instance() \
                                 .in_streaming_mode() \
                                 .build()
    t_env = StreamTableEnvironment.create(env, settings)

    # Configuration
    kafka_servers = "carpark-redpanda:29092"
    kafka_topic = "carpark-availability"
    kafka_table = "carpark_source"

    # Get PostgreSQL configuration from environment variables
    postgres_url = os.environ.get("POSTGRES_URL", "jdbc:postgresql://carpark-postgres:5432/carpark_db")
    postgres_user = os.environ.get("POSTGRES_USER", "root")
    postgres_password = os.environ.get("POSTGRES_PASSWORD", "root")
    postgres_driver = "org.postgresql.Driver"
    postgres_table = "carpark_sink"

    print(f"Connecting to PostgreSQL at: {postgres_url}")

    # Create source and sink tables
    create_kafka_source_table(t_env, kafka_servers, kafka_topic, kafka_table)
    create_postgres_sink_table(t_env, postgres_url, postgres_driver, postgres_user, postgres_password, postgres_table)

    # SQL query to process and transform data
    result = t_env.sql_query(f"""
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
        FROM {kafka_table}
    """)

    # Insert the result into PostgreSQL
    print("Executing insert into PostgreSQL...")
    result.execute_insert(postgres_table).wait()
    print("Job completed.")

if __name__ == "__main__":
    main()
