Sentiment Analyzer for Call Centers

Exposed API will take an audio fiel path from S3 as input and output the sentiment of the audio

Deployment Steps

1 - Create virtual environemt with Python3
    virtualenv --no-site-packages -p /usr/local/bin/python3  env

2 - Install FLask/ Boto3
    sudo env/bin/pip3.7 install flask
    sudo env/bin/pip3.7 install boto3

3 - Run app
    source env/bin/activate
    sudo python main.py
