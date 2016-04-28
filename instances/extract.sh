#!/bin/bash

for file in *.dump;
do
    DATABASE=${file%%.dump}

    echo Exporting $DATABASE
    /usr/lib/postgresql/8.4/bin/pg_dump --format=c --no-owner -f ../$DATABASE.dump --username=unifield_dev --host=localhost --port=5433 $DATABASE
done

