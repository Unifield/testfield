#!/usr/bin/env bash

TIME_BEFORE=0
HAS_OPTION=no
BROWSER=firefox

function usage()
{
    echo "Usage: "
    echo "  $0 [-b browser] [-s seconds] [-c COUNT] [ lettuce args ]"
    echo "  -h: help"
    echo "  -s: the number of seconds to shift"
    echo "  -b: the browser (firefox or chrome). Firefox: <= 46. Chrome += chromedriver"
    echo "  -c: force a line count (if not provided, use the env variable called COUNT, otherwise 2)"
    exit 1
}

while getopts ":s:b:hc:" OPTION
do
    case $OPTION in
    s)
        TIME_BEFORE=$OPTARG
        ;;
    b)
        BROWSER=$OPTARG
        ;;
    c)
        COUNT=$OPTARG
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

if [[ "$COUNT" == "" ]];
then
    COUNT=2
fi
export COUNT=$COUNT

echo "[INFO] start tests:"
echo " browser: $BROWSER"
echo " time shift: $TIME_BEFORE"
echo " count: $COUNT"

set -o errexit

# from: http://stackoverflow.com/questions/3572030/bash-script-absolute-path-with-osx
realpath() {
    [[ $1 = /* ]] && echo "$1" || echo "$PWD/${1#./}"
}

PATHDIR=`realpath $0`
TESTFIELDDIR=`dirname $PATHDIR`

if [[ -d output ]]
then
    rm -rf output
fi

mkdir output
echo "name=${TEST_NAME-Unknown}" >> output/meta
echo "description=${TEST_DESCRIPTION-Unknown}" >> output/meta
echo "date=${TEST_DATE--}" >> output/meta

PREFIX_RUN=
if [[ -z "$DISPLAY" ]];
then
    PREFIX_RUN=xvfb-run
fi


BROWSER="$BROWSER" $PREFIX_RUN faketime -f -${TIME_BEFORE}s python $TESTFIELDDIR/runtests.py $@

RETVAR=$?

exit $RETVAR

