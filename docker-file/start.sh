#!/bin/bash
cat /root/env.properties

#echo "Printing ENV"
#echo $api_context

echo "Starting the server...\n"
python3 /root/main.py
