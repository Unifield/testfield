#!/bin/bash

set -e

echo "Clean up data"
rm -rf files meta_features instances

KEY_FETCH=${KEY_FETCH-vRN2afzfa7bMOXQ}
DIR_FETCH=${DIR_FETCH-tests}

echo "Download the zip file"
wget -O tests.zip https://cloud.msf.org/index.php/s/${KEY_FETCH}/download

echo "Unzip"
unzip tests.zip

mv ${DIR_FETCH}/* .
rm -rf ${DIR_FETCH} tests.zip


