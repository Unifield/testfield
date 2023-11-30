#!/bin/bash

sudo systemctl stop $USER-server
sudo systemctl stop $USER-psql
sudo systemctl stop $USER-web

echo "refresh dbs ...."
rm -fr /home/$USER/psql-data
cp -a /home/$USER/psql-data-template /home/$USER/psql-data
printf -- "-%ss" $(( $(date  "+%s") - $(date -d "2016-05-25" "+%s") )) > /home/$USER/faketime

sudo systemctl start $USER-psql
sudo systemctl start $USER-server
sudo systemctl start $USER-web
sleep 5
echo "done"
