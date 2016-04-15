# -*- coding: utf-8 -*-

from credentials import *

if __name__ == '__main__':
    import os
    import re
    import sys

    def get_sql_query(sqlquery):
        import psycopg2
        import psycopg2.extras

        conn = psycopg2.connect("host=%s dbname=%s user=%s password=%s" % (DB_ADDRESS, DB_NAME, DB_USERNAME, DB_PASSWORD))
        cr = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cr.execute(sqlquery)
        return cr.fetchall()

    def get_articles(count):
        return get_sql_query("SELECT default_code AS CODE, name_template AS NAME FROM product_product WHERE batch_management = 'f' AND perishable = 'f' AND active = 't' LIMIT %d" % count)

    def inject_variable(line, **variables):

        for key, value in variables.iteritems():
            line = line.replace('{{%s}}' % key, value)
        return line

    class SyntaxException(Exception):
        pass

    if len(sys.argv) != 2:
        sys.stderr.write("Invalid arguments\n")
        sys.stderr.write(" Usage: %s file\n" % sys.argv[0])
        sys.exit(1)


    try:
        with open(sys.argv[1], 'r') as f:

            waiting_lines = [(1, None, [], None)]

            for no, line in enumerate(f):

                # is it a macro line?
                cleaned_line = line.strip()


                iterate_over = re.match('^\s*#loop{\s*(?P<kindof>[^} ),]+)\s*,\s*(?P<varname>[^} ),]+)\s*}\s*$', cleaned_line)
                begin_block_count = re.match('^\s*#begin{\s*(?P<macro>[^}]+)\s*}\s*$', cleaned_line)
                end_block = re.match('\s*#end\s*', cleaned_line)

                if iterate_over is not None:
                    values = iterate_over.groupdict()
                    varname = values['varname']

                    try:
                        number = int(os.environ[varname])
                    except ValueError as e:
                        raise SyntaxException("Invalid variable value: %s (value= '%s')" % (varname, os.environ[varname]))
                    kindof = values['kindof'].upper()

                    assert kindof in ["PRODUCTS"]
                    waiting_lines.append((1, None, [], get_articles(number)))

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
            # We know that the last block is not about a macro
            sys.stdout.write(''.join(waiting_lines[0][0] * waiting_lines[0][2]))

    except SyntaxException as e:
        sys.stderr.write('%s\n' % e)

