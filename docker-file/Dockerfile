FROM python:3.7.6

USER root
RUN \
    python3 -m pip install pip && \
    pip3 install flask && \
    pip3 install boto3

COPY PropertyReader.py SentimentAnalyzer.py main.py start.sh /root/

WORKDIR /root

EXPOSE 5000

ENTRYPOINT ["./start.sh"]
