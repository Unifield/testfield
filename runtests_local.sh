#!/usr/bin/env bash

if [[ "$COUNT" == "" ]];
then
    export COUNT=2
fi

rm output/*

python runtests.py $@

