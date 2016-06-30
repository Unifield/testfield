
if __name__ == '__main__':

    def get_hardware_id():
            mac = []
            if sys.platform == 'win32':
                for line in os.popen("ipconfig /all"):
                    if line.lstrip().startswith('Physical Address'):
                        mac.append(line.split(':')[1].strip().replace('-',':'))
            else:
                for line in os.popen("/sbin/ifconfig"):
                    if line.find('Ether') > -1:
                        mac.append(line.split()[4])
            mac.sort()
            hw_hash = hashlib.md5(''.join(mac)).hexdigest()
            return hw_hash

    import re
    import sys
    import shutil
    import os, os.path
    import tempfile
    import hashlib
    import subprocess

    from credentials import *
    from utils import *

    FLAG_RESET_VERSION ='--reset-versions'

    db_address_with_flag = '' if not DB_ADDRESS else "-h %s" % DB_ADDRESS

    reset_versions = FLAG_RESET_VERSION in sys.argv
    arguments = filter(lambda x : x != FLAG_RESET_VERSION, sys.argv)

    if len(arguments) == 1:
        sys.stdout.write("Env name: ")
        env_name = raw_input()
    else:
        env_name= arguments[1]
    ENV_DIR = 'instances/'

    # We have to load the environment
    environment_dir = os.path.join(ENV_DIR, env_name)

    dumps_to_restore = arguments[2:] if len(arguments) > 2 else []

    if not os.path.isdir(environment_dir):
        print "Invalid environment"
        sys.exit(1)

    class DatabaseException(Exception):
        pass
    class ScriptException(Exception):
        pass

    def run_script(dbname, script):

        scriptfile = tempfile.mkstemp()
        f = os.fdopen(scriptfile[0], 'w')
        f.write(script)
        f.close()

        os.environ['PGPASSWORD'] = DB_PASSWORD

        p1 = subprocess.Popen('psql -v ON_ERROR_STOP=1 -p %d -t %s -U %s %s < %s' % (DB_PORT, db_address_with_flag, DB_USERNAME, dbname, scriptfile[1]),
                              shell=True,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)
        ret, stderr = p1.communicate()

        try:
            os.unlink(scriptfile[1])
        except OSError as e:
            pass

        code = p1.returncode

        if code == 3:
            raise ScriptException("Unable to run '%s'\nSTDERR: %s" % (script, stderr or ''))
        if code != 0:
            raise DatabaseException("Unable to run '%s' because of the database\nSTDERR: %s" % (script, stderr or ''))

        return ret

    try:
        if os.path.isfile(environment_dir):
            raise Exception("%s is a file, not a directory" % environment_dir)
        elif not os.path.isdir(environment_dir):
            raise Exception("%s is not a valid directory" % environment_dir)

        for filename in os.listdir(environment_dir):
            dbname, _ = os.path.splitext(filename)

            if dbname not in dumps_to_restore and dumps_to_restore:
                continue

            if not dbname:
                raise Exception("No database name in %s" % dbname)

            dbname = prefix_db_name(dbname)

            print "Restoring", dbname

            kill_successful = False
            kill_exception = None

            for procname in ['pid', 'procpid']:
                try:
                    dbtokill = run_script("postgres", '''
                        SELECT 'select pg_terminate_backend(' || %s || ');'
                        FROM pg_stat_activity
                        WHERE datname = '%s'
                    ''' % (procname, dbname))

                    names = dbtokill.split('\n')
                    killall = '\n'.join(filter(lambda x : x, names)).strip()

                    if killall:
                        run_script("postgres", killall)
                    kill_successful = True
                except ScriptException as e:
                    kill_exception = e

            if not kill_successful:
                raise kill_exception or Exception("Cannot drop the previous databases")

            run_script("postgres", 'DROP DATABASE IF EXISTS "%s"' % dbname)
            run_script('postgres', 'CREATE DATABASE "%s";' % dbname)
            try:
                run_script(dbname, 'DROP EXTENSION IF EXISTS plpgsql;')
            except ScriptException:
                # sometimes this extension already exist in the DB and in the dump.
                #  We have to remove it before importing the DB otherwise we will get errors
                pass
            try:
                run_script(dbname, 'DROP LANGUAGE plpgsql;')
            except ScriptException:
                pass

            path_dump = os.path.join(environment_dir, filename)

            p1 = subprocess.Popen('pg_restore -p %d %s -U %s --no-acl --no-owner -d %s %s' % (DB_PORT, db_address_with_flag, DB_USERNAME, dbname, path_dump),
                                  shell=True,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)
            ret, stderr = p1.communicate()

            if p1.returncode != 0:
                raise DatabaseException("Unable to restore %s (reason: %s)" % (dbname, stderr))

            run_script(dbname, "UPDATE res_users SET password = '%s' WHERE login = '%s'" % (UNIFIELD_PASSWORD, UNIFIELD_ADMIN))

            # if it's a sync server we have to update the hardware ids. Otherwise our instances won't synchronise
            ret = run_script(dbname, "select 1 from pg_class where relname='sync_server_entity'")

            if filter(lambda x : x, ret.split('\n')):
                hwid = get_hardware_id()
                run_script(dbname, "UPDATE sync_server_entity SET hardware_id = '%s'" % hwid)
                if reset_versions:
                    run_script(dbname, "DELETE FROM sync_server_version WHERE sum NOT IN ('88888888888888888888888888888888', '66f490e4359128c556be7ea2d152e03b')")
            else:
                ret = run_script(dbname, "select database from sync_client_sync_server_connection")
                other = ret.split('\n')
                lines = filter(lambda x : x, other)

                if lines:
                    line = lines[0]
                    pointed_dbname = line.strip()
                    new_name = prefix_db_name(pointed_dbname)

                    run_script(dbname, "UPDATE sync_client_sync_server_connection SET database = '%s', host = 'localhost', protocol = 'netrpc_gzip', port = %d" % (new_name, NETRPC_PORT))
                if reset_versions:
                    run_script(dbname, "DELETE FROM sync_client_version WHERE sum NOT IN ('88888888888888888888888888888888', '66f490e4359128c556be7ea2d152e03b')")

                #FIXME use the same ariable as in steps.py
                #FIXME here we rely on the fact that lettuce and the database run on the same server
                FILE_DIR = 'files'
                base_dir = os.path.dirname(__file__)
                file_path = os.path.join(base_dir, FILE_DIR)
                file_path = os.path.abspath(file_path)

                # this is not safe
                run_script(dbname, "UPDATE backup_config SET name = '%s'" % file_path)

    except (OSError, IOError) as e:
        sys.stderr.write("Unable to access an environment (cause: %s)" % e)
        sys.exit(-1)
    except (DatabaseException, ScriptException) as e:
        sys.stderr.write("Unable to restore the environment (cause: %s)" % e)
        sys.exit(-1)

