# Palette Center server for dev purposes

### Build the docker image ###
`docker build . -t palette-center`

### Run a container with the built image ###

In the repository root call the run.sh as that sets up port redirection of 9443 to 443 and mounts repository folders in the container so that local modifications can be check immediately.

`app/run.sh`

### In the container start postgresql and restart Palette Center components ###

`
service postgresql start
service apache2 start
service controller start

sudo su - postgres

psql paldb -f /home/ubuntu/domain.sql
psql paldb -f /home/ubuntu/environment.sql
psql paldb -f /home/ubuntu/roles.sql
psql paldb -f /home/ubuntu/users.sql

exit

sudo service apache2 reload
sudo service controller restart
`

*NOTE* These steps should go to a startup shell script later on...
