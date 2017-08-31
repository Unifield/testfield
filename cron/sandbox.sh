#!/bin/bash

set -o errexit

if [[ $TMUX ]]
then
    echo "\$TMUX is set!" >&2
    exit 1
fi

[ -f ~/unifield-venv/bin/activate ] && . ~/unifield-venv/bin/activate


cd /home/testing/testfield_sandbox

TMPPATH=/home/testing/repo
DBDIR=/usr/lib/postgresql/9.6/bin/
ENVNAME=lightweight
NAME_RUN=sandbox
DBPORT=8014
DBUSERNAME=selenium_testing
FORCED_DATE=yes

# remove the previous environment
./scripts/stop_unifield.sh -d $TMPPATH $NAME_RUN || true
./scripts/kill_db.sh -D $TMPPATH $NAME_RUN || true

if [[ -e $TMPPATH/data-sandbox ]]
then
    rm -rf $TMPPATH/data-sandbox
fi

if [[ -e $TMPPATH/run-sandbox ]]
then
    rm -rf $TMPPATH/run-sandbox
fi

# OwnCloud won't be used anymore. Tests, instances and files will be moved directly on uf5-hw and backed up on the backup server.
#./fetch/owncloud/fetch.sh

function generate_config()
{
    cat << EOF > config.sh
#!/bin/bash

NETRPC_PORT=8006
WEB_PORT=8004
XMLRPC_PORT=8005
XMLRPCS_PORT=8007

UNIFIELDADMIN=admin
UNIFIELDPASSWORD=admin

DBPASSWORD=$DBUSERNAME
DBADDR=127.0.0.1
DBUSERNAME=$DBUSERNAME
DBPORT=$DBPORT
DBPREFIX='$1'

SERVER_HOST=127.0.0.1
SERVER_TMPDIR=$TMPPATH
SERVER_ENVNAME=$ENVNAME

DBPATH=$DBDIR
FORCED_DATE=$FORCED_DATE

HOMEREDB=\$'ZXBpc2FnYQ==\\naG9tZXJlN3pFcGljb25jZXB0MTIz'

EOF
}

# We have to run the tests and create the environment
NAME_RUN=sandbox

################################################################
# Fetch the time difference between the date we want to use to run the tests
DATEUTILS=date
if [[ $(uname) == Darwin ]]
then
    DATEUTILS=gdate
fi

BEFORE=$($DATEUTILS -d "2016-05-25" '+%s')
NOW=$($DATEUTILS '+%s')

if [[ ${FORCED_DATE} == yes ]];
then
    MINUS_IN_SECOND=$[ $NOW - $BEFORE ]
else
    MINUS_IN_SECOND=0
fi
#################################################################

SERVERBRANCH="lp:unifield-server"
WEBBRANCH="lp:unifield-web"

export PGPASSWORD=$DBPASSWORD


./scripts/fetch_unifield.sh -W "$WEBBRANCH" -S "$SERVERBRANCH" -d $TMPPATH -r $NAME_RUN

./scripts/create_db.sh -P ${DBDIR} -D $TMPPATH -s $MINUS_IN_SECOND -p $DBPORT -c $DBUSERNAME $NAME_RUN

for name in MARJUKKA SARAH TEMPO ANDRES
do
	generate_config $name

	source config.sh

	./generate_credentials.sh HQ1

	python restore.py --bak --reset-sync --reset-versions $ENVNAME

	./scripts/upgrade_unifield.sh -s $MINUS_IN_SECOND -d $TMPPATH $NAME_RUN $ENVNAME
done

./scripts/start_unifield.sh -s $MINUS_IN_SECOND -d $TMPPATH run $NAME_RUN

