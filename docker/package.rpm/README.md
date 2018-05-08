# Build package in Docker container

There is a shell script to automate the RPM package creation using a Docker container.

The required steps are on the host machine
1. Preferably set to current directory to the project root
1. Set the `PALETTE_VERSION` and `CONTROLLER_VERSION` environment variables in `x.x.x` format.
1. Run
    ```bash
    docker/package/build_and_start_container.sh
    ```

This will build and copy the RPM packages under the `palette-x.x.x` folder in the project root folder.

# Test the new package

You may install the `controller` and `webapp` packages in a Docker container

1. Start Docker container exposing port `443`. Eg.:
    ```bash
    docker run -h center -it -p 443:443 -v $(pwd):/project_root centos:7
    ```
1. Copy the RPM packages to the Docker container
1. Install packages
    ```bash
    sudo yum install -y akiri.framework-*.rpm palette-center-*.rpm
    ```
