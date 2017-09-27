# Docker image with persistent data (install_at_start)

Using the `build.sh` and `firstrun.sh` scripts you can build and run a docker image which
runs the `Palette Center` software and is able to persist data between container recreations.

The required steps are:

1. Grab the required version from <https://github.com/palette-software/palette/releases>
and put in the same directory as the `Dockerfile`
1. Run `build.sh` which will download all the necessary packages within the image (Internet required)
1. If you need to move the docker image than save it with:
    ```bash
    docker save palette-center-image:latest | gzip > palette-center-image.gz
    ```
1. Copy the both `palette-center-image.gz` and `firstrun.sh` to the target machine
1. You can load the image on the target machine with:
    ```bash
    gzip -cd palette-center-image.gz | docker load
    ```
1. To persist the necessary files run the container with the `firstrun.sh` script

# Notes

- You may check the startup of the container by running the command:
    ```bash
    docker logs -f palette-center
    ```
- The location of the persisted files are set by `firstrun.sh`.
- You may start and stop the container with:
    ```bash
    docker stop palette-center
    docker start palette-center
    ```
- The container is started on daemon startup and if the container exits
- You may get a shell access with the command:
    ```bash
    docker exec -it palette-center bash
    ```
