#!/bin/bash

r=`lsb_release -r -s`
if [ "$r" == "10.04" ]; then
	echo "Ubuntu $r only runs Firefox 45, but FF 45 hangs when driven by Selenium. Use the system Firefox instead."
	exit 1

	# https://support.mozilla.org/en-US/questions/1121133
	#v=45.4.0esr
	#dl=https://download-installer.cdn.mozilla.net/pub/firefox/releases/45.4.0esr/linux-x86_64/en-US/firefox-45.4.0esr.tar.bz2
else
	# v46 is the last version that selenium 2 works with
	v=46.0.1
	dl=https://ftp.mozilla.org/pub/firefox/releases/46.0.1/linux-x86_64/en-GB/firefox-46.0.1.tar.bz2
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
