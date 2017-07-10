#!/bin/bash

if [ "$1" = "-h" ]; then
	echo "KEY_FETCH=<the key> ./fetch.sh"
	exit 1
fi

set -e

[[ -e .tmp ]] && rm -rf .tmp
mkdir .tmp

echo "Clean up data"
rm -rf files meta_features instances

KEY_FETCH=${KEY_FETCH-tSrHBNFemfKIVuY}

echo "Download the zip file"
out=`date +test-%a.zip`
wget -q -O $out https://cloud.msf.org/index.php/s/${KEY_FETCH}/download
DIRNAME=$(unzip -qql $out | head -n1 | tr -s ' ' | cut -d' ' -f5-)

cp $out .tmp/tests.zip
cd .tmp

echo "Unzip"
unzip tests.zip

cp -R $DIRNAME/instances ../
cp -R $DIRNAME/meta_features ../
cp -R $DIRNAME/files ../

cd ..
rm -rf .tmp

# Save them into a Git repo so that we know what changed and when.
if [ `hostname` = "uf5-hw.unifield.org" -a -d $HOME/precious-data/testfield-input ]; then
	rm -rf testfield-input
	git clone $HOME/precious-data/testfield-input
	rm -rf testfield-input/*
	cp -r meta_features/ files/ instances/ testfield-input/
	cd testfield-input
	git add --all
	git commit -m `date +%Y%m%d-%H%M` || true
	git push origin master
	cd ..
	rm -rf testfield-input
fi

