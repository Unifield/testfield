#!/bin/bash

export LANG=C.UTF-8

set -o errexit
#set -o pipefail

# if you want to create a RAMFS with the database
PARAMS=$@

HAS_REFRESH=`echo $PARAMS | sed -n 's/.*--refresh.*/YES/p'`
PARAMS=`echo $PARAMS | sed 's/--refresh//'`

HAS_QUICK=`echo $PARAMS | sed -n 's/.*--quick.*/YES/p'`
PARAMS=`echo $PARAMS | sed 's/--quick//'`

HAS_RELOAD=`echo $PARAMS | sed -n 's/.*--reload.*/YES/p'`
PARAMS=`echo $PARAMS | sed 's/--reload//'`

BRANCH_TOO_CLONE=master
if [[ ! -z "`echo $PARAMS | sed -n 's/.*--branch*/YES/p'`" ]]
then
    BRANCH_TOO_CLONE=`echo $PARAMS | sed 's/.*--branch=\([^ ]*\).*/\1/'`
    PARAMS=`echo $PARAMS | sed 's/--branch=[^ ]*//'`
fi

ARRPARAMS=($PARAMS)

function make_ramfs
{
    PATH_TMP=/tmp/build_ramfs
    RAMDIR=$1
    SIZE_MB=$2

    if [[ -e "/tmp/build_ramfs" ]]
    then
        rm -rf /tmp/build_ramfs
    fi
    mkdir /tmp/build_ramfs

    if [[ -e "$RAMDIR" ]]
    then
        cp -R $RAMDIR/* /tmp/build_ramfs/ || true
        rm -rf $RAMDIR
    fi

    mkdir $RAMDIR
    mount -t ramfs -o size=${SIZE_MB:-512}M ramfs $RAMDIR
    cp -R /tmp/build_ramfs/* $RAMDIR/  || true
}

function run_website
{
    cd /root/testfield/website
    cp -R /output/benchmarks/* performances/ 2> /dev/null || true
    cp -R /output/tests/* tests/ 2> /dev/null || true
    python performance.py
}

function get_repo
{
    git clone -b $BRANCH_TOO_CLONE https://github.com/hectord/testfield.git && cd testfield
}

if [[ "$1" == "web" && $# == 1 ]];
then
    get_repo;
    run_website;
    exit 0
fi

if [[ $# -lt 2 || ( "$1" != benchmark && "$1" != "test" ) ]];
then
    echo "Usage: "
    echo "  $0 benchmark name [--quick] [--refresh] [--reload] [--branch=git_branch] [server_branch] [web_branch] [tag]"
    echo "  $0 test name [--quick] [--refresh] [--reload] [--branch=git_branch] [server_branch] [web_branch] [tag]"
    echo "  $0 web"
    exit 1
fi

TO_PATH=
FROM_PATH=

#LETTUCE_PARAMS="${*:5}"

if [[ "$1" == "benchmark" ]];
then
    TO_PATH=/output/benchmarks/${ARRPARAMS[1]}
    FROM_PATH=/root/testfield/website/performances/${ARRPARAMS[1]}
else
    TO_PATH=/output/tests/${ARRPARAMS[1]}
    FROM_PATH=/root/testfield/website/tests/${ARRPARAMS[1]}
fi

if [[ -e $TO_PATH ]];
then
    echo "This path already exist: $TO_PATH"
    exit 1
fi

get_repo;

BACKUP_NAME=backup.tar.gz
PATH_CACHE=/output/$BACKUP_NAME
if [[ ! ( -z "$HAS_REFRESH" ) || ! ( -e "$PATH_CACHE" ) ]]
then
    if [[ -e "$PATH_CACHE" ]]
    then
        rm -f "$PATH_CACHE"
    fi

    echo "Downloading the tests..."
    curl http://uf0003.unifield.org/backup.tar.gz > $PATH_CACHE
fi

cp $PATH_CACHE $BACKUP_NAME
gunzip $BACKUP_NAME -c > tmp.tar
tar -xvvf tmp.tar

if [[ ! ( -z "$HAS_QUICK" ) ]]
then
    PG_DATA_DIR=/var/lib/postgresql/8.4/main/
    #TODO: Check that it works with PostgreSQL 8.4 ... (the path should be differnet)
    make_ramfs $PG_DATA_DIR
    chown -R postgres:postgres $PG_DATA_DIR
    chmod 0700 $PG_DATA_DIR

    cd /tmp
    make_ramfs /root/testfield
    cd /root/testfield
fi

# we have to create the directories for the input/output files (features & dumps)
mkdir output || true

/etc/init.d/postgresql start
cd /root/testfield

export RELOAD_BASE_MODULE=no
if [[ ! ( -z "$HAS_RELOAD" ) ]]
then
    export RELOAD_BASE_MODULE=yes
fi

./runtests_server.sh $PARAMS

if [[ -e $TO_PATH ]]
then
    rm -rf $TO_PATH
fi
mkdir $TO_PATH


if [[ -e $FROM_PATH ]]
then
    cp -R $FROM_PATH/* $TO_PATH
fi

