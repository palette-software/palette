# Troubleshooting

This guide can address issues which might occur during the installation or operation of the Palette Center service.

## Install on Red Hat 7 - Dependencies

### Issue

During the package installation an error message similar to the following is displayed:

```
Error: Package: palette-center-webapp-3.0.1-1.noarch (/palette-center-webapp-3.0.1-1.noarch)
           Requires: python-sphinx
Error: Package: akiri.framework-0.5.7-1.noarch (/akiri.framework-0.5.7-1.noarch)
           Requires: python-paste-script
Error: Package: palette-center-controller-3.0.1-1.noarch (/palette-center-controller-3.0.1-1.noarch)
           Requires: python-sphinx
Error: Package: akiri.framework-0.5.7-1.noarch (/akiri.framework-0.5.7-1.noarch)
           Requires: python-webob
Error: Package: palette-center-webapp-3.0.1-1.noarch (/palette-center-webapp-3.0.1-1.noarch)
           Requires: python-webob
Error: Package: akiri.framework-0.5.7-1.noarch (/akiri.framework-0.5.7-1.noarch)
           Requires: python-paste-deploy
Error: Package: palette-center-controller-3.0.1-1.noarch (/palette-center-controller-3.0.1-1.noarch)
           Requires: python-crypto
```

### Resolution

You can get these packages from a CentOS 7 installation.

## Install on Red Hat 7 - POSTIN failure

### Issue

During the package installation an error message similar to the following is displayed:

```
chown: invalid user: 'apache:apache'
warning: %post(palette-center-controller-3.0.1-1.noarch) scriptlet failed, exit status 1
Non-fatal POSTIN scriptlet failure in rpm package palette-center-controller-3.0.1-1.noarch
```

### Resolution

Execute the following commands to finish the setup of the package:

```
rm /var/palette/.aes
systemctl enable controller
systemctl start controller
systemctl start httpd
```

## Alerting email is not sent (not even to SPAM)

### Issue

The Palette Center service does not send email alerts.

### Resolution 1

Visit the Palette Center in a browser to access its UI and check whether the email alerting is enabled at:

Gear icon > General Configuration > Email Alerts

### Resolution 2

Check whether the email is set for the users.

```
$ psql -U palette -d paldb -c "select userid,name,email from users;"
```

Set email address for the Palette Admin user

```
$ psql -U palette -d paldb -c "update users set email='EMAIL_ADDRESS@COMPANY' where userid=0 and name='palette';"
```

### Resolution 3

Check the `/var/log/maillog` file whether it has an entry similar to the following:

```
Apr 13 18:16:09 ip-172-32-1-150 postfix/cleanup[2445]: 0411597CA2: message-id=<20180413181609.0411597CA2@outgoing.alerting.com>
Apr 13 18:16:09 ip-172-32-1-150 postfix/qmgr[2283]: 0411597CA2: from=<robot@alerting.com>, size=1006, nrcpt=1 (queue active)
Apr 13 18:16:09 ip-172-32-1-150 postfix/smtpd[2439]: disconnect from localhost[::1]
Apr 13 18:16:09 ip-172-32-1-150 postfix/smtp[2447]: connect to aspmx.l.google.com[2a00:1450:400b:c03::1b]:25: Network is unreachable
Apr 13 18:16:09 ip-172-32-1-150 postfix/smtp[2447]: 0411597CA2: to=<operations@company.com>, relay=aspmx.l.google.com[209.85.203.27]:25, delay=0.35, delays=0.03/0.03/0.18/0.1, dsn=2.0.0, status=sent (250 2.0.0 OK 1523643369 d35si2811407ede.363 - gsmtp)
Apr 13 18:16:09 ip-172-32-1-150 postfix/qmgr[2283]: 0411597CA2: removed
```

If so uncomment the following lines in `/etc/postfix/main.cf`:

```
# smtpd_tls_cert_file=/etc/ssl/certs/ssl-cert-snakeoil.pem
# smtpd_tls_key_file=/etc/ssl/private/ssl-cert-snakeoil.key
# smtpd_use_tls=no
```

