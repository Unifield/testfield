#!/bin/bash

set -o errexit

Xvfb :1 -screen 0 1024x768x16 &
export DISPLAY=:1

chmod -R 777 /output
chown -R testing:testing /output

su testing -c "/home/testing/docker-entrypoint.sh $*"


