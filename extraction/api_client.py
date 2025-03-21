#!/usr/bin/env python
import os
import json
import time
import logging
import requests
from typing import Dict, List, Optional
from datetime import datetime
from dotenv import load_dotenv
from kafka import KafkaProducer


class LTAApiHandler:
    """Handler for LTA DataMall API operations"""

    def __init__(self, base_url: str = 'https://datamall2.mytransport.sg/ltaodataservice/'):
        """
        Initialize LTA API handler
        
        Args:
            base_url (str): Base URL for the API
        """
        # Setup logging
        self._setup_logger()
        
        # Load environment variables
        load_dotenv()
        
        self.base_url = base_url
        self.api_key = self._get_api_key()
        self.headers = {'AccountKey': self.api_key, 'accept': 'application/json'}
        
        # Create data directory
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        os.makedirs(self.data_dir, exist_ok=True)
    
    def _setup_logger(self) -> None:
        """Configure the logger"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def _get_api_key(self) -> str:
        """
        Get API key from environment variables
        
        Returns:
            str: API key
            
        Raises:
            ValueError: If API key is not found
        """
        api_key = os.getenv("LTA_API_KEY")
        if not api_key:
            self.logger.error("API key not found. Please set LTA_API_KEY in .env file")
            raise ValueError("API key not found. Please set LTA_API_KEY in .env file")
        return api_key
    
    def get_carpark_availability(self) -> List[Dict]:
        """
        Get carpark availability data
        
        Returns:
            List[Dict]: List containing carpark data
            
        Raises:
            RuntimeError: If API request fails
        """
        endpoint = "CarParkAvailabilityv2"
        url = self.base_url + endpoint
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            carparks = data.get('value', [])
            
            # Add timestamp and process location coordinates
            self._enrich_carpark_data(carparks)
            
            self.logger.info(f"Successfully retrieved {len(carparks)} carpark records")
            return carparks
            
        except requests.RequestException as e:
            error_msg = f"API request failed: {str(e)}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def _enrich_carpark_data(self, carparks: List[Dict]) -> None:
        """
        Enrich carpark data with timestamp and parsed coordinates
        
        Args:
            carparks (List[Dict]): List of carpark data
        """
        timestamp = datetime.now().isoformat()
        
        for carpark in carparks:
            # Add timestamp
            carpark['timestamp'] = timestamp
            
            # Parse location coordinates
            if 'Location' in carpark:
                try:
                    lat, lng = map(float, carpark['Location'].split())
                    carpark['Latitude'] = lat
                    carpark['Longitude'] = lng
                except (ValueError, TypeError):
                    carpark['Latitude'] = None
                    carpark['Longitude'] = None
    
    def save_to_local(self, data: List[Dict], filename: Optional[str] = None) -> str:
        """
        Save data to local file
        
        Args:
            data (List[Dict]): Data to save
            filename (Optional[str]): Filename, auto-generated if not provided
            
        Returns:
            str: Path to the saved file
            
        Raises:
            IOError: If saving fails
        """
        if not data:
            self.logger.warning("No data to save")
            return ""
        
        if filename is None:
            filename = f"carpark_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = os.path.join(self.data_dir, filename)
        
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            self.logger.info(f"Data saved to: {filepath}")
            return filepath
        except Exception as e:
            error_msg = f"Error saving data: {str(e)}"
            self.logger.error(error_msg)
            raise IOError(error_msg)
    
    def to_dataframe(self, data: List[Dict]) -> 'pd.DataFrame':
        """
        Convert data to Pandas DataFrame
        
        Args:
            data (List[Dict]): List of carpark data
            
        Returns:
            pd.DataFrame: DataFrame containing carpark data
        """
        try:
            import pandas as pd
            df = pd.DataFrame(data)
            self.logger.info(f"Successfully converted to DataFrame, shape: {df.shape}")
            return df
        except ImportError:
            self.logger.warning("Pandas not installed, cannot convert to DataFrame")
            raise ImportError("Please install pandas: pip install pandas")

    def send_to_kafka(self, data: List[Dict], topic: str = "carpark-availability") -> int:
        """
        Send data to Kafka topic
        
        Args:
            data (List[Dict]): Data to send
            topic (str): Kafka topic name
            
        Returns:
            int: Number of records sent
            
        Raises:
            RuntimeError: If sending to Kafka fails
        """
        if not data:
            self.logger.warning("No data to send to Kafka")
            return 0
        
        try:
            # Create Kafka producer
            producer = KafkaProducer(
                bootstrap_servers=['localhost:9092'],
                value_serializer=lambda x: json.dumps(x).encode('utf-8')
            )
            
            # Send each record individually
            for record in data:
                producer.send(topic, value=record)
            
            # Flush to ensure all messages are sent
            producer.flush()
            
            # Close producer connection
            producer.close()
            
            self.logger.info(f"Successfully sent {len(data)} records to Kafka topic '{topic}'")
            return len(data)
            
        except Exception as e:
            error_msg = f"Failed to send data to Kafka: {str(e)}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)

def main():
    """Main function to retrieve and save carpark data"""
    try:
        # Create API handler
        api_handler = LTAApiHandler()
        
        # Get carpark data
        carpark_data = api_handler.get_carpark_availability()
        
        # Save data locally
        if carpark_data:
            api_handler.save_to_local(carpark_data)
            
            # Send data to kafka
            try:
                api_handler.send_to_kafka(carpark_data)
                print(f"Successfully processed, saved, and sent {len(carpark_data)} records to Kafka")
            except Exception as e:
                 print(f"Saved data locally but failed to send to Kafka: {str(e)}")
        else:
            print("No data received")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)