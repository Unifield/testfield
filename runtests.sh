#!/bin/bash

rm -rf features


for dir in `find meta_features/ -type d`;
do
    NEWDIR=`echo $dir | sed 's/^meta_features/features/'`
    mkdir $NEWDIR 2> /dev/null
done

for meta_out in `find meta_features/ -name "*.meta_feature"`;
do
    META_FEATURE=$meta_out
    FEATURE=`echo $meta_out | sed 's/^meta_features/features/' | sed 's/\.meta_feature$/\.feature/'`

    python preproc.py $META_FEATURE > $FEATURE;
done

lettuce $@

