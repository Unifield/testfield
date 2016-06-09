
set -o errexit
set -o pipefail

function usage()
{
    echo $0 [-h] [-D dbpath] name
    echo "  -h: help"
    echo "  -D: set the DB path var/run in a specific directory (default: /tmp)"
}

DBPATH=/tmp

while getopts "D:h" OPTION
do
    case $OPTION in
    h)
        usage;
        exit 1
        ;;
    D)
        DBPATH=$OPTARG
        ;;
    *)
        exit 1
    esac
done;

POS_PARAM=(${@:$OPTIND})
NAME=${POS_PARAM[0]}

if [[ ${#POS_PARAM[*]} != 1 ]]
then
    echo "No name provided" >&2
else
    if [[ -e $DBPATH/data-$NAME/postmaster.pid ]];
    then
        PID=$(head -1 $DBPATH/data-$NAME/postmaster.pid)

        if kill -0 $PID;
        then
            echo "Killing $PID"
            kill -INT $PID
        else
            echo "No process with PID $PID"
        fi
    else
        echo "No PID found" >&2
    fi

    if [[ -e $DBPATH/data-$NAME ]]
    then
        rm -rf $DBPATH/data-$NAME
    fi

    if [[ -e $DBPATH/run-$NAME ]]
    then
        rm -rf $DBPATH/run-$NAME
    fi

    echo "Cleaning done!"
fi

