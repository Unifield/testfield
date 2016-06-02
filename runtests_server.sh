#!/usr/bin/env bash

set -o errexit
#set -o nounset
set -o pipefail

if [[ $# -lt 2 || ( "$1" != benchmark && "$1" != "test" ) ]];
then
    echo "Usage: "
    echo "  $0 benchmark name [server_branch[|rev_number]] [web_branch[|rev_number]] [tag]"
    echo "  $0 test name [--only-setup] [server_branch[|rev_number]] [web_branch[|rev_number]] [tag]"
    exit 1
fi

source config.sh

MYTMPDIR=$SERVER_TMPDIR
ENVNAME=$SERVER_ENVNAME

SERVERDIR=$MYTMPDIR/server
WEBDIR=$MYTMPDIR/web

SESSION_NAME=unifield-$$

VERB=${1:-test}

NAME=${2:-unkown}

ONLY_SETUP=
if [[ ${3} == --only-setup ]]
then
    ONLY_SETUP=yes
    SERVERBRANCH=${4:-lp:unifield-server}
    WEBBRANCH=${5:-lp:unifield-web}
else
    ONLY_SETUP=no
    SERVERBRANCH=${3:-lp:unifield-server}
    WEBBRANCH=${4:-lp:unifield-web}
    LETTUCE_PARAMS="${*:5}"
fi

export PGPASSWORD=$DBPASSWORD

if [[ ${DBADDR} ]]
then
    PARAM_UNIFIELD_SERVER="--db_user=$DBUSERNAME --db_password=$DBPASSWORD --db_host=$DBADDR -c $MYTMPDIR/openerp-server.conf"
else

    if [[ ${DBPASSWORD} ]]
    then
        echo "If you peer connect to PostgreSQL, you cannot set a password"
        return 1
    fi

    PARAM_UNIFIELD_SERVER="--db_user=$DBUSERNAME -c $MYTMPDIR/openerp-server.conf"
fi

checkout_revision_in()
{
    REVISION=`python -c "import sys; print '' if '|' not in sys.argv[1] else sys.argv[1][sys.argv[1].index('|')+1:]" "$1"`
    BRANCH=`python -c "import sys; print sys.argv[1] if '|' not in sys.argv[1] else sys.argv[1][:sys.argv[1].index('|'):]" "$1"`

    bzr checkout "$BRANCH" "$2" || { echo Cannot checkout $BRANCH; exit 1; }

    if [[ ! ( -z "$REVISION" ) ]];
    then
        bzr revert -r "$REVISION" "$2" || { echo Cannot revert $BRANCH to revision $REVISION; exit 1; }
    fi
}

fetch_source_code()
{
    # (1) fetch the source code
    rm -rf $MYTMPDIR/server $MYTMPDIR/web || true

    checkout_revision_in "$SERVERBRANCH" "$SERVERDIR"
    checkout_revision_in "$WEBBRANCH" "$WEBDIR"

    if [[ $ONLY_SETUP == "no" ]]
    then
        # we have to get rid of the versions we don't want
        echo "88888888888888888888888888888888
    66f490e4359128c556be7ea2d152e03b 2013-04-27 16:49:56" > $MYTMPDIR/server/bin/unifield-version.txt

        cat $SERVERDIR/bin/openerp-server.py | sed s/"root"/"ssssb"/ >  $SERVERDIR/bin/openerp-server.py.bak
        rm $SERVERDIR/bin/openerp-server.py
        mv $SERVERDIR/bin/openerp-server.py.bak $SERVERDIR/bin/openerp-server.py

        sed -i.bak "s/FOR UPDATE NOWAIT//g" $SERVERDIR/bin/addons/base/ir/ir_sequence.py
    fi
}

generate_configuration_file()
{
    # 3. set up the configuration
    rm $MYTMPDIR/openerp-web.cfg $MYTMPDIR/openerp-server.conf 2> /dev/null || true

    cp config/openerp-web.cfg $MYTMPDIR/openerp-web.cfg
    cp config/openerp-server.conf $MYTMPDIR/openerp-server.conf
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
    """ >> $MYTMPDIR/openerp-server.conf

    if [[ ${DBADDR} ]];
    then
        BASE64_DBPASSWORD=`echo -n "$DBPASSWORD" | base64`
        echo db_password = $BASE64_DBPASSWORD >> $MYTMPDIR/openerp-server.conf
        echo db_host = 127.0.0.1 >> $MYTMPDIR/openerp-server.conf
        echo db_port = $DBPORT >> $MYTMPDIR/openerp-server.conf
    fi

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
        REAL_NAME=$DBNAME

        if [[ "$DBPREFIX" ]]
        then
            REAL_NAME=${DBPREFIX}_${REAL_NAME}
        fi

        echo python $SERVERDIR/bin/openerp-server.py $PARAM_UNIFIELD_SERVER -u base --stop-after-init -d $REAL_NAME
        python $SERVERDIR/bin/openerp-server.py $PARAM_UNIFIELD_SERVER -u base --stop-after-init -d $REAL_NAME
    done
}


run_unifield()
{
    # we print the commands to launch the components in a separate window in order to debug.
    #  We'll launch them later in a tmux
    echo "Run the web server:" python $WEBDIR/openerp-web.py -c $MYTMPDIR/openerp-web.cfg
    echo "Run the server:" python $SERVERDIR/bin/openerp-server.py $PARAM_UNIFIELD_SERVER

    BEFORE_COMMAND=
    if [[ ${FORCED_DATE} ]]
    then
        BEFORE_COMMAND="faketime \"${FORCED_DATE}\""
    fi

    tmux new -d -s $SESSION_NAME -n server "

        tmux new-window -n web \"
        $BEFORE_COMMAND python $WEBDIR/openerp-web.py -c $MYTMPDIR/openerp-web.cfg
        \";

        $BEFORE_COMMAND python $SERVERDIR/bin/openerp-server.py $PARAM_UNIFIELD_SERVER
        \""


    case $VERB in

    test)
        export TIME_BEFORE_FAILURE=${TIME_BEFORE_FAILURE:-40}
        export COUNT=2;

        export TEST_DESCRIPTION=${TEST_DESCRIPTION:-$NAME}
        export TEST_NAME=${TEST_NAME:-$NAME}

        rm output/* || true

        ./runtests_local.sh $LETTUCE_PARAMS || true

        DIREXPORT=website/tests/$NAME
        if [[ -e "$DIREXPORT" ]]
        then
            rm -rf "$DIREXPORT" || true
        fi
        mkdir "$DIREXPORT"

        cp -R output/* $DIREXPORT/ || true

        ;;

    benchmark)
        rm -rf results/* 2> /dev/null || true
        export TIME_BEFORE_FAILURE=

        for count in 5 15 25 35 45
        do
            export COUNT=$count

            # run the benchmark
            for nb in `seq 1 4`;
            do
                ./runtests_local.sh $LETTUCE_PARAMS || true
            done
        done

        DIREXPORT="website/performances/$NAME"
        if [[ -e "$DIREXPORT" ]]
        then
            rm -rf "$DIREXPORT" || true
        fi
        mkdir "$DIREXPORT"

        cp -R results/* "$DIREXPORT/"

        ;;

    esac

    tmux kill-session -t $SESSION_NAME
}

launch_database()
{
    # we have to setup a database if required
    LAUNCH_DB=
    if [[ ${DBPATH} && ${FORCED_DATE} ]];
    then
        DATADIR=$SERVER_TMPDIR/data-$$
        RUNDIR=$SERVER_TMPDIR/run-$$
        DBADDR=localhost

        mkdir $DATADIR $RUNDIR

        $DBPATH/initdb --username=$USER $DATADIR

        echo "port = $DBPORT" >> $DATADIR/postgresql.conf
        echo "unix_socket_directory = '$RUNDIR'" >> $DATADIR/postgresql.conf

        LAUNCH_DB="faketime ${FORCED_DATE} $DBPATH/postgres -D $DATADIR"
        tmux new -d -s PostgreSQL_$$ "$LAUNCH_DB; read"

        #TODO: Fix that... we should wait until psql can connect
        sleep 2
        psql -h $DBADDR -p $DBPORT postgres -c "CREATE USER $DBUSERNAME WITH CREATEDB PASSWORD '$DBPASSWORD'" || echo $?

    else
        FORCED_DATE=
    fi
}

DATABASES=
for FILENAME in `find instances/$ENVNAME -name *.dump | sort`;
do
    F_WITHOUT_EXTENSION=${FILENAME%.dump}
    DBNAME=${F_WITHOUT_EXTENSION##*/}

    DATABASES="$DATABASES $DBNAME"
done
FIRST_DATABASE=`echo $DATABASES | cut -d " " -f1`

export DATABASES=$DATABASES

./generate_credentials.sh $FIRST_DATABASE $DBPREFIX
fetch_source_code;
launch_database;

if [[ $ONLY_SETUP == "no" ]]
then
    python restore.py --reset-versions $ENVNAME
else
    python restore.py $ENVNAME
fi
generate_configuration_file;

#FIXME: We should do it only if necessary. How can we check that?
if [[ "$RELOAD_BASE_MODULE" != 'no' ]]
then
    upgrade_server;
fi

if [[ $ONLY_SETUP == "yes" ]]
then
    echo "Setup done!"
    exit 0
fi

DISPLAY_BEFORE=$DISPLAY

if [[ -z "$DISPLAY" ]];
then
    tmux new -d -s X_$$ "Xvfb :$$"
    export DISPLAY=:$$
fi

run_unifield;

if [[ -z "$DISPLAY_BEFORE" ]];
then
    tmux kill-session -t X_$$
fi

if [[ ${DBPATH} && ${FORCED_DATE} ]];
then
    tmux kill-session -t PostgreSQL_$$
fi

if [[ ${DATADIR} ]];
then
    rm -rf ${DATADIR}
fi

if [[ ${RUNDIR} ]];
then
    rm -rf ${RUNDIR}
fi

