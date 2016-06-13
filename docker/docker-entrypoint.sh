#!/bin/bash

set -o errexit

export LANG=C.UTF-8
# if you want to create a RAMFS with the database
PARAMS=$@

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
    cd /home/testing/testfield/website
    cp -R /output/benchmarks/* performances/ 2> /dev/null || true
    cp -R /output/tests/* tests/ 2> /dev/null || true
    python performance.py
}

function get_repo
{
    git clone -b $BRANCH_TOO_CLONE https://github.com/hectord/testfield.git && cd testfield

    if [[ -f config.sh ]];
    then
        rm config.sh
    fi
    cp ../config.sh .
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
    echo "  $0 benchmark name [--branch=git_branch] [server_branch] [web_branch] [tag]"
    echo "  $0 test name [--branch=git_branch] [server_branch] [web_branch] [tag]"
    echo "  $0 web"
    exit 1
fi

TO_PATH=
FROM_PATH=

if [[ "$1" == "benchmark" ]];
then
    TO_PATH=/output/benchmarks/${ARRPARAMS[1]}
    FROM_PATH=/home/testing/testfield/website/performances/${ARRPARAMS[1]}
else
    TO_PATH=/output/tests/${ARRPARAMS[1]}
    FROM_PATH=/home/testing/testfield/website/tests/${ARRPARAMS[1]}
fi

if [[ -e $TO_PATH ]];
then
    echo "This path already exist: $TO_PATH"
    exit 1
fi

get_repo;

cd /home/testing/testfield

./fetch/owncloud/fetch.sh

# we have to create the directories for the input/output files (features & dumps)
mkdir output || true

cd /home/testing/testfield

function copy()
{
    if [[ -e $TO_PATH ]];
    then
        rm -rf $TO_PATH;
    fi
    mkdir $TO_PATH;

    if [[ -e $FROM_PATH ]]
    then
        cp -R $FROM_PATH/* $TO_PATH;
    fi
}
trap "copy;" EXIT;

./runtests_server.sh $PARAMS
