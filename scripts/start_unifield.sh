#!/bin/bash

set -o errexit
set -o pipefail

function usage()
{
    echo $0 [-h] [-d dir] [-c config_file] upgrade name db
    echo $0 [-h] [-d dir] [-c config_file] run name
    echo "  -h: help"
    echo "  -s: number of seconds to shift"
    echo "  -c: configuration file (default \$(pwd)/config.sh). Values looked up in this file are:"
    echo "       XMLRPCS_PORT:"
    echo "       XMLRPC_PORT:"
    echo "       WEB_PORT:"
    echo "       NETRPC_PORT:"
    echo "       DBADDR:"
    echo "       DBPORT:"
    echo "       DBPASSWORD:"
    echo "       UNIFIELDPASSWORD:"
    echo "       DBPREFIX:"
    echo "  -d: the directory where the branchs will be stored (by default: /tmp)"
}

BDIR=/tmp
CONFIG_FILE="$(pwd)/config.sh"
TIME_BEFORE=

while getopts "s:d:h:" OPTION
do
    case $OPTION in
    h)
        usage;
        exit 1
        ;;
    s)
        TIME_BEFORE=$OPTARG
        ;;
    d)
        BDIR=$OPTARG
        ;;
    c)
        CONFIG_FILE=$OPTARG
        ;;
    *)
        exit 1
    esac
done;


POS_PARAM=(${@:$OPTIND})

ACTION=${POS_PARAM[0]}
NAME=${POS_PARAM[1]}


echo "[INFO] $ACTION unifield:"
echo " config: $CONFIG_FILE"
echo " dir: $BDIR"
echo " timeshift: -$TIME_BEFORE"
if [[ $ACTION == upgrade ]]
then
    DBNAME=${POS_PARAM[2]}
    echo " database: $DBNAME"
fi

START_FAKETIME=
if [[ $TIME_BEFORE ]]
then
    START_FAKETIME="faketime -f -${TIME_BEFORE}s"
fi