## In the browser an Internal Server Error is displayed

### Issue 1

An error message similar to the following is displayed in `/var/log/httpd/error_log`:

```
[Fri Apr 13 12:48:44.074352 2018] [:error] [pid 1895] [client 192.168.0.1:49653] mod_wsgi (pid=1895): Target WSGI script '/opt/palette/application.wsgi' cannot be loaded as Python module.
[Fri Apr 13 12:48:44.074377 2018] [:error] [pid 1895] [client 192.168.0.1:49653] mod_wsgi (pid=1895): Exception occurred processing WSGI script '/opt/palette/application.wsgi'.
[Fri Apr 13 12:48:44.074397 2018] [:error] [pid 1895] [client 192.168.0.1:49653] Traceback (most recent call last):
[Fri Apr 13 12:48:44.074414 2018] [:error] [pid 1895] [client 192.168.0.1:49653]   File "/opt/palette/application.wsgi", line 47, in <module>
[Fri Apr 13 12:48:44.074487 2018] [:error] [pid 1895] [client 192.168.0.1:49653]     set_aes_key_file(AES_KEY_FILE)
[Fri Apr 13 12:48:44.074497 2018] [:error] [pid 1895] [client 192.168.0.1:49653]   File "/usr/lib/python2.7/site-packages/controller/passwd.py", line 27, in set_aes_key_file
[Fri Apr 13 12:48:44.074546 2018] [:error] [pid 1895] [client 192.168.0.1:49653]     return genaeskey()
[Fri Apr 13 12:48:44.074555 2018] [:error] [pid 1895] [client 192.168.0.1:49653]   File "/usr/lib/python2.7/site-packages/controller/passwd.py", line 34, in genaeskey
[Fri Apr 13 12:48:44.074569 2018] [:error] [pid 1895] [client 192.168.0.1:49653]     os.rename(tmp, aes_key_file)
[Fri Apr 13 12:48:44.074584 2018] [:error] [pid 1895] [client 192.168.0.1:49653] OSError: [Errno 13] Permission denied
```

### Resolution 1

Execute the following command:

```
$ rm /var/palette/.aes
```

### Issue 2

An error message similar to the following is displayed in `/var/log/httpd/error_log`:

```
[Fri Apr 13 12:49:01.324468 2018] [:error] [pid 1895] [client 192.168.0.1:49660] OperationalError: (OperationalError) could not connect to server: Permission denied, referer: https://192.168.0.2/
[Fri Apr 13 12:49:01.324473 2018] [:error] [pid 1895] [client 192.168.0.1:49660] \tIs the server running on host "localhost" (::1) and accepting, referer: https://192.168.0.2/
[Fri Apr 13 12:49:01.324476 2018] [:error] [pid 1895] [client 192.168.0.1:49660] \tTCP/IP connections on port 5432?, referer: https://192.168.0.2/
[Fri Apr 13 12:49:01.324478 2018] [:error] [pid 1895] [client 192.168.0.1:49660] could not connect to server: Permission denied, referer: https://192.168.0.2/
[Fri Apr 13 12:49:01.324481 2018] [:error] [pid 1895] [client 192.168.0.1:49660] \tIs the server running on host "localhost" (127.0.0.1) and accepting, referer: https://192.168.0.2/
[Fri Apr 13 12:49:01.324483 2018] [:error] [pid 1895] [client 192.168.0.1:49660] \tTCP/IP connections on port 5432?, referer: https://192.168.0.2/
```

### Resolution 2

In an SELinux environment enable networking for the httpd server:

```
setsebool -P httpd_can_network_connect on
```

## Cannot connect to Palette Center in browser

### Issue

The webpage of the Palette Center is not displayed. It might be the firewall which is blocking it.

### Resolution

Enable `http` and `https` on the firewall.

NOTE: you might be using a different solution but for `firewalld` execute the following commands:

```
firewall-cmd --zone=public --permanent --add-service=http
firewall-cmd --zone=public --permanent --add-service=https
firewall-cmd --zone=public --add-service=http
firewall-cmd --zone=public --add-service=https
```
