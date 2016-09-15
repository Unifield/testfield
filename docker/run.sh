#!/bin/bash

docker pull hectord/autotestfield

EXTRA_PARAM=
if [[ $TESTFIELD_TEST_KEY ]]
then
    EXTRA_PARAM="-e KEY_FETCH=$TESTFIELD_TEST_KEY"
fi

docker run $EXTRA_PARAM --rm --privileged -it -P -p 8080:8080 -v /home/jra/automafield/testfield/docker/output:/output hectord/autotestfield $@

