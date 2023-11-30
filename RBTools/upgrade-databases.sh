#!/bin/bash


RBUSER=$USER
PGPORT=14724
XMLRPCPORT=14723
. /home/$RBUSER/unifield-venv/bin/activate


sudo systemctl stop $RBUSER-server
sudo systemctl stop $RBUSER-psql
sudo systemctl stop $RBUSER-web

cd /home/$RBUSER
cd unifield-server/
find . -name '*pyc' -exec rm -f {} \; 
bzr revert
#bzr pull lp:unifield-server
REVNO=$(bzr revno --tree)
cd ../unifield-web;
bzr revert
#bzr pull lp:unifield-web

SERVERDIR=/home/$RBUSER/unifield-server
sed -i "s/FOR UPDATE NOWAIT//g" $SERVERDIR/bin/addons/base/ir/ir_sequence.py
sed -i "s/th.join(3)/th.join()/g" $SERVERDIR/bin/addons/msf_tools/msf_tools.py
echo "88888888888888888888888888888888
66f490e4359128c556be7ea2d152e03b 2013-04-27 16:49:56" > $SERVERDIR/bin/unifield-version.txt


DBREVNO=$(cat /home/$RBUSER/psql-data-template/REVNO)

if [ "$DBREVNO" == "$REVNO" ]; then
    sudo systemctl start $RBUSER-psql
    sudo systemctl start $RBUSER-server
    sudo systemctl start $RBUSER-web
    echo "dbs up to date $DBREVNO $REVNO"
    exit 0
fi

echo -n $REVNO > /home/$RBUSER/psql-data-template/REVNO
echo "Update modules"

## -u base
rm -fr /home/$RBUSER/psql-data
cp -a /home/$RBUSER/psql-data-template /home/$RBUSER/psql-data

printf -- "-%ss" $(( $(date  "+%s") - $(date -d "2016-05-25" "+%s") )) > /home/$RBUSER/faketime
sudo systemctl start $RBUSER-psql
sleep 5

for x in `psql -h 127.0.0.1 -p $PGPORT  -td template1 -c "SELECT datname FROM pg_database WHERE pg_get_userbyid(datdba) = current_user and datname like 'TESTS_%';"`; do
    psql  -h 127.0.0.1 -p $PGPORT -d $x -c "delete from sync_client_version;"
    psql  -h 127.0.0.1 -p $PGPORT -d $x -c "delete from sync_server_version;"
    LD_PRELOAD=/usr/local/lib/faketime/libfaketime.so.1 FAKETIME_TIMESTAMP_FILE=/home/$RBUSER/faketime /home/$RBUSER/unifield-server/bin/openerp-server.py -c /home/$RBUSER/etc/openerprc -d $x -u ${1:-base} --stop-after-init
    psql  -h 127.0.0.1 -p $PGPORT -d $x -c "update sync_client_sync_server_connection set database='TESTS_SYNC_SERVER', port=${XMLRPCPORT};"
done

echo -n $REVNO > /home/$RBUSER/psql-data-template/REVNO

mv /home/$RBUSER/psql-data-template /home/$RBUSER/psql-data-template-$(date +'%Y%m%d-%H%M')
sudo systemctl stop $RBUSER-psql
sleep 5

# sync all
printf -- "-%ss" $(( $(date  "+%s") - $(date -d "2016-05-25" "+%s") )) > /home/$RBUSER/faketime
sudo systemctl start $RBUSER-server
sudo systemctl start $RBUSER-psql
sleep 5
/opt/unifield-toolbox/maintenance/synchro/sync_all.py
/opt/unifield-toolbox/maintenance/synchro/sync_all.py

for x in `psql -h 127.0.0.1 -p $PGPORT  -td template1 -c "SELECT datname FROM pg_database WHERE pg_get_userbyid(datdba) = current_user and datname like 'TESTS_%';"`; do
	psql  -h 127.0.0.1 -p $PGPORT -d $x -c "update ir_model_data set last_modification='2016-05-25 00:00:00' where last_modification is not null and last_modification>sync_date and touched is null;"
	psql  -h 127.0.0.1 -p $PGPORT -d $x -c "update product_product set active_change_date='2016-05-25 00:00:00' where active_change_date>'2016-05-25 00:00:00';"
done
sudo systemctl stop $RBUSER-server
sudo systemctl stop $RBUSER-psql
sleep 5
cp -a /home/$RBUSER/psql-data /home/$RBUSER/psql-data-template
sleep 5
sudo systemctl start $RBUSER-psql
sudo systemctl start $RBUSER-web
sudo systemctl start $RBUSER-server

