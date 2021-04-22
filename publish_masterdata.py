#!/usr/bin/env python

import sys
import os
import credentials
import tempfile
import subprocess
import shutil
import time

target_dump_path = '/home/testing/testfield/instances/lightweight'

if len(sys.argv) > 1:
    credentials.DB_PREFIX = sys.argv[1]
else:
    credentials.DB_PREFIX = 'MASTERDATA'

if not os.path.isdir(target_dump_path):
    print('Path %s does not exist' % target_dump_path)
    sys.exit(1)

from utils import synchronize_instance, prefix_db_name

instance_list = []
sync_name = False
for dumpname in os.listdir(os.path.join(os.path.dirname(sys.argv[0]), 'instances/lightweight/')):
    dbname = dumpname[0:-5]
    if 'SYNC' not in dumpname:
        instance_list.append(dbname)
    else:
        sync_name = dbname

for steps in [1, 2]:
    for instance_name in instance_list:
        print('Sync %s' % prefix_db_name(instance_name))
        synchronize_instance(instance_name)

tempdir = tempfile.mkdtemp()

for instance_name in instance_list + [sync_name]:
    output_dump = os.path.join(tempdir, '%s.dump' % instance_name)
    print('Dump %s to %s' % (prefix_db_name(instance_name), output_dump))
    pg_dump = ['pg_dump', '-p', '%s'%credentials.DB_PORT, '-h', credentials.DB_ADDRESS, '-U', credentials.DB_USERNAME, '-Fc', prefix_db_name(instance_name),  '-f', output_dump]
    subprocess.check_output(pg_dump)

if target_dump_path.endswith('/'):
    target_dump_path = target_dump_path[0:-1]

saved_dir = '%s_%s' % (target_dump_path, time.strftime('%Y%m%d-%H%M%S'))
print('Backup %s to %s' % (target_dump_path, saved_dir))
shutil.move(target_dump_path, saved_dir)
print('Move new dump to %s' % target_dump_path)
shutil.move(tempdir, target_dump_path)
print('Done')
