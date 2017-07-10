#!/bin/bash

set -o errexit
set -o pipefail

DBPATH=/tmp
DBDIR=
DBPORT=5432
CREDENTIALS=testing
FORCED_DATE=no
TIME_BEFORE=0

function usage()
{
    echo $0 [-h] -P execpath [-D dbpath] [-s seconds] [-p port] [-c credentials] name
    echo "  -h: help"
    echo "  -P: path to PostgreSQL"
    echo "  -D: set the DB path var/run in a specific directory (default: /tmp)"
    echo "  -s: set the current date when launching postgres (default: no)"
    echo "  -p: the port used by PostgreSQL (default: 5432)"
    echo "  -c: credentials used by the database (default: testing)"
}

while getopts "P:hD:s:p:c:" OPTION
do
    case $OPTION in
    h)
        usage;
        exit 1
        ;;
    D)
        DBPATH=$OPTARG
        ;;
    P)
        DBDIR=$OPTARG
        ;;
    s)
        FORCED_DATE=yes
        TIME_BEFORE=$OPTARG
        ;;
    p)
        DBPORT=$OPTARG
        ;;
    c)
        CREDENTIALS=$OPTARG
        ;;
    *)
        exit 1
    esac
done;

echo "[INFO] create DB:"
echo " PostgreSQL path: $DBPATH"
echo " dir: $DBDIR"
echo " port: $DBPORT"
echo " username: $CREDENTIALS"
echo " password: $CREDENTIALS"
echo " time shift: -$TIME_BEFORE"

POS_PARAM=(${@:$OPTIND})
NAME_KILL=${POS_PARAM[0]}

if [[ ${#POS_PARAM[*]} != 1 ]]
then
    echo "There must be a unique name for your new database" >&2
    exit 1
fi

if [[ -z ${DBDIR} ]]
then
    echo "You should set at least a DB directory" >&2
    exit 1
fi

if [[ ! -e ${DBDIR}/initdb || ! -e ${DBDIR}/postgres ]]
then
    echo "I don't find PostgreSQL or initdb in ${DBDIR}" >&2
    exit 1
fi

if [[ $TMUX ]]
then
    echo "You shouldn't launch that in a TMUX console" >&2
    exit 1
fi

if ! which nc >&2 > /dev/null;
then
    echo No nc utility >&2
    exit 1
fi

# port open?
if nc -z -v -w5 127.0.0.1 $DBPORT >&2 2> /dev/null;
then
    echo Port $DBPORT already in use >&2
    exit 1
fi

DBPASSWORD=$CREDENTIALS
DBUSERNAME=$CREDENTIALS

# we have to setup a database if required
LAUNCH_DB=

DATADIR=$DBPATH/data-$NAME_KILL
RUNDIR=$DBPATH/run-$NAME_KILL
DBADDR=localhost

mkdir $DATADIR $RUNDIR
FAKED_COMMAND=''
# we have to change the date before the initdb otherwise PostgreSQL doesn't take the
#   new date into account.
if [[ $FORCED_DATE == yes ]]
then
    source scripts/setup_faketime.sh ${TIME_BEFORE}
    FAKED_COMMAND="FAKETIME=$FAKETIME LD_PRELOAD=$LD_PRELOAD"
fi

$DBDIR/initdb --username=$USER $DATADIR

echo "port = $DBPORT" >> $DATADIR/postgresql.conf

if [[ $($DBDIR/postgres --version | egrep -o '[0-9]{1,}\.[0-9]{1,}') == "8.4" ]]
then
    echo "unix_socket_directory = '$RUNDIR'" >> $DATADIR/postgresql.conf
else
    echo "unix_socket_directories = '$RUNDIR'" >> $DATADIR/postgresql.conf
fi

tmux new -d -s PostGre_$NAME_KILL "$FAKED_COMMAND $DBDIR/postgres -D $DATADIR"

#TODO: Fix that... we should wait until psql can connect
for i in $(seq 1 10);
do
    ROLE_CREATED=1

    # >&2 2> /dev/null
    psql -h $DBADDR -p $DBPORT postgres -c "CREATE USER $DBUSERNAME WITH CREATEDB PASSWORD '$DBPASSWORD'" >&2 2> /dev/null  || {
        ROLE_CREATED=0
    }
    if [[ $ROLE_CREATED == 1 ]]
    then
        psql -h $DBADDR -p $DBPORT postgres -c "UPDATE pg_database set datallowconn = TRUE where datname = 'template0'";
        psql -h $DBADDR -p $DBPORT postgres -c "UPDATE pg_database set datistemplate = FALSE where datname = 'template1'";
        psql -h $DBADDR -p $DBPORT postgres -c "DROP DATABASE template1"
        psql -h $DBADDR -p $DBPORT postgres -c "CREATE DATABASE template1 with template = template0 encoding = 'UTF8'"
        psql -h $DBADDR -p $DBPORT template0 -c "UPDATE pg_database set datistemplate = TRUE where datname = 'template1';" 
        psql -h $DBADDR -p $DBPORT template1 -c "UPDATE pg_database set datallowconn = FALSE where datname = 'template0';" 
        echo "[DB setup] Done!"
        exit 0
    fi

    echo "Cannot create the role, let's retry later"
    sleep 1
done

echo "Failure!"
exit 1

