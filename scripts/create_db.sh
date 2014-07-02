#!/bin/bash
# script to create db and user for palette

# to run it you must first
# sudo passwd postgres
# (set the password)
# 
# Once the user postgres has the right password you need to run this script
# sudo postgres create_db.sh
#
psql -U postgres -h localhost << EOF
CREATE USER palette WITH PASSWORD 'palpass';
CREATE DATABASE paldb;
GRANT ALL PRIVILEGES ON DATABASE paldb to palette;
EOF
