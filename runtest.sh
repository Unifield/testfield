#!/bin/bash

python runtests.py $@

for fichier in results/*.csv
do
    FROM_FILE=$fichier
    TO_FILE=${fichier%.csv}.png

    python generate.py $FROM_FILE $TO_FILE
done

