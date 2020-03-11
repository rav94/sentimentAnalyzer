import os
import boto3
import time
import uuid
import json
import urllib.request
from datetime import datetime
from PropertyReader import PropertyReader
from botocore.exceptions import ClientError

class SentimentAnalyzer(object):
    def __init__(self, parsed_audio_file_url):
        self.parsed_audio_file_url = parsed_audio_file_url

    def _upload_audio(self):

        env_props = PropertyReader().read_properties_file()

        s3_client = boto3.client(
            's3',
            aws_access_key_id=env_props.get('aws_access_id'),
            aws_secret_access_key=env_props.get('aws_access_key'),
            region_name=env_props.get('aws_region')
        )

        #File served in URL pre-processing logic
        full_file_name = str(datetime.now()) + ".mp3";
        full_file_path = os.path.join(env_props.get('local_file_path'), full_file_name)
        retrieved_file_path = urllib.request.urlretrieve(self.parsed_audio_file_url, full_file_path)

        try:
            #Uploading to S3 AWS logic
            bucket_key = full_file_name #Bucket key is generated as current timestamp
            bucket_name = env_props.get('aws_audio_log_bucket')
            s3_client.create_bucket(Bucket=bucket_name)
            s3_client.upload_file(full_file_path,bucket_name,bucket_key)
            
            #Removing processed file
            if os.path.isfile(full_file_path):
                os.remove(full_file_path)

            success_result = dict();
            success_result['status'] = True
            success_result['bucket_key'] = bucket_key
            success_result['bucket_name'] = bucket_name
            
            return success_result

        except ClientError as e:
            print("Unexpected Error Occurred: %s" % e)

            error_result = dict();
            error_result['status'] = False        

            return error_result

    def _start_transcription(self, bucket_key, wait_process=True):

        env_props = PropertyReader().read_properties_file()

        transcribe_client = boto3.client(
            'transcribe',
            aws_access_key_id=env_props.get('aws_access_id'),
            aws_secret_access_key=env_props.get('aws_access_key'),
            region_name=env_props.get('aws_region')
        )
        
        transcribe_job_name='transcribe-' + str(uuid.uuid4()) #Unique transcribe job name 
        audio_file_url='http://s3-' + env_props.get('aws_region') + '.amazonaws.com/' + env_props.get('aws_audio_log_bucket') + '/' + bucket_key
        
        try:
            transcribe_client.start_transcription_job(
                TranscriptionJobName=transcribe_job_name,
                Media={'MediaFileUri': audio_file_url},
                MediaFormat='mp3',
                LanguageCode='en-US',
                OutputBucketName=env_props.get('aws_transcribe_bucket'))

            if wait_process:
                while True:
                    status = transcribe_client.get_transcription_job(TranscriptionJobName=transcribe_job_name)
                    if status['TranscriptionJob']['TranscriptionJobStatus'] in ['COMPLETED', 'FAILED']:
                        break
                    print("Not ready yet...")
                    time.sleep(20)

                print('Transcription finished')
               
                transcribe_bucket_name_key = transcribe_job_name + '.json'

                sucess_result = 'COMPLETED'

                return sucess_result, transcribe_bucket_name_key

        except ClientError as e:
            print("Unexpected Error Occurred: %s" % e)

            error_result = 'FAILEDBYEXCEPTION'
            return error_result, None

    def _get_text_from_json(self, transcribe_saved_bucket_key):

        env_props = PropertyReader().read_properties_file()

        s3_client = boto3.client(
            's3',
            aws_access_key_id=env_props.get('aws_access_id'),
            aws_secret_access_key=env_props.get('aws_access_key'),
            region_name=env_props.get('aws_region')
        )

        object = s3_client.get_object(Bucket=env_props.get('aws_transcribe_bucket'), Key=transcribe_saved_bucket_key)
        serializedObject = object['Body'].read()
        data = json.loads(serializedObject)
        return data.get('results').get('transcripts')[0].get('transcript')

    def _start_comprehend_job(self, text):
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

        env_props = PropertyReader().read_properties_file()

        comprehend_client = boto3.client(
            'comprehend',
            aws_access_key_id=env_props.get('aws_access_id'),
            aws_secret_access_key=env_props.get('aws_access_key'),
            region_name=env_props.get('aws_region')
        )

        try:
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
            
            return final_dict, None
       
        except ClientError as e:
            print("Unexpected Error Occurred: %s" % e)

            return None, True


    def sentiment_analyze_invoke(self):
        audio_upload_to_s3 = self._upload_audio()

        if (audio_upload_to_s3["status"]):
            bucket_key=audio_upload_to_s3["bucket_key"]
            bucket_name=audio_upload_to_s3["bucket_name"]

            status, transcribe_bucket_name_key = self._start_transcription(bucket_key)

            if status == 'COMPLETED':
                print('Transcribe Job Completion - SUCCESS')

                transcript_text = self._get_text_from_json(transcribe_bucket_name_key)

                sentiment_result, error = self._start_comprehend_job(transcript_text)

                if (sentiment_result):
                    print('Comprehend Job Completion - SUCCESS')

                    success_result = dict();
                    success_result['status'] = True
                    success_result['sentiment'] = sentiment_result
                    
                    return success_result
                    
                else:
                    print('Comprehend Sentiment Extraction - FAILED')

                    comprehend_error_result = dict();
                    comprehend_error_result['status'] = False
                    comprehend_error_result['error'] = 'Error in extracting sentiment from Comprehend'

                    return comprehend_error_result

            elif status == 'FAILED':
                print('Transcribe Job Completion - FAILED')

                transcribe_upload_error_result = dict();
                transcribe_upload_error_result['status'] = False
                transcribe_upload_error_result['error'] = 'Error in uploading file to Transcribe' 

                return transcribe_upload_error_result

            else:
                print('Transcribe Internal Error - FAILED')

                transcribe_internal_error_result = dict();
                transcribe_internal_error_result['status'] = False
                transcribe_internal_error_result['error'] = 'Internal Error in uploading file to Transcribe' 

                return transcribe_internal_error_result

        else:
            print('Audio File to S3 Upload - FAILED')

            s3_upload_error_result = dict();
            s3_upload_error_result['status'] = False
            s3_upload_error_result['error'] = 'Error in file uploading to S3' 

            return s3_upload_error_result

    
    



