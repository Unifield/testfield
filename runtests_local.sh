#!/usr/bin/env bash

DIREXPORT=website/tests/last

if [[ "$COUNT" == "" ]];
then
    export COUNT=2
fi

rm output/*

export TEST_NAME=Last
export TEST_DESCRIPTION=Run locally

python runtests.py $@


if [[ -e "$DIREXPORT" ]]
then
    rm -rf "$DIREXPORT"
fi
mkdir "$DIREXPORT"

cp output/* $DIREXPORT/

