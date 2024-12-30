FROM python:3.11-alpine

# Upgrade PIP
RUN python3 -m pip install --upgrade pip

# Install debugging tools
RUN apk add --no-cache iputils-ping git

# Set the working directory
WORKDIR /gateway

# Install micrOS
RUN python3 -m pip install micrOSDevToolKit==2.8.7

# Change to the micrOS directory
WORKDIR /gateway/micrOS

# Expose port
EXPOSE 5000

# Start the gateway
ENTRYPOINT ["devToolKit.py", "--light", "-s", "-gw"]
