#!/bin/bash

export LANG=C.UTF-8

set -o errexit
set -o pipefail

git clone https://github.com/hectord/testfield.git && cd testfield

cp -R /data/* .

chmod +x run.sh

./run.sh $@


