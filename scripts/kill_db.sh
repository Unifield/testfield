
set -o errexit
set -o pipefail

if [[ $# != 1 ]]
then
    echo "No name provided" >&2
else
    if [[ -e /tmp/data-$1/postmaster.pid ]];
    then
        PID=$(head -1 /tmp/data-$1/postmaster.pid)

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

    if [[ -e /tmp/data-$1 ]]
    then
        rm -rf /tmp/data-$1
    fi

    if [[ -e /tmp/run-$1 ]]
    then
        rm -rf /tmp/run-$1
    fi

    echo "Cleaning done!"
fi

