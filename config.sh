#!/bin/bash

####################################################################
## UNIFIELD (LOCAL CONFIG)
####################################################################

# The HTTP port of Unifield
WEB_PORT=8061
# The XMLRPC port of Unifield (used to synchronize and to build tests)
XMLRPC_PORT=8069

# The credentials used to log into Unifield as administrator
UNIFIELDADMIN=admin
UNIFIELDPASSWORD=admin

# Unifield's address
SERVER_HOST=127.0.0.1

# The hardware ID that will be used to link the databases with the
#  sync server. If it's not available, the current computer's hardware
#  ID will be computed automatically.
SERVER_HWID=

####################################################################
## UNIFIELD (OPTIONAL CONFIG)
####################################################################

# directory name in directory instances/ where the databases are stored
#  they will be restored before each run.
SERVER_ENVNAME=lightweight

# the prefix used to name the databases. If DBPREFIX=YYY, the databases' name
#  will all start with YYY_.
DBPREFIX=''

####################################################################
## UNIFIELD CONFIG (IN DOCKER CONTAINERS ONLY)
####################################################################

## DATABASE credentials/port
DBADDR=$SERVER_HOST
DBPASSWORD=unifield_dev
DBUSERNAME=unifield_dev
DBPORT=5432

NETRPC_PORT=8070

XMLRPCS_PORT=8071

# directory where we store Unifield and its database
SERVER_TMPDIR=/tmp/repo

# the database's path to launch it in the container with faketime
DBPATH=
FORCED_DATE=

# HOMERE password (if available, otherwise, the tests related to Homere will
#  fail everytime)
HOMEREDB=$''

