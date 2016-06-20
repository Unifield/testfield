#!/usr/bin/env bash

TIME_BEFORE=0
HAS_OPTION=no

while getopts ":s:" OPTION
do
    case $OPTION in
    s)
        TIME_BEFORE=$OPTARG
        ;;
    *)
        HAS_OPTION=yes
        break
        ;;
    esac
done;

if [[ $HAS_OPTION == yes ]]
then
    shift $((OPTIND-2));
else
    shift $((OPTIND-1));
fi

set -o errexit

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

faketime -f -${TIME_BEFORE}s python $TESTFIELDDIR/runtests.py $@

RETVAR=$?

if [[ ${KILL_ID_DISPLAY} ]];
then
    echo Kill the screen
    kill -9 $KILL_ID_DISPLAY
fi


exit $RETVAR
