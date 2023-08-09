#!/bin/bash
#set -x

VERSION=$1
if [ "$VERSION" = "" ]
then
    echo -e "Missing version number"
    exit 1
fi

IMAGE="bxnxm/micros-gateway:${VERSION}"

echo -e "[CREATE IMAGE] docker build --no-cache -t ${IMAGE}"
docker build --no-cache -t "${IMAGE}" .

echo -e "[RUN IMAGE] docker run"
docker run --name micros-gateway -p 5000:5000 -e GATEWAYIP="10.0.1.1" -d "${IMAGE}"

echo -n "DO YOU WANT TO PUBLISH THE IMAGE ${IMAGE} (Y/n): "
read answer

if [[ "$answer" == "Y" ]]; then
    echo -e "\t[PUBLISH CONTAINER] docker push "${IMAGE}""
    docker push "${IMAGE}"
else
    echo -e "\t[PUBLISH CONTAINER] SKIP docker push "${IMAGE}""
fi

exit 0
