#!/bin/bash

set -e

echo "Clean up data"
rm -rf files meta_features instances

echo "Download the zip file"
python fetch/owncloud/download_cloud.py tests.zip
echo "Unzip"
unzip tests.zip

mv tests/* .
rm -rf tests tests.zip


