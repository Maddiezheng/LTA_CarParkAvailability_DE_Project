#!/usr/bin/env python
import json
import sys
import os

# Add parent directory to Python path to import LTAApiHandler
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from extraction.api_client import LTAApiHandler

def test_api():
    """Test LTA API connection and data format"""
    print("Testing LTA CarPark Availability API...")
    
    try:
        # Create API handler
        api_handler = LTAApiHandler()
        
        # Get carpark data
        carpark_data = api_handler.get_carpark_availability()
        
        # Analyze data
        if carpark_data:
            # Print sample data
            print("\nSample data (first record):")
            print(json.dumps(carpark_data[0], indent=2))
            
            # Print total record count
            print(f"\nSuccessfully retrieved data, total records: {len(carpark_data)}")
            
            # Data field analysis
            print("\nData field analysis:")
            fields = list(carpark_data[0].keys())
            print(f"Field list: {fields}")
            
            # Print data statistics
            areas = set(item.get('Area', 'Unknown') for item in carpark_data)
            agencies = set(item.get('Agency', 'Unknown') for item in carpark_data)
            
            print(f"\nTotal areas: {len(areas)}")
            print(f"Total agencies: {len(agencies)}")
            
            if len(areas) <= 10:  # If there aren't too many areas, print them all
                print(f"Area list: {sorted(areas)}")
            
            return len(carpark_data)
        else:
            print("No data received")
            return 0
            
    except Exception as e:
        print(f"API test failed: {str(e)}")
        return 0


if __name__ == "__main__":
    record_count = test_api()
    if record_count > 0:
        print("\nAPI test successful! ")
    else:
        print("\nAPI test failed! ")