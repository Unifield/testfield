#!/bin/bash

set -e

[[ -e .tmp ]] && rm -rf .tmp
mkdir .tmp

echo "Clean up data"
rm -rf files meta_features instances

KEY_FETCH=${KEY_FETCH-vRN2afzfa7bMOXQ}

echo "Download the zip file"
wget -O tests.zip https://cloud.msf.org/index.php/s/${KEY_FETCH}/download
DIRNAME=$(unzip -qql tests.zip | head -n1 | tr -s ' ' | cut -d' ' -f5-)

mv tests.zip .tmp/
cd .tmp

echo "Unzip"
unzip tests.zip

cp -R $DIRNAME/* ../

cd ..
rm -rf .tmp

