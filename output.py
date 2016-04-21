
from utils import *
from lettuce import *
from selenium import webdriver
import os.path
import datetime
import tempfile

OUTPUT_DIR = 'output/'
TEMPLATES_DIR = 'templates/'

from bottle import SimpleTemplate

def register_for_printscreen(function):
    def newfonc(step, *arg1, **arg2):
        world.steps_to_display.append(step.original_sentence)
        return function(step, *arg1, **arg2)
    return newfonc

def add_printscreen(function):
    def newfonc(step, *arg1, **arg2):
        world.steps_to_display.append(step.original_sentence)
        write_printscreen(world)
        return function(step, *arg1, **arg2)
    return newfonc

@before.all
def create_website():
    world.scenarios = []
    world.idscenario = 0
    world.idprintscreen = 1

@before.each_scenario
def save_time(scenario):
    world.time_before = datetime.datetime.now()

@after.each_scenario
def after_scenario(scenario):
    all_ok = all(map(lambda x : x.passed, scenario.steps))
    filter_passed = sum(map(lambda x : 1 if x.passed else 0, scenario.steps))
    percentage_ok = '%.2f' % (float(filter_passed) / len(scenario.steps) * 100.0)
    time_total = ('%.2f' % timedelta_total_seconds(datetime.datetime.now() - world.time_before)) if all_ok else ''
    index_page = 'index%d.html' % world.idscenario

    world.scenarios.append((all_ok, scenario.name, percentage_ok, time_total, index_page))
    world.idscenario += 1

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

    path_html = os.path.join(OUTPUT_DIR, "index%d.html" % world.idscenario)
    world.output_file = open(path_html, 'w')

    world.output_file.write("<html><head><title>%s</title></head><body>" % scenario.name)
    world.output_file.write("<h1>%s</h1>" % scenario.name)

    world.output_file.write("<table>")

    world.steps_to_display = []

@after.each_scenario
def write_end_of_section(scenario):
    # we have to add the steps that haven't been included
    write_printscreen(world)

    world.output_file.write("</table>")
    world.output_file.write("</body></html>")
    world.output_file.close()

def write_printscreen(world):

    if not world.steps_to_display:
        return

    steps_to_print = world.steps_to_display
    world.steps_to_display = []

    # can we merge this step with the previous one?
    world.output_file.write("<tr>")
    world.output_file.write("<td>")

    world.output_file.write("<ul>")
    for sentence in steps_to_print:
        world.output_file.write("<li>")
        world.output_file.write(sentence)
        world.output_file.write("</li>")
    world.output_file.write("</ul>")

    world.output_file.write("</td>")

    filename = "printscreen%d.png" % world.idprintscreen

    path_printscreen = os.path.join(OUTPUT_DIR, filename)
    world.browser.save_screenshot(path_printscreen)

    world.idprintscreen += 1

    world.output_file.write("<td><img src='%s' width='400px'></td>" % filename)
    world.output_file.write("</tr>")

