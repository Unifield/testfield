#!/usr/bin/env bash

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

python $TESTFIELDDIR/runtests.py $@

