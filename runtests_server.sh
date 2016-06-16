#!/usr/bin/env bash

set -o errexit
#set -o nounset
set -o pipefail

if [[ $# -lt 2 || ( "$1" != benchmark && "$1" != "test" && "$1" != "setup" ) ]];
then
    echo "Usage: "
    echo "  $0 benchmark name [server_branch[|rev_number]] [web_branch[|rev_number]] [-t tag]"
    echo "  $0 test name [server_branch[|rev_number]] [web_branch[|rev_number]] [-t tag]"
    exit 1
fi

source config.sh

################################################################
# Fetch the time difference between the date we want to use to run the tests
DATEUTILS=date
if [[ $(uname) == Darwin ]]
then
    DATEUTILS=gdate
fi

BEFORE=$($DATEUTILS -d "2016-05-25" '+%s')
NOW=$($DATEUTILS '+%s')

if [[ ${FORCED_DATE} == yes ]];
then
    MINUS_IN_SECOND=$[ $NOW - $BEFORE ]
else
    MINUS_IN_SECOND=0
fi
#################################################################

VERB=${1:-test}
ENVNAME=$SERVER_ENVNAME

NAME=${2:-unkown}

SERVERBRANCH=${3:-lp:unifield-server}
WEBBRANCH=${4:-lp:unifield-web}
LETTUCE_PARAMS="${*:5}"

function cleanup()
{
    if [[ $VERB != setup ]];
    then
        ./scripts/kill_db.sh -D $SERVER_TMPDIR $NAME || true
        ./scripts/stop_unifield.sh -d $SERVER_TMPDIR $NAME || true
    fi
}
trap "cleanup;" EXIT


export PGPASSWORD=$DBPASSWORD

run_tests()
{
    case $VERB in

    test|setup)
        export TIME_BEFORE_FAILURE=${TIME_BEFORE_FAILURE:-40}
        export COUNT=2;

        export TEST_DESCRIPTION=${TEST_DESCRIPTION:-$NAME}
        export TEST_NAME=${TEST_NAME:-$NAME}
        export TEST_DATE=$($DATEUTILS '+%Y/%m/%d')

        rm output/* || true

        ./runtests_local.sh -s $MINUS_IN_SECOND $LETTUCE_PARAMS || true

        DIREXPORT=website/tests/$($DATEUTILS '+%Y%m%d')_$NAME
        if [[ -e "$DIREXPORT" ]]
        then
            rm -rf "$DIREXPORT" || true
        fi
        mkdir "$DIREXPORT"

        ./scripts/start_unifield.sh -d $SERVER_TMPDIR version $NAME > output/version

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
                ./runtests_local.sh -s $MINUS_IN_SECOND $LETTUCE_PARAMS || true
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
}

launch_database()
{
    if [[ $DBUSERNAME != $DBPASSWORD ]]
    then
        echo Username and password must be the same if you want to set a fixed date
        exit 1
    fi

    ./scripts/create_db.sh -P ${DBPATH} -D $SERVER_TMPDIR -s $MINUS_IN_SECOND -p $DBPORT -c $DBUSERNAME $NAME
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

./scripts/fetch_unifield.sh -W "$WEBBRANCH" -S "$SERVERBRANCH" -d $SERVER_TMPDIR -r $NAME

# we have to setup a database if required
if [[ ${DBPATH} && ${FORCED_DATE} == yes ]];
then
    launch_database;
else
    FORCED_DATE=no
fi

python restore.py --reset-versions $ENVNAME

./scripts/upgrade_unifield.sh -d $SERVER_TMPDIR $NAME $ENVNAME

./scripts/start_unifield.sh -s $MINUS_IN_SECOND -d $SERVER_TMPDIR run $NAME

run_tests;

