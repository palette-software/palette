# Build package in Docker container

There are two shell scripts to automate the deb package creation locally using a Docker container.

The required steps are:

- In host machine
    1. Preferably set to current directory to the project root
    1. Set the `PALETTE_VERSION` and `CONTROLLER_VERSION` variables in `docker/package/build_package.sh`
    1. Run
        ```bash
        docker/package/build_and_start_container.sh
        ```
- In Docker container
    1. Run
        ```bash
        docker/package/build_package.sh
        ```
    1. Copy the created zip file `palette-x.x.x.zip` to `/project_root`. Eg.:
        ```bash
        cp palette-2.3.4.zip /project_root
        ```

# Test the new package

You may install the `controller` and `palette` packages in a Docker container

1. Start Docker container exposing ports `443` and `888`. Eg.:
    ```bash
    docker run -h center -it -p 443:443 -p 888:888 -v $(pwd):/project_root ubuntu:14.04
    ```
1. Copy file `palette-x.x.x.zip` to a Docker container
1. Unzip it
1. Set folder as local apt repository. Eg. if you unzipped it to `/root` add the following line to the apt source.list:
    ```
    deb file:///root/dpkg/apt stable non-free
    ```
1. Install packages
    ```bash
    apt get install -y palette controller
    ```
