#encoding=utf-8

from bottle import route, run, template, view, redirect, static_file, request
import datetime

PATH_TESTS = './tests/'
PERFORMANCE_TESTS = './performances/'
PAGE_SIZE=15

@route('/')
def index():
    redirect("/tests")

@route('/tests')
@view('tests')
def tests():
    import math

    nbtests = get_number_of_functional_tests(PATH_TESTS)

    try:
        pagenum = int(request.query.page)
    except (ValueError, TypeError) as e:
        pagenum = 1
    pagenum = max(pagenum, 1)


    nbpages = int(math.ceil(float(nbtests) / PAGE_SIZE))
    pages = []

    if pagenum <= 0 or pagenum > nbpages:
        pagenum = 1

    first_page = 0
    last_page = nbpages
    for nopage in xrange(1, nbpages+1):
        pages.append((pagenum == nopage, nopage))

    return dict(tests=get_functional_tests(offset=(pagenum-1)*PAGE_SIZE,
                                            length=PAGE_SIZE,
                                            path_dir=PATH_TESTS),
                first_page=first_page,
                last_page=last_page,
                pages=pages,
                datetime=datetime)

class SyntaxError(Exception):
    pass

def load_file(filename):
    ret = {}

    import itertools

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

            ret[name] = suite

        return ret

def load_meta_file(path):
    import collections
    tests_meta = collections.defaultdict(lambda : "")

    try:
        with open(path, 'r') as f:
            lines = filter(lambda x : x.strip(), f.readlines())
            separator = '='

            for line in lines:
                if separator in line:
                    i = line.index(separator)
                    name = line[:i].strip()
                    value = line[i+1:].strip()
                    tests_meta[name] = value
    except IOError as e:
        print e

    return tests_meta

def get_number_of_functional_tests(path_dir):
    import os
    return len(os.listdir(path_dir))

def get_functional_tests(path_dir, offset, length):
    import os
    import os.path

    tests = []

    elements = sorted(os.listdir(PATH_TESTS), reverse=True)

    for rep_test in elements[offset:offset+length]:
        path_dir = os.path.join(PATH_TESTS, rep_test)
        if os.path.isdir(path_dir):
            path_meta = os.path.join(path_dir, "meta")

            tests_meta = load_meta_file(path_meta)
            tests_meta["id"] = rep_test

            path_version = os.path.join(path_dir, "version")
            if os.path.isfile(path_version):
                tests_meta["version"] = ''.join(map(lambda x : x.strip(), open(path_version, 'r')))

            path_index = os.path.join(path_dir, "index.html")
            tests_meta['valid'] = os.path.isfile(path_index)

            tests.append(tests_meta)

    tests.sort(key=lambda x : x["date"])
    tests.reverse()

    return tests

def get_performance_tests(path_dir, tests=None):
    import re
    import collections
    import os, os.path
    path_dir = os.path.join(PERFORMANCE_TESTS)
    tabular_file = re.compile('^(?P<name>.*)\.csv$')

    versions = set([])
    versions_by_test = collections.defaultdict(lambda : set([]))
    config_by_test_by_version = dict()

    for version_dir in os.listdir(path_dir):
        rep_dir = os.path.join(path_dir, version_dir)
        file_found = False

        if not os.path.isdir(rep_dir):
            continue

        config_by_test = dict()

        for csv_file in os.listdir(rep_dir):
            csv_path = os.path.join(rep_dir, csv_file)

            if not os.path.isfile(csv_path):
                continue

            m = tabular_file.match(csv_file)
            if m:

                try:
                    suites = load_file(csv_path)

                    name = m.groupdict()['name']

                    if tests is not None and name not in tests:
                        continue

                    file_found = True

                    versions_by_test[name].add(version_dir)

                    meta_file = '%s.meta' % name
                    meta_path = os.path.join(rep_dir, meta_file)

                    if name not in config_by_test or not config_by_test[name][1]:
                        config = load_meta_file(meta_path)
                    else:
                        config = config_by_test[name][1]


                    if name in config_by_test:
                        suites.update(**config_by_test[name][0])

                    config_by_test[name] = (suites, config)

                except SyntaxError as e:
                    print e

            if file_found:
                versions.add(version_dir)

        config_by_test_by_version[version_dir] = config_by_test

    return versions_by_test, list(versions), config_by_test_by_version

