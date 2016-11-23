#!/bin/bash

mkdir -p output/tests
mkdir -p output/benchmarks

echo "#!/bin/bash

sudo docker pull unifield/autotestfield

EXTRA_PARAM=
if [[ \$TESTFIELD_TEST_KEY ]]
then
    EXTRA_PARAM=\"-e KEY_FETCH=\$TESTFIELD_TEST_KEY\"
fi

sudo docker run \$EXTRA_PARAM --rm --privileged -it -P -p 8080:8080 -v `pwd`/output:/output hectord/autotestfield \$@
" > run.sh

sudo chmod +x run.sh

