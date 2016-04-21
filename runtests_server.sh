#!/bin/bash

MYTMPDIR=/tmp
ENVNAME=P1C1

SERVERDIR=$MYTMPDIR/server
WEBDIR=$MYTMPDIR/web

SESSION_NAME=unifield-$$

if [[ $# == 0 ]];
then
    SERVERBRANCH=lp:unifield-server
    WEBBRANCH=lp:unifield-web
elif [[ $# == 1 ]];
then
    SERVERBRANCH=$1
    WEBBRANCH=lp:unifield-web
elif [[ $# == 2 ]];
then
    SERVERBRANCH=$1
    WEBBRANCH=$2
else
    exit 1
fi

source config.sh
export PGPASSWORD=$DBPASSWORD

PARAM_UNIFIELD_SERVER="--db_user=$DBUSERNAME --db_password=$DBPASSWORD --db_host=$DBADDR -c $MYTMPDIR/openerp-server.conf"

fetch_source_code()
{
    # (1) fetch the source code
    rm -rf $MYTMPDIR/server $MYTMPDIR/web
    bzr checkout --lightweight "$SERVERBRANCH" "$SERVERDIR"
    bzr checkout --lightweight "$WEBBRANCH" "$WEBDIR"
    echo
}

generate_configuration_file()
{
    # 3. set up the configuration
    rm $MYTMPDIR/openerp-web.cfg $MYTMPDIR/openerp-server.conf 2> /dev/null
    cp config/openerp-web.cfg $MYTMPDIR/openerp-web.cfg
    cp config/openerp-server.conf $MYTMPDIR/openerp-server.conf
    # add the specific rules

    BASE64_UNIFIELDPASSWORD=`echo -n "$UNIFIELDPASSWORD" | base64`
    BASE64_DBPASSWORD=`echo -n "$DBPASSWORD" | base64`

    echo """
admin_passwd = $BASE64_UNIFIELDPASSWORD
admin_bkpdb_passwd = $BASE64_UNIFIELDPASSWORD
admin_dropdb_passwd = $BASE64_UNIFIELDPASSWORD
admin_restoredb_passwd = $BASE64_UNIFIELDPASSWORD
db_password = $BASE64_DBPASSWORD
xmlrpcs_port = $XMLRPCS_PORT
xmlrpc_port = $XMLRPC_PORT
root_path = $SERVERDIR/bin
netrpc_port = $NETRPC_PORT
    """ >> $MYTMPDIR/openerp-server.conf

    echo """
server.socket_port = $WEB_PORT
openerp.server.port = '$NETRPC_PORT'
    """ >> $MYTMPDIR/openerp-web.cfg
}

upgrade_server()
{
    # at first we have to upgrade all the databases
    for DBNAME in $DATABASES;
    do
        python $SERVERDIR/bin/openerp-server.py $PARAM_UNIFIELD_SERVER -u base --stop-after-init -d $DBNAME
    done
}


run_unifield()
{
    tmux new -d -s $SESSION_NAME "

        tmux new-window -n web \"
        python $WEBDIR/openerp-web.py -c $MYTMPDIR/openerp-web.cfg
        \";

        tmux new-window -n web \"
        python $SERVERDIR/bin/openerp-server.py --db_user=$DBUSERNAME --db_password=$DBPASSWORD --db_host=$DBADDR -c $MYTMPDIR/openerp-server.conf
        \";

        tmux new-window -n tests \"
        tmux set-option -g history-limit 3000;
        export COUNT=2;
        ./runtests_local.sh;
        tmux kill-session -t $SESSION_NAME
        \";
        \""
}

DATABASES=
for FILENAME in `find instances/$ENVNAME -name *.dump`;
do
    F_WITHOUT_EXTENSION=${FILENAME%.dump}
    DBNAME=${F_WITHOUT_EXTENSION##*/}

    DATABASES="$DATABASES $DBNAME"
done
FIRST_DATABASE=`echo $DATABASES | cut -d " " -f1`

fetch_source_code;
python restore.py $ENVNAME
generate_configuration_file;
upgrade_server;

if [[ ! $DISPLAY ]];
then
    tmux new -d -s X_$$ "Xvfb :99"
    export DISPLAY=:99
fi

./generate_credentials.sh $FIRST_DATABASE
run_unifield;

