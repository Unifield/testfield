#!/usr/bin/env bash

set -o errexit
set -o pipefail

BDIR=

function usage()
{
    echo $0 [-h] [-d dir] name environment
    echo "  -h: help"
    echo "  -d: set the DB path var/run in a specific directory (default: /tmp)"
}

DBPATH=/tmp

while getopts "d:h" OPTION
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

NAME=${POS_PARAM[0]}
ENVNAME=${POS_PARAM[1]}

if [[ ${#POS_PARAM[*]} != 2 ]]
then
    echo "Bad arguments" >&2
    usage;
    exit 1
fi

if [[ ! -d instances/$ENVNAME ]];
then
    echo "No env found in instance/$ENVNAME" >&2
    exit 1
fi

echo "[INFO] Upgrade env"
echo " dir: $BDIR"
echo " env: $ENVNAME"
echo " name: $NAME"

DATABASES=
for FILENAME in `find instances/$ENVNAME -name *.dump | sort`;
do
    F_WITHOUT_EXTENSION=${FILENAME%.dump}
    DBNAME=${F_WITHOUT_EXTENSION##*/}

    DATABASES="$DATABASES $DBNAME"
done

for db in $DATABASES
do
    if [[ $BDIR ]]
    then
        ./scripts/start_unifield.sh -d $BDIR upgrade $NAME $db
    else
        ./scripts/start_unifield.sh upgrade $NAME $db
    fi
done

