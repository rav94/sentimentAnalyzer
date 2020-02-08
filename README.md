# Audio Sentiment Analyzer

Audio Sentiment Analyzer with AWS Transcribe/ Comprehend - Exposed as a Flask REST API. Exposed API will take an audio file path from S3 as input and output the sentiment of the audio

## Installation

1 - Create a virtual environment with Python3

    virtualenv --no-site-packages -p /usr/local/bin/python3  env

2 - Install FLask/ Boto3

    sudo env/bin/pip3.7 install flask

    sudo env/bin/pip3.7 install boto3

3 - Run app

    source env/bin/activate

    sudo python main.py

4 - Docker-based deployment

    Pending...

## Inspired By

[Article](https://towardsdatascience.com/analyzing-historical-speeches-using-amazon-transcribe-and-comprehend-636f39a0726a)

## License

[MIT](https://choosealicense.com/licenses/mit/)
