"""
This script is a wrapper for runtests.py when running tests under docker in multiple instances at the same time
Script takes these arguments:
    -t/--tags
    -f/--files
    -d/--directory
    -w/--workers

All arguments that specify files to run are considered as union not intersection.

Divided files are printed on stdout

"""

import argparse
import os.path
import re
import numpy
import sys
from jinja2 import Template

BASE_DIR = "meta_features"


def has_tags(file, tags):
    """
    file -> str: file to inspect for tags
    tags -> list: tags to find

    returns True or False
    """

    with open(file, 'r') as f:
        _str = f.read()
        # We want just unique tags
        found_tags = set(re.findall("@(\S*)\s", _str))

    for tag in tags:
        if tag in found_tags:
            return True
    else:
        return False


def split_to_parts(files, workers):
    """
    workers -> int: number of workers
    files -> list: list of files to divide among workers

    returns json with divided files

    """
    results = list()
    for i, file_list in enumerate(numpy.array_split(files, workers)):
        results.append(','.join(list(file_list)))

    template = """
results=()
{% for result in results %}results+=('{{ result.replace("'", "'\\\\''") }}')
{% endfor %}
    """
    tmpl = Template(template)
    return tmpl.render(results=results)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--tags", action="append", dest='tags',
                        help="Specify tags that should be run, use multiple -t to add more tags -t finance -t it etc.;"
                             "tags work as union not intersection")
    parser.add_argument("-d", "--directory", action="append", dest="directories",
                        help="Specify directories of meta_features to run use multiple as -d A -d B")
    parser.add_argument("-f", "--file", action="append", dest="files",
                        help="Specify files to run, multiple files as -f A -f B etc")
    parser.add_argument("-w", "--workers", action="store", dest="workers",
                        help="How many workers we want to user", type=int)
    args = parser.parse_args()

    files_to_run = list()

    # If there is no number of workers specified, we assume that tests are supposed to run in one instance
    if not args.workers:
        args.workers = 1

    if args.tags:
        for path, subdirs, files in os.walk(BASE_DIR):
            for file in files:
                filename, file_ext = os.path.splitext(file)
                if file_ext != ".meta_feature":
                    continue
                file_path = os.path.abspath(os.path.join(path, file))
                if has_tags(file_path, args.tags):
                    files_to_run.append(file_path)

    if args.directories:
        for directory in args.directories:
            if not os.path.isdir(directory):
                print("{} is not a valid directory".format(directory))
                continue
            for path, subdirs, files in os.walk(directory):
                for file in files:
                    filename, file_ext = os.path.splitext(file)
                    if file_ext != ".meta_feature":
                        continue
                    file_path = os.path.abspath(os.path.join(path, file))
                    files_to_run.append(file_path)

    if args.files:
        for file in args.files:
            if not os.path.isfile(file):
                print("{} is not a valid file".format(file))
                continue
            files_to_run.append(os.path.abspath(file))

    if not files_to_run:
        print("No files to run! Exiting...")
        exit(1)

    sys.stdout.write(split_to_parts(files_to_run, args.workers))
