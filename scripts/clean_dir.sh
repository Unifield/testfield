#!/bin/bash

set -e

NBDIR_TO_KEEP=0
PATH_TO_CLEAN=$1

if [[ ! -d $PATH_TO_CLEAN ]]
then
    echo ${1} is not a directory >&2
    exit 1
fi

NB_DIRS=$(ls -rth1 ${PATH_TO_CLEAN} | wc -l)
NB_DIRS_TO_REMOVE=$[ NB_DIRS - NBDIR_TO_KEEP ]

if [[ $NB_DIRS_TO_REMOVE -le 0 ]]
then
    echo No directory has to be removed
    exit 0
fi

for file in $(ls -rth1 ${PATH_TO_CLEAN} | head -$NB_DIRS_TO_REMOVE);
do
    echo Remove \"${file}\";

    rm -rf ${PATH_TO_CLEAN}/${file} &>2 2> /dev/null || {
        echo "Unable to remove ${file}" >&2
    }
done

