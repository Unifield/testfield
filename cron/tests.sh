#!/bin/bash

set -o errexit

if [[ $TMUX ]]
then
    echo "\$TMUX is set!" >&2
    exit 1
fi

source /home/testing/myenv2/bin/activate
cd /home/testing/testfield/

TMPPATH=/home/testing/repo
DBDIR=/usr/lib/postgresql/8.4/bin/
ENVNAME=lightweight
NAME_RUN=autotest

# remove the previous environment
./scripts/stop_unifield.sh -d $TMPPATH $NAME_RUN || true
./scripts/kill_db.sh -D $TMPPATH $NAME_RUN || true

# If it fails, allow this script to keep going anyway.
# We will use the files fetched yesterday.
./fetch/owncloud/fetch.sh || true

function generate_config()
{
    cat << EOF > config.sh
#!/bin/bash

NETRPC_PORT=7006
WEB_PORT=7004
XMLRPC_PORT=7005
XMLRPCS_PORT=7007

UNIFIELDADMIN=admin
UNIFIELDPASSWORD=admin

DBPASSWORD=selenium_testing
DBADDR=127.0.0.1
DBUSERNAME=selenium_testing
DBPORT=7014
DBPREFIX='$1'

SERVER_HOST=127.0.0.1
SERVER_TMPDIR=$TMPPATH
SERVER_ENVNAME=$ENVNAME

DBPATH=$DBDIR
FORCED_DATE=yes

HOMEREDB=\$'ZXBpc2FnYQ==\\naG9tZXJlN3pFcGljb25jZXB0MTIz'

EOF
}

# We have to run the tests and create the environment
NAME="TRUNK`date +'%d%m%Y'`"
generate_config "TESTS"

export TEST_DESCRIPTION="Automated tests - Trunk"
export TEST_NAME="Trunk `date +'%d-%m-%Y'`"

./runtests_server.sh setup $NAME_RUN

