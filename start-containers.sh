#!/bin/sh

set -e

docker-compose up -d

# Find the ephemeral ports the containers use, and put them
# into credentials.py
./generate_credentials.sh ports \
        `docker-compose port uf-web 8061 | awk -F: '{print $2}'` \
        `docker-compose port uf-server 8069 | awk -F: '{print $2}'`

docker-compose run uf-server /opt/unifield/server/bin/wait-postgres-start db

echo "containers started"
exit 0
