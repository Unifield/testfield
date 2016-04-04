#!/bin/bash



for meta_out in `find . -name "*.meta_feature"`;
do
    META_FEATURE=$meta_out
    FEATURE=`echo $meta_out | sed 's/\.meta_feature$/\.feature/'`

    rm $FEATURE

    python preproc.py $META_FEATURE > $FEATURE;
    
done

lettuce $@


