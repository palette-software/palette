#!/bin/bash
# script to drop tables from postgres

psql -U palette -d paldb -h localhost << EOF
UPDATE domain SET expiration_time = NOW() + INTERVAL '14 days';
UPDATE domain SET contact_time = NOW();
UPDATE domain SET trial = TRUE;
EOF
