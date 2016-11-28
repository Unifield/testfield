#!/bin/bash

set -o errexit

source /home/testing/venv/bin/activate
cd /home/testing/testfield/

NAME_RUN=autotest

# If it fails, allow this script to keep going anyway.
# We will use the files fetched yesterday.
./fetch/owncloud/fetch.sh || true

function generate_config()
{
    cat << EOF > config.sh
#!/bin/bash

UNIFIELDADMIN=admin
UNIFIELDPASSWORD=admin

FORCED_DATE=yes
HOMEREDB=\$'ZXBpc2FnYQ==\\naG9tZXJlN3pFcGljb25jZXB0MTIz'

EOF
}

generate_config

export TEST_DESCRIPTION="Automated tests - Trunk"
export TEST_NAME="Trunk `date +'%d-%m-%Y'`"

./runtests_server.sh test $NAME_RUN 2.1-3p1

