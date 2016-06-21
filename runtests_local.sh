#!/usr/bin/env bash

TIME_BEFORE=0
HAS_OPTION=no
BROWSER=firefox

function usage()
{
    echo "Usage: "
    echo "  $0 [-b browser] [-s seconds] [ lettuce args ]"
    echo "  -h: help"
    echo "  -s: the number of seconds to shift"
    echo "  -b: the browser (firefox or chrome). Firefox: <= 46. Chrome += chromedriver"
    exit 1
}

while getopts ":s:b:h" OPTION
do
    case $OPTION in
    s)
        TIME_BEFORE=$OPTARG
        ;;
    b)
        BROWSER=$OPTARG
        ;;
    h)
        usage;
        exit 1
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

echo "[INFO] start tests:"
echo " browser: $BROWSER"
echo " time shift: $TIME_BEFORE"

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

BROWSER="$BROWSER" faketime -f -${TIME_BEFORE}s python $TESTFIELDDIR/runtests.py $@

RETVAR=$?

if [[ ${KILL_ID_DISPLAY} ]];
then
    echo Kill the screen
    kill -9 $KILL_ID_DISPLAY
fi


exit $RETVAR
