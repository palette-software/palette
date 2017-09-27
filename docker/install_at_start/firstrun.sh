#!/bin/bash

HOST_VOLUME_PATH_ROOT="/var/lib/palette-center-docker"
DOCKER_IMAGE="palette-center-image"

docker run --detach --tty \
    --restart on-failure \
    --publish "443:443" \
    --publish "888:888" \
    --publish "5432:5432" \
    --publish-all \
    --hostname palette-center \
    --name palette-center \
    --volume ${HOST_VOLUME_PATH_ROOT}/log/palette:/var/log/palette \
    --volume ${HOST_VOLUME_PATH_ROOT}/log/apache2:/var/log/apache2 \
    --volume ${HOST_VOLUME_PATH_ROOT}/log/postgresql:/var/log/postgresql \
    --volume ${HOST_VOLUME_PATH_ROOT}/lib/postgresql:/var/lib/postgresql/9.3/main \
    --volume ${HOST_VOLUME_PATH_ROOT}/etc/postgresql:/etc/postgresql \
    ${DOCKER_IMAGE}
