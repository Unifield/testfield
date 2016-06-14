#!/bin/bash

set -o errexit

Xvfb :1 -screen 0 1024x768x16 &
export DISPLAY=:1

su testing -c "/home/testing/docker-entrypoint.sh $*"

