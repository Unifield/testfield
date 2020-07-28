#encoding=utf-8

from __future__ import print_function
import credentials

import re
import sys
import shutil
import os
import utils
import credentials
import subprocess


# http://stackoverflow.com/questions/5574702/how-to-print-to-stderr-in-python
def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


FEATURE_DIR = "features"
META_FEATURE_DIR = "meta_features"


class SyntaxException(Exception):
    pass


class DBException(Exception):
    pass


def get_articles(database, count):
    from oerplib import OERP
    oerp = OERP(server=credentials.SRV_ADDRESS, database=database, protocol='xmlrpc', port=credentials.XMLRPC_PORT, version='6.0')
    u = oerp.login(credentials.UNIFIELD_ADMIN, credentials.UNIFIELD_PASSWORD)
    prod_obj = oerp.get('product.product')
    ids = prod_obj.search([('batch_management', '=', False), ('perishable', '=', False),
        ('active', '=', True), '|', ('state', '!=', 'archived'), ('state', '=', False)], 0, count)

    return [{'code': x['default_code'], 'name': x['name']} for x in prod_obj.read(ids, ['default_code', 'name'], { 'lang': 'en_MF' })]


def inject_variable(line, **variables):

    for key, value in variables.iteritems():
        line = line.replace('{{%s}}' % key, value)
    return line


def get_template_lines(template_path):
    """
    Validate template_path and then returns file lines as a list
    """
    if not os.path.isfile(template_path):
        #  Python 2.7 doesn't have FileNotFoundError as built-in, used IOError instead
        raise IOError("{} is not a valid file or is not in the location you gave.".format(template_path))

    file_name, ext = os.path.splitext(template_path)
    if not ext == ".template":
        raise IOError("{} has not proper extension, should be filename.template".format(template_path))

    with open(template_path, 'r') as f:
        return f.readlines()


def run_preprocessor(path):
    with open(path, 'r') as f:

        waiting_lines = [(1, None, [], None)]

        for no, line in enumerate(f):

            # is it a macro line?
            cleaned_line = line.strip()

            iterate_over_with_database = re.match(
                '^\s*#loop{\s*(?P<database>[^} ),]+)\s*,\s*(?P<kindof>[^} ),]+)\s*,\s*(?P<varname>[^} ),]+)\s*}\s*$',
                cleaned_line)
            begin_block_count = re.match('^\s*#begin{\s*(?P<macro>[^}]+)\s*}\s*$', cleaned_line)
            end_block = re.match('\s*#end\s*', cleaned_line)
            template_path = re.match('%%{TEMPLATE:(?P<template>\s*.*)}%%', cleaned_line)

            if iterate_over_with_database is not None:
                values = iterate_over_with_database.groupdict()

                database = utils.prefix_db_name(values['database'])
                varname = values['varname']

                try:
                    if re.match(r'^[0-9]+$', varname):
                        number = int(varname)
                    else:
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

            elif template_path:
                # We get lines from template and add them to waiting lines
                path = template_path.groupdict()['template'].strip()
                template_lines = get_template_lines(path)
                for template_line in template_lines:
                    waiting_lines[-1][2].append(template_line)

            else:
                waiting_lines[-1][2].append(line)

        if len(waiting_lines) != 1:
            raise SyntaxException("A block is not open or is not closed")

        return ''.join(waiting_lines[0][0] * waiting_lines[0][2])


if __name__ == '__main__':
    try:

        import argparse
        parser = argparse.ArgumentParser(description='Run the tests')
        parser.add_argument('-t', type=str, dest="tags", action='store', nargs=1, help='the tag to select')
        parser.add_argument('files', type=str, nargs='*', help='the files to execute')
        args = parser.parse_args()

        if os.path.isdir(FEATURE_DIR):
            shutil.rmtree(FEATURE_DIR)
        os.mkdir(FEATURE_DIR)

        # we have to extract the filenames if necessary (ends with meta_feature or feature)
        #if args.files:
        filename_only = []
        for filename in args.files:
            filename = os.path.basename(filename)
            filename, _ = os.path.splitext(filename)
            filename_only.append(filename)

        # We should used processed file paths - ends with .feature for case that some processing in file is done
        new_args_files_destination = list()

        for dirpath, dirnames, filenames in os.walk(META_FEATURE_DIR):

            # do we have to create the directory?
            relative_path_in_meta = os.path.sep.join(dirpath.split(os.path.sep)[1:])
            if relative_path_in_meta and not os.path.isdir(relative_path_in_meta):
                os.mkdir(os.path.join(FEATURE_DIR, relative_path_in_meta))

            # Which file ends with the extension we have to convert?
            for filename in filenames:

                filename_without_ext, _ = os.path.splitext(filename)

                if filename_without_ext not in filename_only and filename_only:
                    continue


                m = re.match('(?P<filename>.*)\.meta_feature$', filename, re.IGNORECASE)
                if m:
                    from_path = os.path.join(dirpath, filename)
                    new_file_name = '%s.feature' % m.groupdict()['filename']

                    to_path = os.path.join(FEATURE_DIR, relative_path_in_meta, new_file_name)
                    if filename_without_ext in filename_only and filename_only:
                        new_args_files_destination.append(to_path)

                    try:
                        eprint("Converting %s" % new_file_name)

                        content = run_preprocessor(from_path)
                        with open(to_path, 'w') as f:
                            # remove invalid characters due to bad unifield encodings in test instances
                            out = []
                            for a in list(content):
                                if ord(a) in range(128):
                                    out.append(a)
                            f.write(''.join(out))

                    except SyntaxException as e:
                        eprint('SYNTAX FAILURE:%s: %s\n\n' % (filename, e))
                    except DBException as e:
                        eprint('DB FAILURE:%s: %s\n\n' % (filename, e))

        args_found = []

        if args.tags:
            for tt in args.tags:
                for splittt in tt.split(','):
                    args_found += ['-t'] + [splittt]

        if args.files:
            args_found += new_args_files_destination
        
        # we can run lettuce now
        lettuce_cmd = ["lettuce", "--verbosity=3", "--no-color"] + args_found
        eprint("runtests.py calling lettuce: ", lettuce_cmd)
        ret = subprocess.call(lettuce_cmd)
        sys.exit(ret)

    except shutil.Error as e:
        eprint(e)
        sys.exit(-1)
    except (OSError, IOError) as e:
        eprint(e)
        sys.exit(-1)


