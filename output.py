
from lettuce import *
from selenium import webdriver
import os.path
import tempfile

OUTPUT_DIR = 'output/'

@before.all
def create_report():
    path_html = os.path.join(OUTPUT_DIR, "index.html")
    world.output_file = open(path_html, 'w')

    world.output_file.write("<html><head><title>UniField Automatized Tests - Summary</title></head><body>")
    world.output_file.write("<h1>UniField Automatized Tests</h1>")

    world.idprintscreen = 1

@after.all
def write_report(total):
    world.output_file.write("</body></html>")
    world.output_file.close()

@before.each_scenario
def write_title(scenario):
    world.output_file.write("<h2>Test '%s'</h2>" % scenario.name)
    world.output_file.write("<table>")

    world.steps_to_display = []

@after.each_scenario
def write_end_of_section(scenario):
    # we have to add the steps that haven't been included

    write_printscreen(world)

    world.output_file.write("</table>")


@before.each_step
def setup_printscreen(step):
    step.need_printscreen = True
    world.take_printscren_before = True

def write_printscreen(world):

    if not world.steps_to_display:
        return

    # can we merge this step with the previous one?
    world.output_file.write("<tr>")
    world.output_file.write("<td>")

    world.output_file.write("<ul>")
    for sentence in world.steps_to_display:
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

    world.steps_to_display = []

@before.each_step
def add_printscreen(step):

    if not step.need_printscreen:
        return

    if not world.take_printscren_before:
        world.steps_to_display.append(step.original_sentence)
    else:

        world.steps_to_display.append(step.original_sentence)

        write_printscreen(world)

