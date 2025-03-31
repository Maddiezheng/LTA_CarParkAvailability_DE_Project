from kafka import KafkaProducer, KafkaConsumer
import json
import time

def test_producer():
    try:
        # Create producer
        producer = KafkaProducer(
            bootstrap_servers=['34.126.86.205:9093'],
            value_serializer=lambda x: json.dumps(x).encode('utf-8')
        )
        
        # Send test message
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
        # Create consumer
        consumer = KafkaConsumer(
            'carpark-availability',
            bootstrap_servers=['34.126.86.205:9093'],
            auto_offset_reset='earliest',  # Ensure that it is possible to receive previous messages
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
    # Test Kafka connection
    print("Testing Kafka connection...")
    
    # Test Producer
    producer_result = test_producer()
    
    if producer_result:
        # Test consumer
        test_consumer()