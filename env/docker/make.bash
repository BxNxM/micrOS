#!/bin/bash
set -x

echo -e "[CREATE IMAGE] docker build"
docker build --no-cache -t micros-gateway:1.0 .

echo -e "[RUN IMAGE] docker run"
docker run --name micros-gateway -p 5000:5000 -e GATEWAYIP="10.0.1.1" -d micros-gateway:1.0

