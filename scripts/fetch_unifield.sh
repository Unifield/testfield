#!/bin/bash

set -o errexit
set -o pipefail

BDIR=/tmp
BWEB=lp:unifield-web
BSERVER=lp:unifield-server
RESET_VERSION=no

function usage()
{
    echo "$0 [-h] [ -W  branch[|rev] ] [ -S branch[|rev]] [ -d dir ] name"
    echo "  -h: help"
    echo "  -W: the server branch (evt. with the revision, by default: lp:unifield-web)"
    echo "  -S: the web branch (evt. with the revision, by default: lp:unifield-server)"
    echo "  -d: the directory where the branchs will be stored (by default: /tmp)"
    echo "  -r: reset the versions"
}

while getopts "rhW:S:d:" OPTION
do
    case $OPTION in
    r)
        RESET_VERSION=yes
        ;;
    h)
        usage;
        exit 1
        ;;
    W)
        BWEB=$OPTARG
        ;;
    S)
        BSERVER=$OPTARG
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
    echo "You should define what will be the install name (only ONE argument)" >&2
    usage;
    exit 1
fi

echo "[INFO] fetch code:"
echo " Directory: $BDIR"
echo " Web: $BWEB"
echo " Server: $BSERVER"
echo " reset: $RESET_VERSION"

NAME=${POS_PARAM[0]}

SERVERDIR=$BDIR/server_$NAME
WEBDIR=$BDIR/web_$NAME

for dirname in "$SERVERDIR" "$WEBDIR"
do
    if [[ -e $BDIR/$dirname ]]
    then
        echo "$BDIR/$dirname already exists" >&2
        exit 1
    fi
done


checkout_revision_in()
{
    REVISION=`python -c "import sys; print '' if '|' not in sys.argv[1] else sys.argv[1][sys.argv[1].index('|')+1:]" "$1"`
    BRANCH=`python -c "import sys; print sys.argv[1] if '|' not in sys.argv[1] else sys.argv[1][:sys.argv[1].index('|'):]" "$1"`


    if [[ ! ( -z "$REVISION" ) ]];
    then
        bzr checkout --lightweight -r "$REVISION" "$BRANCH" "$2" || { echo Cannot checkout $BRANCH; exit 1; }
    else
        bzr checkout --lightweight "$BRANCH" "$2" || { echo Cannot checkout $BRANCH; exit 1; }
    fi
}

# (1) fetch the source code
rm -rf $MYTMPDIR/server $MYTMPDIR/web || true

checkout_revision_in "$BSERVER" "$SERVERDIR"
checkout_revision_in "$BWEB" "$WEBDIR"

if [[ $RESET_VERSION == "yes" ]]
then
    # we have to get rid of the versions we don't want
    echo "88888888888888888888888888888888
66f490e4359128c556be7ea2d152e03b 2013-04-27 16:49:56" > $SERVERDIR/bin/unifield-version.txt

    cat $SERVERDIR/bin/openerp-server.py | sed s/"root"/"ssssb"/ >  $SERVERDIR/bin/openerp-server.py.bak
    rm $SERVERDIR/bin/openerp-server.py
    mv $SERVERDIR/bin/openerp-server.py.bak $SERVERDIR/bin/openerp-server.py

    sed -i.bak "s/FOR UPDATE NOWAIT//g" $SERVERDIR/bin/addons/base/ir/ir_sequence.py
fi

echo "[UniField setup] Done!"

