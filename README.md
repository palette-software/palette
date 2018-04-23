# Palette Center

[![Build Status](https://travis-ci.org/palette-software/palette.svg?branch=master)](https://travis-ci.org/palette-software/palette)

# Open ports on firewall
Make sure that the following ports are allowed both for inbound and outbound connections by your firewall:
* 22 (SSH)
* 80, 443 (HTTP, HTTPS)
* 888 (Agent)
* 5432 (PostgreSql)
# Red Hat / CentOS 7

## SELinux

In order to enable the webapp to communicate with the other components (controller, database) the SELinux settings should be changed:

```
$ setsebool -P httpd_can_network_connect on
```

## Download the packages

The latest version can be downloaded from the [GitHub Releases](https://github.com/palette-software/palette/releases) page or can be built locally.

## Install

```
$ sudo yum install -y akiri.framework-*.rpm palette-center-*.rpm
```

# Ubuntu 14.04

Please NOTE: Starting from version 3.0.x installing Palette Center on Ubuntu 14.04 is not supported.

### Make sure Palette APT repository is enabled

```
$ sudo vi /etc/apt/sources.list.d/palette.center.list
deb http://palette-rpm.brilliant-data.net/ubuntu/ stable non-free
```
or
```
$ echo "deb http://palette-rpm.brilliant-data.net/ubuntu/ stable non-free" | sudo tee /etc/apt/sources.list.d/palette.center.list
```

### Install

To install all Palette Center server side components just execute the following:

`sudo apt-get install -y --force-yes palette controller`

Make sure that there is no error in the output of the `apt-get` command above.

# Configuration

Visiting the Palette Center server in a browser for the first time loads the setup page.

## Tableau Server URL

Please make sure you enter the Tableau Server URL in the format http://tableau.server.address
Please NOTE the `http` protocol, use it even if you access your Tableau on `https.`

## Palette License Key

This *must* be the same one which was used at the setup of the [agent](https://github.com/palette-software/agent).
The license key can be any valid generated [GUID](https://en.wikipedia.org/wiki/Universally_unique_identifier).

## Alerting

### Thresholds

The Alerting Configuration is available under the `Alerting` menu item of the Palette Center Webapp UI (https://<SERVER_ADDRESS>/alerts).

There are two threshold levels for alerting (`Warning` and `Error`) in five categories (`Storage`, `CPU`, `Workbook`, `Process CPU` and `Process Memory`).

### Emails

Sending of the alerting emails can be enabled under the `General Configuration` section (Gear icon > General Configuration).

Please consult the [Troubleshooting Guide](https://github.com/palette-software/palette/blob/master/TROUBLESHOOTING.md#alerting-email-is-not-sent-not-even-to-spam) if the emails are not sent.

# Troubleshooting

## Guide
Please visit the separate [Troubleshooting guide](TROUBLESHOOTING.md) for additional information.

## Configuration

The configuration files are located at:
* controller: `/etc/controller.ini`
* palette-webapp: `/etc/httpd/conf.d/palette*`

## Log file locations
Here are the log file locations on the Palette Center Server:
* controller: `/var/log/palette/controller.log*`
* palette-webapp: `/var/log/httpd/*.log`

# Local dev environment

1. Create a docker image and a docker container. Follow the setps in docker/README.md
2. Get third party dependencies


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
