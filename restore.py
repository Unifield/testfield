

if __name__ == '__main__':

    import re
    import sys
    import shutil
    import os, os.path
    import tempfile

    from credentials import *

    import sys

    if len(sys.argv) != 2:
        sys.stdout.write("Env name: ")
        env_name = raw_input()
    else:
        env_name= sys.argv[1]
    ENV_DIR = 'instances/'

    # We have to load the environment
    environment_dir = os.path.join(ENV_DIR, env_name)

    if not os.path.isdir(environment_dir):
        print "Invalid environment"
        sys.exit(1)

    def run_script(dbname, script):

        scriptfile = tempfile.mkstemp()
        f = os.fdopen(scriptfile[0], 'w')
        f.write(script)
        f.close()

        os.environ['PGPASSWORD'] = DB_PASSWORD

        ret = os.popen('psql -h %s -U %s %s < %s' % (DB_ADDRESS, DB_USERNAME, dbname, scriptfile[1])).read()

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
            print "Restoring", dbname

            if not dbname:
                raise Exception("No database name in %s" % dbname)

            dbtokill = run_script("postgres", '''
                SELECT 'select pg_terminate_backend(' || procpid || ');'
                FROM pg_stat_activity
                WHERE datname = '%s'
            ''' % dbname)

            names = dbtokill.split('\n')
            killall = '\n'.join(names[2:-3]).strip()

            if killall:
                run_script("postgres", killall)

            run_script("postgres", 'DROP DATABASE IF EXISTS "%s"' % dbname)
            run_script('postgres', 'CREATE DATABASE "%s";' % dbname)
            run_script(dbname, 'DROP EXTENSION IF EXISTS plpgsql;')

            path_dump = os.path.join(environment_dir, filename)
            os.system('pg_restore -h %s -U %s --no-acl --no-owner -d %s %s' % (DB_ADDRESS, DB_USERNAME, dbname, path_dump))

            run_script(dbname, "UPDATE res_users SET password = '%s' WHERE login = '%s'" % (UNIFIELD_PASSWORD, UNIFIELD_ADMIN))

            #FIXME: We have to update the HWID if it's a sync server

    except (OSError, IOError) as e:
        raise Exception("Unable to access an environment (cause: %s)" % e)

