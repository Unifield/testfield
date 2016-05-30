#!/bin/bash

set -e

echo "Clean up data"
rm -rf files meta_features instances

echo "Download the zip file"
wget -O tests.zip https://cloud.msf.org/index.php/s/vRN2afzfa7bMOXQ/download

echo "Unzip"
unzip tests.zip

mv tests/* .
rm -rf tests tests.zip


