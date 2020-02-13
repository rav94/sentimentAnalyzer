import os
import boto3
import time
import uuid
from datetime import datetime
from PropertyReader import PropertyReader

class SentimentAnalyzer(object):
    def __init__(self, audio_file_path):
        self.audio_file_path = audio_file_path

    env_props = PropertyReader().read_properties_file()

    def _create_aws_client(self, props):
        
        s3_client = boto3.client(
            's3',
            aws_access_key_id=props.get('aws_access_id'),
            aws_secret_access_key=props.get('aws_access_key'),
            aws_session_token=props.get('aws_session_id'),
            aws_region=props.get('aws_region')
        )

        transcribe_client = boto3.client(
            'transcribe',
            aws_access_key_id=props.get('aws_access_id'),
            aws_secret_access_key=props.get('aws_access_key'),
            aws_session_token=props.get('aws_session_id'),
            aws_region=props.get('aws_region')
        )

        comprehend_client = boto3.client(
            'comprehend',
            aws_access_key_id=props.get('aws_access_id'),
            aws_secret_access_key=props.get('aws_access_key'),
            aws_session_token=props.get('aws_session_id'),
            aws_region=props.get('aws_region')
        )

        return s3_client, transcribe_client, comprehend_client

    def _upload_audio(self, s3_client, props):
        bucket_key=datetime.now() #Bucket key is generated as current timestamp
        bucket_name=props.get('aws_audio_log_bucket')
        s3_client.create_bucket(Bucket=bucket_name)
        s3_client.upload_file(self.audio_file_path,bucket_name,bucket_key)
        return bucket_key, bucket_name

    def _start_transcription(self, bucket_key, transcribe_client, props, wait_process=True):
        
        transcribe_job_name='transcribe-' + str(uuid.uuid4) #Unique transcribe job name 
        audio_file_url='http://s3-' + props.get('aws_regiion') + '.amazonaws.com/' + props.get('aws_audio_log_bucket') + '/' + bucket_key
        
        transcribe_client.start_transcription_job(
            TranscriptionJobName=transcribe_job_name,
            Media={'MediaFileUri': audio_file_url},
            MediaFormat='mp3',
            LanguageCode='en-US',
            OutputBucketName=props.get('aws_transcribe_bucket'))

        if wait_process:
            while True:
                status = transcribe_client.get_transcription_job(TranscriptionJobName=transcribe_job_name)
                if status['TranscriptionJob']['TranscriptionJobStatus'] in ['COMPLETED', 'FAILED']:
                    break
                print("Not ready yet...")
                time.sleep(20)

            print('Transcription finished')
            return status

    
    
    



