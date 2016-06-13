
from utils import *
from lettuce import *
from selenium import webdriver
import os.path
import datetime
import tempfile

OUTPUT_DIR = 'output/'
TEMPLATES_DIR = 'templates/'

from bottle import SimpleTemplate

class Printscreen(object):

    def __init__(self, filename):
        self.__filename = filename

    def getFilename(self):
        return self.__filename

    def is_error(self):
        raise NotImplementedError

    filename = property(getFilename)

class RegularPrintscreen(Printscreen):

    def __init__(self, filename, steps):
        super(RegularPrintscreen, self).__init__(filename)
        self.__steps = steps

    def is_error(self):
        return False

    def getSteps(self):
        return self.__steps

    steps = property(getSteps)

class ErrorPrintscreen(Printscreen):

    def __init__(self, filename, description):
        super(ErrorPrintscreen, self).__init__(filename)
        self.__description = description

    def is_error(self):
        return True

    def getDescription(self):
        return self.__description

    description = property(getDescription)

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
            value = line.get(header, "")
            value = convert_input(world, value)
            row.append(value)
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

    if not os.path.isdir(OUTPUT_DIR):
        os.mkdir(OUTPUT_DIR)

    world.scenarios = []
    world.idscenario = 0
    world.idprintscreen = 1

@after.all
def create_real_repport(total):

    path_tpl = get_absolute_path(os.path.join(TEMPLATES_DIR, "index.tpl"))

    import collections
    count_by_tag = collections.defaultdict(lambda : 0)

    for scenario in world.scenarios:
        for tag in scenario[5]:
            count_by_tag[tag] += 1
    values = count_by_tag.items()
    values.sort(key=lambda x : x[1])
    values.reverse()
    values = filter(lambda x : x[1] > 1, values)
    alltags = map(lambda x : x[0], values)

    with open(path_tpl, 'r') as f:
        content = ''.join(f.xreadlines())

        mytemplate = SimpleTemplate(content)
        content = mytemplate.render(scenarios=world.scenarios, alltags=alltags)

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

    # we have to add the steps that haven't been included
    write_printscreen(world)

    # we have to add en explanation "why" the scenario has failed
    if not all_ok:
        # we cannot rely on "passed" because it seems that the exception is sometimes attached to
        #  another step
        first_failure = filter(lambda x : x.why, (scenario.background.steps if scenario.background else []) + scenario.steps)[0]
        exception_failure = first_failure.why.exception

        msg_error = str(exception_failure)

        write_errorscreen(world, msg_error)

    world.scenarios.append((all_ok, scenario.name, percentage_ok, time_total, index_page, tags))


    path_html = os.path.join(OUTPUT_DIR, index_page)

    path_tpl = get_absolute_path(os.path.join(TEMPLATES_DIR, "scenario.tpl"))
    with open(path_tpl, 'r') as f:
        content = ''.join(f.xreadlines())

        mytemplate = SimpleTemplate(content)
        _, filename = os.path.split(scenario.described_at.file)
        content = mytemplate.render(printscreens=world.printscreen_to_display, scenario=scenario, filename=filename)

        output_index_file = open(path_html, 'w')
        output_index_file.write(content.encode('ascii', 'ignore'))
        output_index_file.close()

    world.printscreen_to_display = []

    world.idscenario += 1

def get_printscreen(world):

    filename = "printscreen%d.png" % world.idprintscreen
    path_printscreen = os.path.join(OUTPUT_DIR, filename)

    elements = []
    for classattr in ['#body_form', '.db-form', '.loginbox']:
        if classattr[0] == '.':
            elements = get_elements(world.browser, class_attr=classattr[1:])
        elif classattr[0] == '#':
            elements = get_elements(world.browser, id_attr=classattr[1:])
        else:
            assert False

        if elements:
            break

    if elements:
        import tempfile
        filename_tmp = tempfile.mktemp()

        world.browser.save_screenshot(filename_tmp)

        from PIL import Image
        im=Image.open(filename_tmp)
        location = elements[0].location
        size = elements[0].size
        rect = (location['x'], location['y'], location['x'] + size['width'], location['y'] + size['height'])
        new = im.crop(rect)
        new.save(path_printscreen)

        try:
            os.unlink(filename_tmp)
        except (IOError, OSError):
            pass
    else:
        world.browser.save_screenshot(path_printscreen)

    world.idprintscreen += 1

    return filename

def write_errorscreen(world, error_message):

    filename = get_printscreen(world)

    world.printscreen_to_display.append(ErrorPrintscreen(filename, error_message))

def write_printscreen(world):

    if not world.steps_to_display:
        return

    steps_to_print = world.steps_to_display
    world.steps_to_display = []

    filename = get_printscreen(world)

    world.printscreen_to_display.append(RegularPrintscreen(filename, steps_to_print))

@after.all
def save_meta(total):
    path_meta = os.path.join(OUTPUT_DIR, 'meta')
    f = open(path_meta, 'w')
    f.write('name=%s\r\n' % (os.environ['TEST_NAME'] if 'TEST_NAME' in os.environ else 'Unknown'))
    f.write('description=%s\r\n' % (os.environ['TEST_DESCRIPTION'] if 'TEST_DESCRIPTION' in os.environ else 'Unknown'))
    f.write('result=%s\r\n' % ('ok' if total.scenarios_ran == total.scenarios_passed else 'ko'))
    f.write("date=%s\r\n" % datetime.datetime.now().strftime("%Y/%m/%d"))
    f.close()

