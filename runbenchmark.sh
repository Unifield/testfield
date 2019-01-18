#!/usr/bin/env bash

rm -rf results/* 2> /dev/null

export TIME_BEFORE_FAILURE=

LETTUCE_PARAMS="${*:2}"
TAG="-t supply1"

echo $LETTUCE_PARAMS
#Première série de tests Supply : 10 25 100
#for count in 10 25 100
for count in 10
do
    export COUNT=$count

    # run the benchmark
    for nb in `seq 1 3`;
    do
    	#./runtests_local.sh $LETTUCE_PARAMS '-t supply1'
	./runtests_local.sh $LETTUCE_PARAMS
    done
done

LETTUCE_PARAMS="${*:2}"
TAG="-t supply2"

#Seconde série de tests Supply : 50 250
#for count in 50 250
for count in 50
do
    export COUNT=$count

    # run the benchmark
    for nb in `seq 1 3`;
    do
    	./runtests_local.sh $LETTUCE_PARAMS '-t supply2'
    done
done

REP_RESULTS="website/performances/$1"

mkdir $REP_RESULTS
cp -R results/* "$REP_RESULTS/"
