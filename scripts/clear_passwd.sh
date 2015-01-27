#!/bin/bash
# script to drop tables from postgres

psql -U palette -d paldb -h localhost << EOF
UPDATE users SET hashed_password = NULL WHERE userid = 0;
EOF
