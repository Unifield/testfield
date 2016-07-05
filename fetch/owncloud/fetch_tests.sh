#!/bin/bash

set -e

echo "Clean up data"
rm -rf files meta_features instances

echo "Download the zip file"
wget -O tests.zip https://cloud.msf.org/index.php/s/GqurD9dOcYqlFrl/download

echo "Unzip"
unzip tests.zip

mv testfield_tests/* .
rm -rf testfield_tests tests.zip

