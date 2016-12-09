#!/usr/bin/env bash

set -o errexit
#set -o nounset
set -o pipefail

if [[ $# -lt 2 || ( "$1" != benchmark && "$1" != "test" && "$1" != "setup" ) ]];
then
    echo "Usage: "
    echo "  $0 benchmark output-name [docker-hub-tag] [-t tag]"
    echo "  $0 test output-name [docker-hub-tag] [-t tag]"
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

NAME=${2:-unknown}

DOCKER_TAG=${3:-2.1-3p1}
export DOCKER_TAG
LETTUCE_PARAMS="${*:4}"

function cleanup()
{
    if [[ $VERB != setup ]];
    then
        docker-compose stop
    fi
}
trap "cleanup;" EXIT

run_tests()
{
    RET=0

    case $VERB in

    test|setup)
        export TIME_BEFORE_FAILURE=${TIME_BEFORE_FAILURE:-40}
        export COUNT=5

        export TEST_DESCRIPTION=${TEST_DESCRIPTION:-$NAME}
        export TEST_NAME=${TEST_NAME:-$NAME}
        export TEST_DATE=$($DATEUTILS '+%Y/%m/%d')

        rm output/* || true

        ./runtests_local.sh -s $MINUS_IN_SECOND $LETTUCE_PARAMS || RET=1

        DIREXPORT=website/tests/$($DATEUTILS '+%Y%m%d')_$NAME
        if [[ -e "$DIREXPORT" ]]
        then
            rm -rf "$DIREXPORT" || true
        fi
        mkdir -p "$DIREXPORT"

#        ./scripts/start_unifield.sh -d $SERVER_TMPDIR version $NAME > output/version

        docker-compose logs > output/server.log

        cp -R output/* $DIREXPORT/ || true

        ;;

    benchmark)
        rm -rf results/* 2> /dev/null || true
        export TIME_BEFORE_FAILURE=

        # If they did not tell us what tags to use, then
        # default to testing @testperf features.
        if [ -z "$LETTUCE_PARAMS" ]; then
            LETTUCE_PARAMS="-t testperf"
        fi

        for count in 5 15 25 35 45 200 400
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
        mkdir -p "$DIREXPORT"

        cp -R results/* "$DIREXPORT/"

        ;;

    esac

    return $RET
}

./start-containers.sh
run_tests
rc=$?
echo "run_tests returns rc $rc"

exit $rc

