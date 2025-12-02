#!/usr/bin/env bash

cd "$(dirname "$0")"

RBTools/upgrade-databases.sh
RBTools/reset-databases.sh

rm -fr files meta_features
cp -a /home/testing/testfield/files /home/testing/testfield/meta_features .


if [[ -f ~/venv-tf/bin/activate ]]; then
        . ~/venv-tf/bin/activate
fi

export TIME_BEFORE_FAILURE=120

./runtests_local.sh "$@"
mkdir -p website/tests/
./scripts/start_unifield.sh -d ../ version src > output/version
mv output website/tests/`date +%Y-%m-%d-%H%M`
rm -f ~/DUMPS/*
