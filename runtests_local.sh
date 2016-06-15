#!/usr/bin/env bash


getopts ":s:" VALUE
TIME_BEFORE=0
if [[ $VALUE == "s" ]]
then
    TIME_BEFORE=$OPTARG
fi
shift $(((OPTIND-1)));

# from: http://stackoverflow.com/questions/3572030/bash-script-absolute-path-with-osx
realpath() {
    [[ $1 = /* ]] && echo "$1" || echo "$PWD/${1#./}"
}

PATHDIR=`realpath $0`
TESTFIELDDIR=`dirname $PATHDIR`

if [[ "$COUNT" == "" ]];
then
    export COUNT=2
fi

if [[ -d output ]]
then
    rm -rf output
fi

KILL_ID_DISPLAY=
if [[ -z "$DISPLAY" ]];
then
    Xvfb :$$ &
    KILL_ID_DISPLAY=$!
    export DISPLAY=:$$
fi

function clean(){
    if [[ ${KILL_ID_DISPLAY} ]];
    then
        echo Kill the screen
        kill -9 $KILL_ID_DISPLAY
    fi
}

trap "clean;" EXIT;

faketime -f -${TIME_BEFORE}s python $TESTFIELDDIR/runtests.py $@

RETVAR=$?

exit $RETVAR