def get_table(test, metric):

    versions_by_test, versions, config_by_test_by_version = get_performance_tests(PERFORMANCE_TESTS, tests=[test])

    series = {}
    series_dict = {}
    for version in versions:
        series[version] = config_by_test_by_version[version][test][0][metric]

    ys = set([])

    for version, values in series.iteritems():
        ret = {}
        for y, x in values:
            ret[y] = x
            ys.add(y)
        series_dict[version] = ret

    ys = list(ys)
    ys.sort()

    return ys, series_dict

CACHE={}

@route('/performance/<test>/<metric>/img')
@view('performance')
def performance(test, metric):
    import io
    global CACHE

    def timedelta_total_seconds(timedelta):
        return (timedelta.microseconds + 0.0 + (timedelta.seconds + timedelta.days * 24 * 3600) * 10 ** 6) / 10 ** 6

    if (test, metric) in CACHE:

        when, bts = CACHE[test, metric]

        if timedelta_total_seconds(datetime.datetime.now() - when) < 3600 * 3:
            return io.BytesIO(bts)

    ys, series_dict = get_table(test, metric)

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    all_ys_values = set([])
    all_xs_values = set([])

    for name, y_x in series_dict.iteritems():
        values = y_x.items()
        values.sort()

        line1, = plt.plot(map(lambda x : x[0], values), map(lambda x : x[1], values), label=name, marker='o')

        for y in y_x.keys():
            all_ys_values.add(y)
        for x in y_x.values():
            all_xs_values.add(x)

    plt.axis([0, max(all_ys_values) * 1.1, 0, max(all_xs_values) * 1.1])
    plt.title('')
    plt.ylabel("Time [s]")
    plt.xlabel("Number of rows")
    plt.legend(loc=2)

    buf = io.BytesIO()
    plt.savefig(buf)
    buf.seek(0)

    plt.clf()

    bts = buf.read()
    CACHE[test, metric] = (datetime.datetime.now(), bts)

    return io.BytesIO(bts)

@route('/performance/<test>/<metric>')
@view('performance')
def performance(test, metric):

    ys, series_dict = get_table(test, metric)

    headers = ['#'] + series_dict.keys()

    data = []
    for y in ys:
        row = []
        row.append(y)
        for version in series_dict.keys():
            value = series_dict[version].get(y)
            row.append(value)
        data.append(row)

    config_by_test_by_version = get_performance_tests(PERFORMANCE_TESTS, test)[2]

    instances = set([])

    for version in config_by_test_by_version.iteritems():
        t, config = version
        if test in config:
            description = config[test][1]['instances']

            for instance in description.split():
                instances.add(instance)

    instances = list(instances)
    instances.sort()

    return dict(headers=headers, table=data, test=test, metric=metric, instances=instances)

@route('/performances')
@view('performances')
def performances():

    import os.path

    versions_by_test, versions, config_by_test_by_version = get_performance_tests(PERFORMANCE_TESTS)

    return dict(versions=versions, versions_by_test=versions_by_test, config_by_test_by_version=config_by_test_by_version)

@route(r'/test/<name>/<filename:re:.*\.html>')
@view('test')
def test(name, filename):
    import os.path

    path_dir = os.path.join(PATH_TESTS, name)
    path_index = os.path.join(path_dir, filename)

    if not os.path.isdir(path_dir) or not os.path.isfile(path_index):
        return dict(error="Unknown test: %s" % name, fichier=None)

    with open(path_index, 'r') as f:
        fichier = ''.join(f.readlines())

    return dict(error=None, fichier=fichier, title=name)

@route(r'/test/<name>/<filename:re:.*(\.png|\.log)>')
def test(name, filename):
    return static_file(filename, root='tests/' + name)

@route('/static/<path:path>')
def callback(path):
    return static_file(path, root='static/')

if __name__ == '__main__':
    run(host='0.0.0.0', port=8080)



