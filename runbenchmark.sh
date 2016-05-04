#!/usr/bin/env bash

rm -rf results/* 2> /dev/null

export TIME_BEFORE_FAILURE=

LETTUCE_PARAMS="${*:2}"

for count in 5 10 15 20 25 30 35 40
do
    export COUNT=$count

    # run the benchmark
    for nb in `seq 1 3`;
    do
        ./runtests_local.sh $LETTUCE_PARAMS
    done
done

REP_RESULTS="website/performances/$1"

mkdir $REP_RESULTS
cp -R results/* "$REP_RESULTS/"