case $ACTION in

    run)
        if [[ ${#POS_PARAM[*]} != 2 ]]
        then
            echo "You should define the install name (only one argument)" >&2
            usage;
            exit 1
        fi
        ;;

    upgrade)
        if [[ ${#POS_PARAM[*]} != 3 ]]
        then
            echo "You should define the install name and the DB to upgrade (only two arguments)" >&2
            usage;
            exit 1
        fi
        DBNAME=${POS_PARAM[2]}
        ;;

    *)
        echo "Bad action" >&2
        exit 1
esac


if [[ ! -e ${CONFIG_FILE} ]]
then
    echo "The configuration file doesn't exist" >&2
fi

SERVERDIR=$BDIR/server_$NAME
WEBDIR=$BDIR/web_$NAME
CFG_WEB=$BDIR/openerp-web-$NAME.cfg
CFG_SERVER=$BDIR/openerp-server.conf

PID_WEB_FILE=$WEBDIR/pid
PID_SERVER_FILE=$SERVERDIR/pid

for dirname in "$SERVERDIR" "$WEBDIR"
do
    if [[ ! -e $dirname ]]
    then
        echo "$dirname doesn't exist" >&2
        exit 1
    fi
done

# XMLRPCS_PORT, XMLRPC_PORT, WEB_PORT, NETRPC_PORT, DBADDR, DBPORT, DBPASSWORD, UNIFIELDPASSWORD
. ${CONFIG_FILE}


generate_configuration_file()
{
    # 3. set up the configuration
    rm $CFG_WEB $CFG_SERVER 2> /dev/null || true

    cp config/openerp-web.cfg $CFG_WEB
    cp config/openerp-server.conf $CFG_SERVER
    # add the specific rules

    BASE64_UNIFIELDPASSWORD=`echo -n "$UNIFIELDPASSWORD" | base64`

    echo """
admin_passwd = $BASE64_UNIFIELDPASSWORD
admin_bkpdb_passwd = $BASE64_UNIFIELDPASSWORD
admin_dropdb_passwd = $BASE64_UNIFIELDPASSWORD
admin_restoredb_passwd = $BASE64_UNIFIELDPASSWORD
xmlrpcs_port = $XMLRPCS_PORT
xmlrpc_port = $XMLRPC_PORT
root_path = $SERVERDIR/bin
netrpc_port = $NETRPC_PORT
    """ >> $CFG_SERVER

    if [[ ${DBADDR} ]];
    then
        BASE64_DBPASSWORD=`echo -n "$DBPASSWORD" | base64`
        echo db_password = $BASE64_DBPASSWORD >> $CFG_SERVER
        echo db_host = 127.0.0.1 >> $CFG_SERVER
        echo db_port = $DBPORT >> $CFG_SERVER
    fi

    echo """
server.socket_port = $WEB_PORT
openerp.server.port = '$NETRPC_PORT'
    """ >> $CFG_WEB
}

function check_unifield_up()
{
    # we have to ensure that the services work
    FAILURE=no
    for i in $(seq 1 10);
    do
        FAILURE=no

        for ports in $WEB_PORT $NETRPC_PORT
        do
            {
                set +e
                nc -z -v -w5 127.0.0.1 $ports >&2 2> /dev/null;
            }
            VAL=$?

            if [[ $VAL != 0 ]]
            then
                echo "Cannot connect to $ports"
                FAILURE=yes
            fi
        done

        if [[ $FAILURE == no ]]
        then
            echo "Can connect!"
            break
        fi

        sleep 1;
    done

    if [[ $FAILURE == yes ]]
    then
        echo "Cannot launch UniField"
        exit 1
    fi
}

generate_configuration_file;

if [[ ${DBADDR} ]]
then
    PARAM_UNIFIELD_SERVER="--db_user=$DBUSERNAME --db_password=$DBPASSWORD --db_host=$DBADDR -c $CFG_SERVER"
else

    if [[ ${DBPASSWORD} ]]
    then
        echo "If you peer connect to PostgreSQL, you cannot set a password"
        return 1
    fi

    PARAM_UNIFIELD_SERVER="--db_user=$DBUSERNAME -c $CFG_SERVER"
fi

case $ACTION in

    run)

        echo "Run WEB: $START_FAKETIME python $WEBDIR/openerp-web.py -c $CFG_WEB"
        echo "RUN SERVER: $START_FAKETIME python $SERVERDIR/bin/openerp-server.py $PARAM_UNIFIELD_SERVER"

        # we print the commands to launch the components in a separate window in order to debug.
        #  We'll launch them later in a tmux
        SESSION_NAME=unifield_$NAME
        tmux new -d -s $SESSION_NAME -n server "

            tmux new-window -n web \"
            $START_FAKETIME python $WEBDIR/openerp-web.py -c $CFG_WEB & PID="'\$!'" ;
            echo \\\$PID > $PID_WEB_FILE;
            wait \\\$PID;
            \";

            $START_FAKETIME python $SERVERDIR/bin/openerp-server.py $PARAM_UNIFIELD_SERVER & PID="'$!'" ;
            echo \$PID > $PID_SERVER_FILE;
            wait \$PID;
            \""

        check_unifield_up;

        ;;
    upgrade)

        echo "Run upgrade: python $SERVERDIR/bin/openerp-server.py $PARAM_UNIFIELD_SERVER -u base --stop-after-init -d $REAL_NAME"

        REAL_NAME=$DBNAME

        if [[ "$DBPREFIX" ]]
        then
            REAL_NAME=${DBPREFIX}_${REAL_NAME}
        fi

        python $SERVERDIR/bin/openerp-server.py $PARAM_UNIFIELD_SERVER -u base --stop-after-init -d $REAL_NAME

        ;;
    *)
        echo "Unkown action $ACTION" >&2
        ;;
esac

