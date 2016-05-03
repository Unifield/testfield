#!/bin/bash

set -o errexit
set -o pipefail

function run_website
{
    cd /root/testfield/website
    python performance.py
}

if [[ "$1" == "web" && $# == 1 ]];
then
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

/etc/init.d/postgresql start
cd /root/testfield

./runtests_server.sh $@

run_website;

