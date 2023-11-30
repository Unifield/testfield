#!/usr/bin/env bash

../upgrade-databases.sh
../reset-databases.sh

rm -fr files meta_features
cp -a /home/testing/testfield/files /home/testing/testfield/meta_features .


if [[ -f ../venv-tf/bin/activate ]]; then
        . ../venv-tf/bin/activate
fi

./runtests_local.sh "$@"
mkdir -p website/tests/
mv output website/tests/`date +%Y-%m-%d-%H%M`

