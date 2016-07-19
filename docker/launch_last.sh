#!/bin/bash


echo "Commit the image"
docker commit `docker ps -q -l` img_tmp
echo "Launch the image"
echo "  it's possible to start Unifield and the PostgreSQL database if you launched the test"
echo "  with the verb 'setup' and no 'test'"
docker run -i -t --entrypoint=/bin/bash img_tmp

