#!/bin/sh

# Origin: https://docs.docker.com/engine/reference/builder/#exec-form-entrypoint-example

# Note: I've written this using sh so it works in the busybox container too

# USE the trap if you need to also do manual cleanup after the service is stopped,
#     or need to start multiple services in the one container
trap "echo TRAPed signal" HUP INT QUIT TERM

apt-get install -y --force-yes palette controller
service postgresql start
service apache2 start
service controller start

echo "[hit enter key to exit] or run 'docker stop <container>'"
read IGNORE_INPUT

# stop service and clean up here
echo "stopping container"
service controller stop
service apache2 stop
service postgresql stop

echo "exited $0"
