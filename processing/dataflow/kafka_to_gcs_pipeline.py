#!/usr/bin/env python

import argparse
import json
import logging
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, StandardOptions, GoogleCloudOptions, SetupOptions
from apache_beam.io.gcp.gcsio import GcsIO
from apache_beam.transforms.window import FixedWindows
import datetime

# Import the correct Kafka IO module
from apache_beam.io.external.kafka import ReadFromKafka

class EnrichCarpark(beam.DoFn):
    """Enriches carpark data with processing metadata"""
    def process(self, element, timestamp=beam.DoFn.TimestampParam):
        try:
            # Parse JSON if it's a string
            if isinstance(element, bytes):
                element = element.decode('utf-8')
            if isinstance(element, str):
                element = json.loads(element)
            
            # Add processing timestamp
            element['processing_time'] = datetime.datetime.now().isoformat()
            # Add event timestamp if available
            if timestamp:
                element['event_timestamp'] = timestamp.to_utc_datetime().isoformat()
                
            return [element]
        except Exception as e:
            logging.error(f"Error processing element: {e}")
            return []

class FormatOutput(beam.DoFn):
    """Format data as JSON string for output"""
    def process(self, element):
        try:
            return [json.dumps(element)]
        except Exception as e:
            logging.error(f"Error formatting output: {e}")
            return []

def run(argv=None):
    """Main entry point"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--kafka_bootstrap_servers',
        default='localhost:9092',
        help='Kafka bootstrap servers')
    parser.add_argument(
        '--kafka_topic',
        default='carpark-availability',
        help='Kafka topic to read from')
    parser.add_argument(
        '--output_path',
        required=True,
        help='GCS output path, e.g., gs://bucket-name/carpark-data/')
    parser.add_argument(
        '--window_size',
        default=60,
        type=int,
        help='Window size in seconds')
    
    # Parse command line arguments
    known_args, pipeline_args = parser.parse_known_args(argv)
    
    # Set up the pipeline options
    pipeline_options = PipelineOptions(pipeline_args)
    pipeline_options.view_as(SetupOptions).save_main_session = True
    pipeline_options.view_as(StandardOptions).streaming = True
    
    # Run the pipeline
    with beam.Pipeline(options=pipeline_options) as p:
        (p 
         # 1. Read from Kafka 
         | 'ReadFromKafka' >> ReadFromKafka(
             consumer_config={
                 'bootstrap.servers': known_args.kafka_bootstrap_servers,
                 'auto.offset.reset': 'latest',
                 'group.id': 'carpark-dataflow-consumer'
             },
             topics=[known_args.kafka_topic])
         
         # 2. Parse JSON
         | 'ParseJSON' >> beam.Map(lambda record: json.loads(record.decode('utf-8') if isinstance(record, bytes) else record))
         
         # 3. Enrich data
         | 'EnrichData' >> beam.ParDo(EnrichCarpark())
         
         # 4. Fixed windows (e.g., 1 minute)
         | 'Window' >> beam.WindowInto(FixedWindows(known_args.window_size))
         
         # 5. Format output
         | 'FormatOutput' >> beam.ParDo(FormatOutput())
         
         # 6. Write to GCS with timestamp in filename
         | 'WriteToGCS' >> beam.io.WriteToText(
             file_path_prefix=f"{known_args.output_path}/carpark-",
             file_name_suffix='.json',
             append_trailing_newlines=True,
             num_shards=1,
             window_into_shards=True,
             shard_name_template='-W-P-SS-of-NN-')
        )

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    run()