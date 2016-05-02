#!/usr/bin/env bash

rm -rf results/* 2> /dev/null

export TIME_BEFORE_FAILURE=

for count in 2 4
do
    export COUNT=$count

    # run the benchmark
    for nb in `seq 1 2`;
    do
        ./runtests_local.sh -t moi
    done
done

REP_RESULTS="website/performances/$1"

mkdir $REP_RESULTS
cp -R results/* "$REP_RESULTS/"

