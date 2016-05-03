#!/bin/bash

rm docker/requirements.txt
cp requirements.txt docker/

rm -rf docker/data

mkdir docker/data
cp -R meta_features docker/data/
cp -R instances docker/data/

