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

if [[ -z "$DISPLAY" ]];
then
    tmux new -d -s X_$$ "Xvfb :session-$$"
    export DISPLAY=:session-$$
fi

faketime -f -${TIME_BEFORE}s python $TESTFIELDDIR/runtests.py $@

RETVAR=$?

if [[ -z "$DISPLAY" ]];
then
    tmux kill-session -t X_$$
fi

exit $RETVAR
