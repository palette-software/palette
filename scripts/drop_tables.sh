#!/bin/bash
# script to drop tables from postgres

psql -U palette -d paldb -h localhost << EOF
drop table agent cascade;
drop table agent_info cascade;
drop table agent_volumes cascade;
drop table agent_yml cascade;
drop table backup cascade;
drop table cloud cascade;
drop table data_source_types cascade;
drop table datasources cascade;
drop table environment cascade;
drop table events cascade;
drop table extracts cascade;
drop table files cascade;
drop table metrics cascade;
drop table notifications cascade;
drop table role_permissions cascade;
drop table permissions cascade;
drop table role_roles cascade;
drop table user_roles cascade;
drop table roles cascade;
drop table users cascade;
drop table system cascade;
drop table domain cascade;
drop table apscheduler_jobs cascade;
drop table license cascade;
drop table tableau_processes cascade;
drop table firewall cascade;
drop table gcs cascade;
drop table data_connections cascade;
drop table http_request cascade;
drop table projects cascade;
drop table sites cascade;
drop table http_requests cascade;
drop table credentials cascade;
drop table cron cascade;
drop table http_control cascade;
drop table ports cascade;
drop table s3 cascade;
drop table workbooks_updates cascade;
drop table workbooks cascade;
drop table state_control cascade;
drop table event_control cascade;
drop table state cascade;
drop table status cascade;
drop table workbook_updates cascade;
drop table XID cascade;
drop table yml cascade;
EOF
