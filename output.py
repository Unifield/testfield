
from utils import *
from lettuce import *
from selenium import webdriver
import os.path
import datetime
import tempfile

OUTPUT_DIR = 'output/'
TEMPLATES_DIR = 'templates/'

from bottle import SimpleTemplate

class MyPrintscreen(object):

    def __init__(self, filename, steps):
        self.__steps = steps
        self.__filename = filename

    def getSteps(self):
        return self.__steps

    def getFilename(self):
        return self.__filename

    steps = property(getSteps)
    filename = property(getFilename)

def convert_hashes_to_table(hashes):
    import itertools
    str_hashes = list(set(itertools.chain(*map(lambda x : x.keys(), hashes))))
    str_hashes.sort()

    if not ''.join(str_hashes).strip():
        return None

    table = [str_hashes]

    for line in hashes:
        row = []
        for header in str_hashes:
            row.append(line.get(header, ""))
        table.append(row)

    return table

def register_for_printscreen(function):
    def newfonc(step, *arg1, **arg2):
        #FIXME: We will keep the wildcar here. We should try to
        #  figue out a way to "turn it" into something real
        #  when we match it against a web element.
        real_sentence = convert_input(world, step.original_sentence)
        real_table = convert_hashes_to_table(step.hashes)
        world.steps_to_display.append((real_sentence, real_table, step))
        return function(step, *arg1, **arg2)
    return newfonc

def add_printscreen(function):
    def newfonc(step, *arg1, **arg2):
        #FIXME: same as above
        real_sentence = convert_input(world, step.original_sentence)
        real_table = convert_hashes_to_table(step.hashes)
        world.steps_to_display.append((real_sentence, real_table, step))
        write_printscreen(world)
        return function(step, *arg1, **arg2)
    return newfonc

@before.all
def create_website():
    world.scenarios = []
    world.idscenario = 0
    world.idprintscreen = 1

@after.all
def create_real_repport(total):

    path_tpl = os.path.join(TEMPLATES_DIR, "index.tpl")
    with open(path_tpl, 'r') as f:
        content = ''.join(f.xreadlines())

        now = datetime.datetime.now()
        str_date = now.strftime('%m/%d/%Y')

        mytemplate = SimpleTemplate(content)
        content = mytemplate.render(scenarios=world.scenarios, date=str_date)

        path_html = os.path.join(OUTPUT_DIR, "index.html")
        output_index_file = open(path_html, 'w')
        output_index_file.write(content)
        output_index_file.close()

@before.each_scenario
def create_scenario_report(scenario):
    world.time_before = datetime.datetime.now()
    world.printscreen_to_display = []
    world.steps_to_display = []

@after.each_scenario
def write_end_of_section(scenario):

    all_ok = all(map(lambda x : x.passed, scenario.steps))
    filter_passed = sum(map(lambda x : 1 if x.passed else 0, scenario.steps))
    percentage_ok = '%.2f' % (float(filter_passed) / len(scenario.steps) * 100.0)
    time_total = ('%.2f' % timedelta_total_seconds(datetime.datetime.now() - world.time_before)) if all_ok else ''
    index_page = 'index%d.html' % world.idscenario
    tags = scenario.tags

    world.scenarios.append((all_ok, scenario.name, percentage_ok, time_total, index_page, tags))

    # we have to add the steps that haven't been included
    write_printscreen(world)

    path_html = os.path.join(OUTPUT_DIR, index_page)

    path_tpl = os.path.join(TEMPLATES_DIR, "scenario.tpl")
    with open(path_tpl, 'r') as f:
        content = ''.join(f.xreadlines())

        mytemplate = SimpleTemplate(content)
        content = mytemplate.render(printscreens=world.printscreen_to_display, scenario=scenario)

        output_index_file = open(path_html, 'w')
        output_index_file.write(content)
        output_index_file.close()

    world.printscreen_to_display = []

    world.idscenario += 1

def write_printscreen(world):

    if not world.steps_to_display:
        return

    steps_to_print = world.steps_to_display
    world.steps_to_display = []

    filename = "printscreen%d.png" % world.idprintscreen
    path_printscreen = os.path.join(OUTPUT_DIR, filename)
    world.browser.save_screenshot(path_printscreen)
    world.idprintscreen += 1

    world.printscreen_to_display.append(MyPrintscreen(filename, steps_to_print))

