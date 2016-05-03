#!/bin/bash

set -o errexit
set -o nounset
set -o pipefail

if [[ $# -lt 2 || ( "$1" != benchmark && "$1" != "test" ) ]];
then
    echo "Usage: "
    echo "  $0 benchmark name [server_branch] [web_branch] [tag]"
    echo "  $0 test name [server_branch] [web_branch] [tag]"
    exit 1
fi

/etc/init.d/postgresql start
cd /root/testfield

./runtests_server.sh $@

cd /root/testfield/website
python performance.py


