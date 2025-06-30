#!/bin/bash


url="http://localhost:3000"
echo -e "OPEN GRAFANA: ${url}"
open $url

url="http://localhost:9090"
echo -e "OPEN PROMETHEUS: ${url}"
open $url

url="http://localhost:5005"
echo -e "OPEN GATEWAY: ${url}"
open $url
