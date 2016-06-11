#!/bin/bash

set -o errexit
set -o pipefail

BDIR=/tmp

function usage()
{
    echo "$0 [-h] [ -d dir ] name"
    echo "  -h: help"
    echo "  -d: the directory where the branchs will be stored (by default: /tmp)"
}

while getopts "hd:" OPTION
do
    case $OPTION in
    h)
        usage;
        exit 1
        ;;
    d)
        BDIR=$OPTARG
        ;;
    *)
        exit 1
    esac
done;


POS_PARAM=(${@:$OPTIND})

if [[ ${#POS_PARAM[*]} != 1 ]]
then
    echo "You should define the install name" >&2
    usage;
    exit 1
fi

NAME=${POS_PARAM[0]}

for dirname in "server_$NAME" "web_$NAME"
do
    DIR_COMPONENT=$BDIR/$dirname

    # kill the applications if necessary
    if [[ -e $DIR_COMPONENT/pid ]]
    then
        PID=$(cat $DIR_COMPONENT/pid | head -1)
        if kill -0 $PID;
        then
            echo "Killing $PID"
            kill -SIGKILL $PID
        else
            echo "No process with PID $PID"
        fi
    fi

    if [[ -e $DIR_COMPONENT ]]
    then
        rm -rf $DIR_COMPONENT
        echo "Delete $DIR_COMPONENT"
    fi
done

echo Done!

