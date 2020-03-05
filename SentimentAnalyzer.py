import os
import boto3
import time
import uuid
import urllib.request
from datetime import datetime
from PropertyReader import PropertyReader

class SentimentAnalyzer(object):
    def __init__(self, parsed_audio_file_url):
        self.parsed_audio_file_url = parsed_audio_file_url

    env_props = PropertyReader().read_properties_file()

    def _create_aws_client(self, props):
        
        s3_client = boto3.client(
            's3',
            aws_access_key_id=props.get('aws_access_id'),
            aws_secret_access_key=props.get('aws_access_key'),
            aws_region=props.get('aws_region')
        )

        transcribe_client = boto3.client(
            'transcribe',
            aws_access_key_id=props.get('aws_access_id'),
            aws_secret_access_key=props.get('aws_access_key'),
            aws_region=props.get('aws_region')
        )

        comprehend_client = boto3.client(
            'comprehend',
            aws_access_key_id=props.get('aws_access_id'),
            aws_secret_access_key=props.get('aws_access_key'),
            aws_region=props.get('aws_region')
        )

        return s3_client, transcribe_client, comprehend_client

    def _upload_audio(self, s3_client, props):

        #File served in URL pre-processing logic
        full_file_name = datetime.now() + ".mp3";
        full_file_path = os.path.join(props.get('local_file_path'), full_file_path)
        retrieved_file_path = urllib.request.urlretrieve(self.parsed_audio_file_url, full_file_path)

        #Uploading to S3 AWS logic
        bucket_key = full_file_name #Bucket key is generated as current timestamp
        bucket_name = props.get('aws_audio_log_bucket')
        s3_client.create_bucket(Bucket=bucket_name)
        s3_client.upload_file(self.audio_file_path,bucket_name,bucket_key)
        
        return bucket_key, bucket_name

    def _start_transcription(self, transcribe_client, props, bucket_key, wait_process=True):
        
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

    def _get_text_from_json(self, s3_client, bucket, bucket_key):

        object = s3_client.get_object(Bucket=bucket, Key=bucket_key)
        serializedObject = object['Body'].read()
        data = json.loads(serializedObject)
        return data.get('results').get('transcripts')[0].get('transcript')

    def _start_comprehend_job(self, comprehend_client, props, text):
        """
        Executes sentiment analysis of a text using Amazon Comprehend.
        The text can be larger than 5000 bytes (one limitation for each job), as 
        the function will split it into multiple processes and return a 
        averaged value for each sentiment.
        
        Parameter
        - text (str): The text to be analyzed
        
        Return
        - final_dict (dict): Dictionary with the percentage of each one of the 4 
        sentiments evaluated on Amazon Comprehend model (positive, negative, 
        neutral, mixed)
        """
        list_parts = []
        text_for_analysis = ''
        
        for sentence in text.split('.'):
            current_text = text_for_analysis + f'{sentence}.'

            if len(current_text.encode('utf-8')) > 5000:
                list_parts.append([len(text_for_analysis), text_for_analysis])
                text_for_analysis = f'{sentence}.'

            else:
                text_for_analysis += f'{sentence}.'

        list_parts.append([len(text_for_analysis), text_for_analysis])
        dict_comprehend = {}

        for t_parts in list_parts:
            sentimentData = comprehend_client.detect_sentiment(Text=t_parts[1], LanguageCode='en')
            
            dict_comprehend[t_parts[0]] = sentimentData
            dict_comprehend[t_parts[0]]['ratio'] = t_parts[0]/float(len(text))

        final_dict = {'Positive':0, 'Negative':0, 'Neutral':0, 'Mixed':0}
        list_sentiments = ['Positive', 'Negative', 'Neutral', 'Mixed']

        for sentiment in list_sentiments:
            for key, value in dict_comprehend.items():
                final_dict[sentiment] += value.get('SentimentScore').get(sentiment) * value.get('ratio')
        
        return final_dict

    def sentiment_analyze_invoke(self):
        s3_client, transcribe_client, comprehend_client = self._create_aws_client(env_props)

        audio_bucket_key, audio_bucket_name = self._upload_audio(s3_client, env_props)

        if (audio_bucket_key):
            return "Addition Bucket Key" + audio_bucket_key  
        else:
            return "Error"

    
    



