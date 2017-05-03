#!/usr/bin/env bash

TIME_BEFORE=0
FORCED_DATE=no
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
        FORCED_DATE=yes
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
    COUNT=5
fi
export COUNT=$COUNT

echo "[INFO] start tests:"
echo " browser: $BROWSER"
echo " time shift: -$TIME_BEFORE"
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

if [ $BROWSER = "firefox" ]; then
    # Check the system Firefox first
    v=`firefox --version | cut -d' ' -f 3 | sed 's/\..*$//'`
    echo "Firefox version $v"
    if [ "$v" != 33 ]; then
        echo "  -> getting proper version"
        # Get the proper version of Firefox
        (cd $TESTFIELDDIR && ./get_firefox.sh 33.1.1)
        export PATH=$TESTFIELDDIR/firefox:$PATH
    fi
fi

if [[ $FORCED_DATE == yes ]]
then
    if [[ $(uname) == Darwin ]]
    then
        export DYLD_INSERT_LIBRARIES=/usr/local/lib/faketime/libfaketime.1.dylib
    else
        export LD_PRELOAD=/usr/local/lib/faketime/libfaketime.so.1
    fi
    export DYLD_FORCE_FLAT_NAMESPACE=1
    export FAKETIME="-${TIME_BEFORE}s"
fi

if [[ -z "$DISPLAY" ]];
then
    echo BROWSER="$BROWSER" xvfb-run -s '-screen 1 1024x768x16' -a python -u $TESTFIELDDIR/runtests.py "$@"
    BROWSER="$BROWSER" xvfb-run -s '-screen 1 1024x768x16' -a python -u $TESTFIELDDIR/runtests.py "$@"
else
    echo BROWSER="$BROWSER" python -u $TESTFIELDDIR/runtests.py "$@"
    BROWSER="$BROWSER" python -u $TESTFIELDDIR/runtests.py "$@"
fi

RETVAR=$?

exit $RETVAR

