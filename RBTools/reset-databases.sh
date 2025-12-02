#!/bin/bash

MYUSER=$LOGNAME
sudo systemctl stop $MYUSER-server
sudo systemctl stop $MYUSER-psql
sudo systemctl stop $MYUSER-web

echo "refresh dbs ...."
rm -fr /home/$MYUSER/psql-data
cp -a /home/$MYUSER/psql-data-template /home/$MYUSER/psql-data
printf -- "-%ss" $(( $(date  "+%s") - $(date -d "2016-05-25" "+%s") )) > /home/$MYUSER/faketime

sudo systemctl start $MYUSER-psql
sudo systemctl start $MYUSER-server
sudo systemctl start $MYUSER-web
sleep 5
echo "done"
