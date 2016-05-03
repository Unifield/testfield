
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

    from credentials import *

    import sys

    FLAG_RESET_VERSION ='--reset-versions'

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

    def run_script(dbname, script):

        scriptfile = tempfile.mkstemp()
        f = os.fdopen(scriptfile[0], 'w')
        f.write(script)
        f.close()

        os.environ['PGPASSWORD'] = DB_PASSWORD

        pipe_stderr = "2> /dev/null" if sys.platform != 'win32' else ""
        ret = os.popen('psql -p %d -t -h %s -U %s %s %s < %s' % (DB_PORT, DB_ADDRESS, DB_USERNAME, dbname, pipe_stderr, scriptfile[1])).read()

        try:
            os.unlink(scriptfile[1])
        except OSError as e:
            pass

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

            print "Restoring", dbname

            if not dbname:
                raise Exception("No database name in %s" % dbname)


            for procname in ['pid', 'procpid']:
                dbtokill = run_script("postgres", '''
                    SELECT 'select pg_terminate_backend(' || %s || ');'
                    FROM pg_stat_activity
                    WHERE datname = '%s'
                ''' % (procname, dbname))

                names = dbtokill.split('\n')
                killall = '\n'.join(filter(lambda x : x, names)).strip()

                if killall:
                    run_script("postgres", killall)

            run_script("postgres", 'DROP DATABASE IF EXISTS "%s"' % dbname)
            run_script('postgres', 'CREATE DATABASE "%s";' % dbname)
            #run_script(dbname, 'DROP EXTENSION IF EXISTS plpgsql;')

            path_dump = os.path.join(environment_dir, filename)
            os.system('pg_restore -p %d -h %s -U %s --no-acl --no-owner -d %s %s' % (DB_PORT, DB_ADDRESS, DB_USERNAME, dbname, path_dump))

            run_script(dbname, "UPDATE res_users SET password = '%s' WHERE login = '%s'" % (UNIFIELD_PASSWORD, UNIFIELD_ADMIN))

            # if it's a sync server we have to update the hardware ids. Otherwise our instances won't synchronise
            ret = run_script(dbname, "select 1 from pg_class where relname='sync_server_entity'")

            if filter(lambda x : x, ret.split('\n')):
                hwid = get_hardware_id()
                run_script(dbname, "UPDATE sync_server_entity SET hardware_id = '%s'" % hwid)
                if reset_versions:
                    run_script(dbname, "DELETE FROM sync_server_version WHERE sum NOT IN ('88888888888888888888888888888888', '66f490e4359128c556be7ea2d152e03b')")
            else:
                run_script(dbname, "UPDATE sync_client_sync_server_connection SET host = 'localhost', protocol = 'netrpc_gzip', port = %d" % NETRPC_PORT)
                if reset_versions:
                    run_script(dbname, "DELETE FROM sync_client_version WHERE sum NOT IN ('88888888888888888888888888888888', '66f490e4359128c556be7ea2d152e03b')")

    except (OSError, IOError) as e:
        raise Exception("Unable to access an environment (cause: %s)" % e)

