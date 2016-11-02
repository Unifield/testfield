#!/bin/bash

if [ ! -x firefox/firefox ];
then
    echo "Download Firefox v.46"
    wget https://ftp.mozilla.org/pub/firefox/releases/46.0.1/linux-x86_64/en-GB/firefox-46.0.1.tar.bz2 --output-document=/tmp/firefox-46.0.1.tar.bz2 --quiet
    echo "Extract the archive"
    tar -xjf /tmp/firefox-46.0.1.tar.bz2
    rm /tmp/firefox-46.0.1.tar.bz2
    echo "Firefox binaries are now installed in testfield directory"
else
    echo "Firefox binaries are already here"
fi
