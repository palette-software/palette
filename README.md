# Palette Center

[![Build Status](https://travis-ci.org/palette-software/palette.svg?branch=master)](https://travis-ci.org/palette-software/palette)


# Local dev environment

1. Create a docker image and a docker container. Follow the setps in docker/README.md
2. Get third party dependencies:


This repository is hosting the server side codebase of the Palette Center product.

**NOTE** A valid server certificate is needed for the controller.

Packaging:
    To build the Debian packages:

        INSTALL THE DEPENDENCY:
            sudo apt-get install debhelper
            sudo apt-get install pylint python-tz python-passlib python-dateutil python-boto python-crypto
            sudo apt-get install python-mako python-webob python-pastescript python-sqlalchemy python-paste python-pastedeploy

        Install the Akiri framework:
            Download and install the latest Akiri framework. On 2015/07/15
            this could be done via:

                cd /tmp
                wget https://www.akirisolutions.com/download/framework/akiri.framework_0.5.0_all.deb
                sudo dpkg --install akiri.framework_0.5.0_all.deb

        Build the Debian packages:
            # follow the setup instructions in controller/README and app/README
            make palette && make controller

        This will create the packages:
            controller_0.1_all.deb
            palette_0.1_all.deb (the "webapp")

        You will also see other files have been created, such as
        controller_0.1.orig.tar.gz, controller_0.1.debian.tar.gz, etc.
        which you can ignore.

Configuration:
    Controller:
        - Configuration file used: /etc/controller.ini
        - Logging:
            * /var/log/palette/controller.log
        - Autostarted via /etc/init/controller.conf

    Palette (webapp):
        - Configuration file used: /etc/palette.ini
        - Logging:
            * /var/log/palette/webapp.log
            * /var/log/palette/access.log (http traffic)
        - Autostarted via /etc/init/palette.conf

To install the packages:
    gdebi controller_0.1_all.deb
    gdebi palette_0.1_all.deb

To remove the packages:
    apt-get remove controller
    apt-get remove palette

To stop or start the controller:
    # stop controller
    # start controller

To stop or start the palette webapp:
    # stop palette
    # start palette

To see if the controller or palette webapp is running:
    The controller is stopped:
        # initctl list | grep controller
        controller stop/waiting

    The palette/webapp process is running:
        # initctl list | grep palette
        palette start/running, process 4460

## To run the controller without installing the "controller" package

    sudo mkdir /var/log/palette
    sudo chown-to-whoever-will-berunning-controller /var/log/palette
    cd palette/controller/controller

## To run the webapp without installing the "palette" package

    cd palette/app
    httpserver etc/palette.ini
