#!/bin/bash

for fichier in results/*.csv
do
    FROM_FILE=$fichier
    TO_FILE=${fichier%.csv}.png

    python graph_generator.py $FROM_FILE $TO_FILE
done

