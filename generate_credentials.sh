#!/usr/bin/env bash

rm credentials.py 2> /dev/null

. config.sh

if [ "$1" = sandbox ]; then
	if [ -z "$2" ]; then
		echo "usage: $0 sandbox database-prefix"
		exit 1
	fi
	WEB_PORT=8004
	XMLRPC_PORT=8005
	SERVER_HOST=uf5.unifield.org
	DBPREFIX=$2
fi

docker=False
if [ "$1" = ports ]; then
	WEB_PORT=$2
	XMLRPC_PORT=$3
	docker=True
fi

echo """#encoding=utf-8

SRV_ADDRESS = '$SERVER_HOST'

# Configuration variables 
XMLRPC_PORT = $XMLRPC_PORT
HTTP_PORT = $WEB_PORT
HTTP_URL_SERVER = 'http://%s:%d' % (SRV_ADDRESS, HTTP_PORT)

# Configuration variable to generate input files / Restore dumps
DB_ADDRESS = '$DBADDR'
DB_USERNAME = '$DBUSERNAME'
DB_PASSWORD = '$DBPASSWORD'
DB_PREFIX = '$DBPREFIX'

UNIFIELD_ADMIN = '$UNIFIELDADMIN'
UNIFIELD_PASSWORD = '$UNIFIELDPASSWORD'

SERVER_HWID = '$SERVER_HWID'
USING_DOCKER = $docker
""" > credentials.py

echo """set COUNT=2
python runtests.py %*
pause
""" > runtests.bat

