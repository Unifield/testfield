#!/bin/bash

export LANG=C.UTF-8

#set -o errexit
#set -o pipefail

function run_website
{
    cd /root/testfield/website
    cp -R /output/benchmarks/* performances/ 2> /dev/null || true
    cp -R /output/tests/* tests/ 2> /dev/null || true
    python performance.py
}

function get_repo
{
    git clone https://github.com/hectord/testfield.git && cd testfield
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
    echo "  $0 benchmark name [server_branch] [web_branch] [tag]"
    echo "  $0 test name [server_branch] [web_branch] [tag]"
    echo "  $0 web"
    exit 1
fi

TO_PATH=
FROM_PATH=

if [[ "$1" == "benchmark" ]];
then
    TO_PATH=/output/benchmarks/$2
    FROM_PATH=/root/testfield/website/performances/$2
else
    TO_PATH=/output/tests/$2
    FROM_PATH=/root/testfield/website/tests/$2
fi

if [[ -e $TO_PATH ]];
then
    echo "This path already exist: $TO_PATH"
    exit 1
fi

get_repo;

mkdir output || true

cp -R /input/* .

/etc/init.d/postgresql start
cd /root/testfield

./runtests_server.sh $@

if [[ -e $TO_PATH ]]
then
    rm -rf $TO_PATH
fi
mkdir $TO_PATH


if [[ -e $FROM_PATH ]]
then
    cp -R $FROM_PATH/* $TO_PATH
fi

#    cp -R /output/benchmarks/* ../website/performances/ 2> /dev/null || true
#    cp -R /output/tests/* ../website/tests/ 2> /dev/null || true

#cp -R website/performances/* /output/benchmarks/
#cp -R website/tests/* /output/tests/


