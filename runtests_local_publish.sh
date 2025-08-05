#!/usr/bin/env bash

if [[ -f ../venv-tf/bin/activate ]]; then
        . ../venv-tf/bin/activate
fi

./runtests_local.sh "$@"
./scripts/start_unifield.sh -d ../ version src > output/version
mkdir -p website/tests/
mv output website/tests/`date +%Y-%m-%d-%H%M`

