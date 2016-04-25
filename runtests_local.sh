#!/usr/bin/env bash

if [[ "$COUNT" == "" ]];
then
    export COUNT=2
fi

python runtests.py $@

