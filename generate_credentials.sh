#!/bin/bash

rm credentials.py 2> /dev/null

. config.sh

echo """#encoding=utf-8

SRV_ADDRESS = '127.0.0.1'

# Configuration variables 
NETRPC_PORT = $NETRPC_PORT
HTTP_PORT = $WEB_PORT
HTTP_URL_SERVER = 'http://%s:%d' % (SRV_ADDRESS, HTTP_PORT)

# Configuration variable to generate input files / Restore dumps
DB_ADDRESS = '$DBADDR'
DB_PORT = 5432
DB_NAME = '$1'
DB_USERNAME = '$DBUSERNAME'
DB_PASSWORD = '$DBPASSWORD'

UNIFIELD_ADMIN = '$UNIFIELDADMIN'
UNIFIELD_PASSWORD = '$UNIFIELDPASSWORD'

""" > credentials.py


