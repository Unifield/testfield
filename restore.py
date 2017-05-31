
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

    import sys
    import os, os.path
    import tempfile
    import hashlib
    import subprocess

    import credentials as c
    import utils

    FLAG_RESET_VERSION ='--reset-versions'
    FLAG_RESET_SYNC ='--reset-sync'
    FLAG_BAK ='--bak'

    db_address_with_flag = '' if not c.DB_ADDRESS else "-h %s" % c.DB_ADDRESS

    reset_versions = FLAG_RESET_VERSION in sys.argv
    reset_sync = FLAG_RESET_SYNC in sys.argv
    do_bak = FLAG_BAK in sys.argv
    arguments = filter(lambda x : x != FLAG_RESET_VERSION, sys.argv)
    arguments = filter(lambda x : x != FLAG_RESET_SYNC, arguments)
    arguments = filter(lambda x : x != FLAG_BAK, arguments)

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

        os.environ['PGPASSWORD'] = c.DB_PASSWORD

        p1 = subprocess.Popen('psql -v ON_ERROR_STOP=1 -p %d -t %s -U %s %s < %s' % (c.DB_PORT, db_address_with_flag, c.DB_USERNAME, dbname, scriptfile[1]),
                              shell=True,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)
        ret, stderr = p1.communicate()

        try:
            os.unlink(scriptfile[1])
        except OSError:
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

        sync_server_db = False
        to_restore = []

        for filename in os.listdir(environment_dir):
            dbname, _ = os.path.splitext(filename)

            if dbname not in dumps_to_restore and dumps_to_restore:
                continue

            if not dbname:
                raise Exception("No database name in %s" % dbname)

            dbname = utils.prefix_db_name(dbname)
            to_restore.append((dbname, filename))
            if 'SYNC_SERVER' in dbname:
                sync_server_db = dbname

        for dbname, filename in to_restore:

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

            p1 = subprocess.Popen('pg_restore -p %d %s -U %s --no-acl --no-owner -n public -d %s %s' % (c.DB_PORT, db_address_with_flag, c.DB_USERNAME, dbname, path_dump),
                                  shell=True,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)
            ret, stderr = p1.communicate()

            if p1.returncode != 0:
                raise DatabaseException("Unable to restore %s (reason: %s)" % (dbname, stderr))

            run_script(dbname, "UPDATE res_users SET password = '%s' WHERE login = '%s'" % (c.UNIFIELD_PASSWORD, c.UNIFIELD_ADMIN))

            # if it's a sync server we have to update the hardware ids. Otherwise our instances won't synchronise
            ret = run_script(dbname, "select 1 from pg_class where relname='sync_server_entity'")

            if filter(lambda x : x, ret.split('\n')):
                hwid = c.SERVER_HWID or get_hardware_id()
                run_script(dbname, "UPDATE sync_server_entity SET hardware_id = '%s'" % hwid)
                if reset_versions:
                    run_script(dbname, "DELETE FROM sync_server_version WHERE sum NOT IN ('88888888888888888888888888888888', '66f490e4359128c556be7ea2d152e03b')")
            else:
                if not sync_server_db:
                    ret = run_script(dbname, "select database from sync_client_sync_server_connection")
                    other = ret.split('\n')
                    lines = filter(lambda x : x, other)

                    if lines:
                        line = lines[0]
                        pointed_dbname = line.strip()
                        sync_server_db = utils.prefix_db_name(pointed_dbname)

                run_script(dbname, "UPDATE sync_client_sync_server_connection SET database = '%s', host = 'localhost', protocol = 'netrpc_gzip', port = %d" % (sync_server_db, c.NETRPC_PORT))
                if reset_versions:
                    run_script(dbname, "DELETE FROM sync_client_version WHERE sum NOT IN ('88888888888888888888888888888888', '66f490e4359128c556be7ea2d152e03b')")

                if reset_sync:
                    run_script(dbname, "UPDATE ir_model_data SET create_date = '2016-05-24' WHERE create_date > '2016-05-24' OR create_date IS NULL")
                    run_script(dbname, "UPDATE ir_model_data SET last_modification =  CASE WHEN sync_date < last_modification OR sync_date IS NULL THEN TIMESTAMP '2016-05-24 23:00:00' ELSE TIMESTAMP '2016-05-24 01:00:00' END")
                    run_script(dbname, "UPDATE ir_model_data SET sync_date = TIMESTAMP '2016-05-24 12:00:00'")

                #FIXME use the same variable as in steps.py
                #FIXME here we rely on the fact that lettuce and the database run on the same server
                base_dir = os.path.dirname(__file__)
                file_path = os.path.join(base_dir, 'files')
                file_path = os.path.abspath(file_path)

                # this is not safe
                run_script(dbname, "UPDATE backup_config SET name = '%s'" % file_path)
                if do_bak:
                    run_script("postgres", "create database \"%s\" template \"%s\"" % (dbname + "_bak", dbname))

    except (OSError, IOError) as e:
        sys.stderr.write("Unable to access an environment (cause: %s)" % e)
        sys.exit(-1)
    except (DatabaseException, ScriptException) as e:
        sys.stderr.write("Unable to restore the environment (cause: %s)" % e)
        sys.exit(-1)

