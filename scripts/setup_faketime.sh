#!/bin/bash

#set -o errexit
#set -o pipefail




TIME_BEFORE=
FORCED_DATE=no

if [[ $# -le 1 ]]
then
    unset DYLD_INSERT_LIBRARIES
    unset LD_PRELOAD

    unset FAKETIME
    unset DYLD_FORCE_FLAT_NAMESPACE

    if [[ $# == 1 ]];
    then
        if [[ $(uname) == Darwin ]]
        then
            export DYLD_INSERT_LIBRARIES=/usr/local/lib/faketime/libfaketime.1.dylib
        else
            export LD_PRELOAD=/usr/local/lib/faketime/libfaketime.so.1
        fi
        export DYLD_FORCE_FLAT_NAMESPACE=1
        export FAKETIME=-${1}s

        # we have to ensure to export the new environment variables
        #  if we create a new tmux session.
        tmux set-option -ga update-environment ' FAKETIME DYLD_FORCE_FLAT_NAMESPACE LD_PRELOAD DYLD_INSERT_LIBRARIES' || true
    fi

else
    echo $0 [time]
    echo "  time: number of seconds to shift (default: no)"
fi

if [[ ${FAKETIME} ]]
then
    echo Shift: -${1}s
else
    echo Shift: no
fi
echo Current date: $(date)

