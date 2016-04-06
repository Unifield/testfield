#!/bin/bash

. credentials.sh

ENVNAME=$1
SERVERNAME=$2

for FILENAME in `find instances/$ENVNAME -name *.dump`;
do
    F_WITHOUT_EXTENSION=${FILENAME%.dump}
    DBNAME=${F_WITHOUT_EXTENSION##*/}

    echo Restoring $DBNAME

    echo DROP DATABASE IF EXISTS \"$DBNAME\" | psql -U $USERNAME  -h $SERVERNAME postgres > /dev/null
    echo CREATE DATABASE \"$DBNAME\" | psql -U $USERNAME  -h $SERVERNAME postgres > /dev/null

    pg_restore -h $SERVERNAME -U $USERNAME -d $DBNAME --no-owner --no-acl $FILENAME

done

