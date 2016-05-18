#!/bin/env python

import owncloud
from credentials import *
import sys

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print "Usage: %s path" % sys.argv[0]
        sys.exit(0)

    oc = owncloud.Client('https://cloud.msf.org/')

    oc.login(OWNCLOUD_USERNAME, OWNCLOUD_PASSWORD)
    oc.get_directory_as_zip('tests', sys.argv[1])

