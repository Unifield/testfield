#encoding=utf-8

if __name__ == '__main__':

    class SyntaxError(Exception):
        pass

    import sys

    if len(sys.argv) != 3:
        print "Usage: %s filename outfile" % os.path.basename(sys.argv[0])
        sys.exit(1)

    filename = sys.argv[1]

    try:
        import os.path
        import itertools
        import collections
        import matplotlib.pyplot as plt

        from matplotlib.legend_handler import HandlerLine2D
    except ImportError as e:
        sys.stderr.write("Error: %s\r\n" % e)
        sys.exit(3)

    try:
        with open(filename, 'r') as f:
            lines = map(lambda x : x.strip(), f.readlines())
            divider = []

            header = lines[0]
            data = lines[1:]

            title = header.split(';')

            if title[0] != 'COUNT':
                raise SyntaxError("No COUNT field in the header")

            xs_s, ys = [], []

            for i in xrange(len(title)-1):
                xs_s.append([])

            for line_number, line in zip(itertools.count(2), data):
                if not line.strip():
                    continue

                values = line.split(';')

                try:
                    y = int(values[0])
                except (ValueError, TypeError) as e:
                    raise SyntaxError("Invalid count value on line %d" % line_number)

                if len(values) != len(title):
                    raise SyntaxError("Invalid number of values on line %d (%d value(s) expected, %d value(s) found)" % (line_number, len(title), len(values)))

                # if the y value already exist we have to add it to the current line
                if y in ys:
                    pos = ys.index(y)
                    divider[pos] += 1
                else:
                    pos = None
                    ys.append(y)
                    divider.append(1)

                for i, value in enumerate(values[1:]):
                    try:
                        value = float(value)
                    except (ValueError, TypeError) as e:
                        raise SyntaxError("Invalid time on line %d" % line_number)

                    if pos is None:
                        xs_s[i].append(value)
                    else:
                        xs_s[i][pos] += value

            all_xs_values = []
            all_ys_values = []

            for xs, name in itertools.izip(xs_s, title[1:]):
                ys_values = list(ys)
                xs_values = map(lambda (x, div) : x / div, zip(xs, divider))

                all_xs_values.extend(xs_values)
                all_ys_values.extend(ys_values)

                suite = zip(ys_values, xs_values)
                suite.sort()

                line1, = plt.plot(map(lambda x : x[0], suite), map(lambda x : x[1], suite), label=name, marker='o')
                #line1, = plt.plot(ys, xs, label=name)

            filename, ext = os.path.splitext(filename.replace('_', ' '))

            plt.axis([0, max(all_ys_values)+1, 0, max(all_xs_values)+2])
            plt.title(filename)
            plt.ylabel("Time [s]")
            plt.xlabel("Number of rows")
            plt.legend(loc=2)

            plt.savefig(sys.argv[2])

    except SyntaxError as e:
        sys.stderr.write("Syntax error in %s: %s\r\n" % (filename, e))
        sys.exit(2)
    except (OSError, IOError) as e:
        sys.stderr.write("IO error in %s: %s\r\n" % (filename, e))
        sys.exit(3)

