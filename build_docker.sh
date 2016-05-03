#!/bin/bash

rm docker/requirements.txt
cp requirements.txt docker/

rm -rf docker/input
rm -rf docker/output

mkdir docker/input
mkdir docker/output
mkdir docker/output/benchmarks
mkdir docker/output/tests

cp -R meta_features docker/input/
cp -R instances docker/input/

