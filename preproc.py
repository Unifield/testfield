# -*- coding: utf-8 -*-

if __name__ == '__main__':
    import os
    import re
    import sys

    class SyntaxException(Exception):
        pass

    if len(sys.argv) != 2:
        sys.stderr.write("Invalid arguments\n")
        sys.stderr.write(" Usage: %s file\n" % sys.argv[0])
        sys.exit(1)


    try:
        with open(sys.argv[1], 'r') as f:

            waiting_lines = [(1, [])]

            for no, line in enumerate(f):

                # is it a macro line?
                cleaned_line = line.strip()

                # Is it a macro line ?
                #   #loop{ENV}
                #   #end

                begin_block = re.match('\s*#begin{(?P<env>\w+)}\s*', cleaned_line)
                end_block = re.match('\s*#end\s*', cleaned_line)

                if begin_block is not None:

                    varname = begin_block.groupdict()['env']

                    if varname not in os.environ:
                        raise SyntaxException("Invalid environment variable: %s" % varname)

                    try:
                        nbvar = int(os.environ[varname])
                    except ValueError as e:
                        raise SyntaxException("Invalid variable value: %s (value= '%s')" % (varname, os.environ[varname]))

                    waiting_lines.append((nbvar, []))

                elif end_block is not None:

                    if len(waiting_lines) <= 1:
                        raise SyntaxException("Invalid end block (line: %d)" % (no+1))

                    last_pos = waiting_lines.pop()

                    to_add = last_pos[0] * last_pos[1]
                    waiting_lines[-1][1].extend(to_add)

                else:
                    waiting_lines[-1][1].append(line)

            assert len(waiting_lines) == 1
            sys.stdout.write(''.join(waiting_lines[0][0] * waiting_lines[0][1]))

    except SyntaxException as e:
        sys.stderr.write('%s\n' % e)

