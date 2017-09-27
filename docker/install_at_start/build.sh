#!/bin/bash

DOCKER_IMAGE="palette-center-image"

docker build -t ${DOCKER_IMAGE} $(dirname $0)
