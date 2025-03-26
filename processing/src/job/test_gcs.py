from pyflink.datastream import StreamExecutionEnvironment

def main():
    # 创建执行环境
    env = StreamExecutionEnvironment.get_execution_environment()
    
    # 配置GCS
    env.get_config().get_configuration().set_string("fs.gs.impl", "com.google.cloud.hadoop.fs.gcs.GoogleHadoopFileSystem")
    env.get_config().get_configuration().set_string("fs.AbstractFileSystem.gs.impl", "com.google.cloud.hadoop.fs.gcs.GoogleHadoopFS") 
    env.get_config().get_configuration().set_string("fs.gs.auth.type", "SERVICE_ACCOUNT_JSON_KEYFILE")
    env.get_config().get_configuration().set_string("fs.gs.auth.service.account.json.keyfile", "/opt/flink/gcp-credentials.json")
    env.get_config().get_configuration().set_string("fs.allowed-fallback-filesystems", "gs")
    
    # 打印配置信息
    print("Flink configuration:", env.get_config().get_configuration())
    
    # 尝试访问GCS
    try:
        # 这会触发文件系统初始化
        path = "gs://lta-carpark/test"
        print(f"Testing access to: {path}")
        
        # 执行作业
        env.execute("GCS Test Job")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
