#!/bin/bash

v="$1"
if [ -z "$1" ]; then
	echo "Missing version number."
	exit 1
fi

r=`lsb_release -r -s`
if [ "$r" == "10.04" ]; then
	echo "Ubuntu $r only runs Firefox 45, but FF 45 hangs when driven by Selenium. Use the system Firefox instead."
	exit 1
else
	dl=https://ftp.mozilla.org/pub/firefox/releases/$v/linux-x86_64/en-GB/firefox-$v.tar.bz2
fi

if [ ! -x firefox/firefox ];
then
    echo "Download Firefox $v"
    wget --quiet -O- $dl | tar jxf -
    if [ $? != 0 ]; then
	    exit $?
    fi
    echo "Firefox is now installed in directory firefox"
else
    echo "Firefox is already here"
fi
