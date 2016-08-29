#!/usr/bin/env bash

set -o errexit
set -o pipefail

BDIR=
FORCED_DATE=no

function usage()
{
    echo $0 [-h] [-d dir] name environment
    echo "  -h: help"
    echo "  -d: set the DB path var/run in a specific directory (default: /tmp)"
    echo "  -s: set the current date when upgrading postgres (default: no)"
}

DBPATH=/tmp

while getopts "s:d:h" OPTION
do
    case $OPTION in
    h)
        usage;
        exit 1
        ;;
    d)
        BDIR=$OPTARG
        ;;
    s)
        FORCED_DATE=yes
        TIME_BEFORE=$OPTARG
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

START_FAKETIME=
if [[ $FORCED_DATE == yes ]]
then
    START_FAKETIME="-s ${TIME_BEFORE}"
fi

echo "[INFO] Upgrade env"
echo " dir: $BDIR"
echo " env: $ENVNAME"
echo " name: $NAME"
echo " faketime: $FORCED_DATE"

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
        ./scripts/start_unifield.sh $START_FAKETIME -d $BDIR upgrade $NAME $db
    else
        ./scripts/start_unifield.sh $START_FAKETIME upgrade $NAME $db
    fi
done

