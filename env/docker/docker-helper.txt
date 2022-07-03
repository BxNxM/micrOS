
# Create docker image
docker build -t micros/gw-docker .

# List docker image
docker images

# Start container (image id)
docker run -d -p 5000:5000 19ccd40a3985

# List all containers
docker ps -a

# Interactive "log-in" to container (container id)
docker exec -it f3a1f13e0817 /bin/bash
