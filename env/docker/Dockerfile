FROM python:3.11-alpine

# Upgrade PIP
RUN python3 -m pip install --upgrade pip

# Debug programs
RUN apk add --no-cache iputils-ping
RUN apk add --no-cache git

# Set the working directory
WORKDIR /gateway

# micrOS install via pip
RUN python3 -m pip install micrOSDevToolKit==1.59.4

# Change the working directory to the scripts directory
WORKDIR /gateway/micrOS

EXPOSE 5000

# Run start command
# Search and start gateway and start simulator (beta)
#ENTRYPOINT devToolKit.py -s -gw -sim
# Search and start gateway
ENTRYPOINT devToolKit.py --light -s -gw

