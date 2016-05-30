#encoding=utf-8

from credentials import *

import re
import sys
import shutil
import os, os.path
import utils

FEATURE_DIR = "features"
META_FEATURE_DIR = "meta_features"

class SyntaxException(Exception):
    pass

class DBException(Exception):
    pass

def get_sql_query(database, sqlquery):
    import psycopg2
    import psycopg2.extras

    try:
        conn = psycopg2.connect(
            database=database,
            user=DB_USERNAME,
            password=DB_PASSWORD,
            port=DB_PORT,
            host=DB_ADDRESS
        )
        cr = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cr.execute(sqlquery)
        return cr.fetchall()
    except psycopg2.OperationalError as e:
        raise DBException("Cannot reach the database (reason: %s)" % e)

def get_articles(database, count):
    return get_sql_query(database, '''
    SELECT default_code AS CODE, name_template AS NAME
    FROM product_product INNER JOIN product_template ON product_tmpl_id = product_template.id
    WHERE batch_management = 'f' AND perishable = 'f' AND active = 't' AND (state IS NULL OR state <> 4)
    LIMIT %d''' % count)

def inject_variable(line, **variables):

    for key, value in variables.iteritems():
        line = line.replace('{{%s}}' % key, value)
    return line

def run_preprocessor(path):
    with open(path, 'r') as f:

        waiting_lines = [(1, None, [], None)]

        for no, line in enumerate(f):

            # is it a macro line?
            cleaned_line = line.strip()

            iterate_over_without_database = re.match('^\s*#loop{\s*(?P<kindof>[^} ),]+)\s*,\s*(?P<varname>[^} ),]+)\s*}\s*$', cleaned_line)
            iterate_over_with_database = re.match('^\s*#loop{\s*(?P<database>[^} ),]+)\s*,\s*(?P<kindof>[^} ),]+)\s*,\s*(?P<varname>[^} ),]+)\s*}\s*$', cleaned_line)
            begin_block_count = re.match('^\s*#begin{\s*(?P<macro>[^}]+)\s*}\s*$', cleaned_line)
            end_block = re.match('\s*#end\s*', cleaned_line)

            if iterate_over_without_database is not None or iterate_over_with_database is not None:
                values = (iterate_over_without_database or iterate_over_with_database).groupdict()

                if iterate_over_without_database is not None:
                    database = utils.prefix_db_name(DB_NAME)
                else:
                    database = utils.prefix_db_name(values['database'])
                varname = values['varname']

                try:
                    number = int(os.environ[varname])
                except ValueError as e:
                    raise SyntaxException("Invalid variable value: %s (value= '%s')" % (varname, os.environ[varname]))
                kindof = values['kindof'].upper()

                assert kindof in ["PRODUCTS"]
                waiting_lines.append((1, None, [], get_articles(database, number)))

            elif begin_block_count is not None:

                varname = begin_block_count.groupdict()['macro']

                # do we have to iterate over values?
                if ',' in varname:
                    variables = varname.split(',')

                    myvar = variables[0].strip()
                    values = map(lambda x : x.strip(), variables[1:])

                    waiting_lines.append((1, (myvar, values), [], None))
                else:
                    if varname not in os.environ:
                        raise SyntaxException("Invalid environment variable: %s" % varname)

                    try:
                        nbvar = int(os.environ[varname])
                    except ValueError as e:
                        raise SyntaxException("Invalid variable value: %s (value= '%s')" % (varname, os.environ[varname]))

                    waiting_lines.append((nbvar, None, [], None))

            elif end_block is not None:

                if len(waiting_lines) <= 1:
                    raise SyntaxException("Invalid end block (line: %d)" % (no+1))

                nbvars, envs, lines, variables = waiting_lines.pop()

                to_add = nbvars * lines

                # we have to add the variable names
                if envs is not None:
                    to_add_converted = []
                    var = envs[0]

                    to_add_converted = []
                    for var_value in envs[1]:
                        for line in to_add:
                            to_add_converted.append(inject_variable(line, **{var: var_value}))

                    to_add = to_add_converted


                if variables is not None:
                    to_add_with_variables = []
                    for varset in variables:
                        to_add_with_variables.extend([inject_variable(l, **varset) for l in to_add])
                else:
                    to_add_with_variables = to_add

                waiting_lines[-1][2].extend(to_add_with_variables)

            else:
                waiting_lines[-1][2].append(line)

        if len(waiting_lines) != 1:
            raise SyntaxException("A block is not open or is not closed")

        return ''.join(waiting_lines[0][0] * waiting_lines[0][2])

if __name__ == '__main__':
    try:
        if os.path.isdir(FEATURE_DIR):
            shutil.rmtree(FEATURE_DIR)
        os.mkdir(FEATURE_DIR)

        for dirpath, dirnames, filenames in os.walk(META_FEATURE_DIR):

            # do we have to create the directory?
            relative_path_in_meta = os.path.sep.join(dirpath.split(os.path.sep)[1:])
            if relative_path_in_meta and not os.path.isdir(relative_path_in_meta):
                os.mkdir(os.path.join(FEATURE_DIR, relative_path_in_meta))

            # Which file ends with the extension we have to convert?
            for filename in filenames:
                m = re.match('(?P<filename>.*)\.meta_feature$', filename, re.IGNORECASE)
                if m:
                    from_path = os.path.join(dirpath, filename)
                    new_file_name = '%s.feature' % m.groupdict()['filename']

                    to_path = os.path.join(FEATURE_DIR, relative_path_in_meta, new_file_name)

                    try:
                        print "Converting %s" % new_file_name

                        content = run_preprocessor(from_path)

                        f = open(to_path, 'w')
                        f.write(content)
                        f.close()

                    except SyntaxException as e:
                        sys.stderr.write('SYNTAX FAILURE:%s: %s\n\n' % (filename, e))
                    except DBException as e:
                        sys.stderr.write('DB FAILURE:%s: %s\n\n' % (filename, e))

        # we can run lettuce now
        import subprocess
        ret = subprocess.call(["lettuce"] + sys.argv[1:])

        sys.exit(ret)

    except shutil.Error as e:
        sys.stderr.write(e)
        sys.exit(-1)
    except (OSError, IOError) as e:
        sys.stderr.write(str(e))
        sys.exit(-1)


