# -*- coding: utf-8 -*-

if __name__ == '__main__':
    import os
    import re
    import sys

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

            waiting_lines = [(1, None, [])]

            for no, line in enumerate(f):

                # is it a macro line?
                cleaned_line = line.strip()

                begin_block_count = re.match('^\s*#begin{\s*(?P<macro>[^}]+)\s*}\s*$', cleaned_line)
                end_block = re.match('\s*#end\s*', cleaned_line)

                if begin_block_count is not None:

                    varname = begin_block_count.groupdict()['macro']

                    if ',' in varname:
                        variables = varname.split(',')

                        myvar = variables[0].strip()
                        values = map(lambda x : x.strip(), variables[1:])

                        waiting_lines.append((1, (myvar, values), []))
                    else:
                        if varname not in os.environ:
                            raise SyntaxException("Invalid environment variable: %s" % varname)

                        try:
                            nbvar = int(os.environ[varname])
                        except ValueError as e:
                            raise SyntaxException("Invalid variable value: %s (value= '%s')" % (varname, os.environ[varname]))

                        waiting_lines.append((nbvar, None, []))

                elif end_block is not None:

                    if len(waiting_lines) <= 1:
                        raise SyntaxException("Invalid end block (line: %d)" % (no+1))

                    nbvars, envs, lines = waiting_lines.pop()

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

                    waiting_lines[-1][2].extend(to_add)

                else:
                    waiting_lines[-1][2].append(line)

            if len(waiting_lines) != 1:
                raise SyntaxException("A block is not open or is not closed")
            # We know that the last block is not about a macro
            sys.stdout.write(''.join(waiting_lines[0][0] * waiting_lines[0][2]))

    except SyntaxException as e:
        sys.stderr.write('%s\n' % e)

