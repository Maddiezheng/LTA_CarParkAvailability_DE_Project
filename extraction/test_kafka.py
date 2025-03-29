# 文件名：test_kafka.py
from kafka import KafkaProducer, KafkaConsumer
import json
import time

def test_producer():
    try:
        # 创建生产者
        producer = KafkaProducer(
            bootstrap_servers=['34.126.86.205:9093'],
            value_serializer=lambda x: json.dumps(x).encode('utf-8')
        )
        
        # 发送测试消息
        test_message = {'test': 'message', 'timestamp': time.time()}
        producer.send('carpark-availability', test_message)
        producer.flush()
        producer.close()
        
        print("Successfully sent test message to Kafka")
        return True
    except Exception as e:
        print(f"Producer test failed: {str(e)}")
        return False

def test_consumer(timeout=10):
    try:
        # 创建消费者
        consumer = KafkaConsumer(
            'carpark-availability',
            bootstrap_servers=['34.126.86.205:9093'],
            auto_offset_reset='earliest',  # 确保可以接收之前的消息
            enable_auto_commit=True,
            group_id='test-group',
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )

        print("Listening for messages...")
        for message in consumer:
            print(f"Received message: {message.value}")

            consumer.close()
            return True
        
        consumer.close()
        print("No messages received in the specified timeout")
        return False
    except Exception as e:
        print(f"Consumer test failed: {str(e)}")
        return False

if __name__ == "__main__":
    # 测试Kafka连接
    print("Testing Kafka connection...")
    
    # 测试生产者
    producer_result = test_producer()
    
    if producer_result:
        # 测试消费者
        test_consumer()