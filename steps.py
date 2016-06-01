#FIXME: The resolution sometimes hides the controls (if it's at the far right). This is also the case on my laptop
# The version I use at the job is 2.48.0. It doesn't have this issue.
from credentials import *

import output
from lettuce import *
from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException, ElementNotVisibleException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from utils import *
import datetime
import os
import os.path
import re
import tempfile

RESULTS_DIR = 'results/'
ENV_DIR = 'instances/'
FILE_DIR = 'files'

RUN_NUMBER_FILE = 'run'

# Selenium management {%{
@before.all
def connect_to_db():

    #WARNING: we need firefox at least Firefox 43. Otherwise, AJAX call seem to be asynchronous
    from selenium.webdriver.firefox.options import Options
    from selenium.webdriver.firefox.firefox_binary import FirefoxBinary

    # /Applications/Firefox.app/Contents/MacOS/firefox
    #world.browser = webdriver.Firefox(firefox_binary=FirefoxBinary('/Users/sblanc/Desktop/msf/testfield/bin/firefox2/main'))

    world.browser = webdriver.Firefox()
    #world.browser = webdriver.PhantomJS()
    #world.browser = webdriver.Chrome()

    TIME_BEFORE_FAILURE = get_TIME_BEFORE_FAILURE()
    if TIME_BEFORE_FAILURE is not None:
        world.browser.set_page_load_timeout(TIME_BEFORE_FAILURE)
        world.browser.set_script_timeout(TIME_BEFORE_FAILURE)

    world.browser.set_window_size(1600, 1200)
    world.nbframes = 0

    world.durations = {}

    mkp = get_absolute_path("monkeypatch.js")
    with open(mkp) as f:
        world.monkeypatch = '\r\n'.join(f.readlines())

    world.nofailure = 0

    # we have to save the files in the directory to remove those who are not
    #  useful anymore
    base_dir = os.path.dirname(__file__)
    file_path = os.path.join(base_dir, FILE_DIR)
    world.files_before = os.listdir(file_path)

    world.logged_in = False
    world.must_fail = None

    def incr_func(param):
        m = re.search('\d+$', param)
        if m is None:
            return param
        number = m.group()
        new_number = '%%0%sd' % len(number) % (int(number) + 1)
        return param[:-len(number)] + new_number

    world.FUNCTIONS = {'INCR': incr_func}


# Dirty hack to display an error message when a step goes wrong in the background {%{
@before.each_background
def do_not_crash(background):
    world.must_fail = None

@after.each_background
def cancel_background(background, results):
    if len(background.steps) != len(results):
        # we have to check what's the exception to reraise it (we don't want to fail silently)
        for step in background.steps:
            if step.why is not None and step.why.exception is not None:
                world.must_fail = step.why.exception
                break
        else:
            world.must_fail = Exception("Unknown error while executing the background")

@before.each_step
def fail_if_background(step):
    if world.must_fail is not None:
        e = world.must_fail
        world.must_fail = None
        raise e
#}%}

@before.each_step
def apply_monkey_patch(step):
    world.browser.execute_script(world.monkeypatch)

@after.each_scenario
def after_scenario(scenario):
    all_ok = all(map(lambda x : x.passed, scenario.steps))
    if not all_ok:
        try:
            world.nofailure += 1
            world.browser.save_screenshot('failure_%d_%d.png' % (world.FEATURE_VARIABLE['ID'], world.nofailure))
        except:
            pass

@before.each_scenario
def update_idrun(scenario):
    world.FEATURE_VARIABLE = {}

    world.FEATURE_VARIABLE['ID'] = 1

    if os.path.isdir(RUN_NUMBER_FILE):
        raise Error("A configuration file is a directory")
    if os.path.isfile(RUN_NUMBER_FILE):
        #FIXME: A file could be huge, it could lead to a memory burst...
        f = open(RUN_NUMBER_FILE)
        try:
            s_idrun = f.read(512)
            last_idrun = int(s_idrun)
            world.FEATURE_VARIABLE['ID'] = last_idrun + 1
        except ValueError:
            raise Error("Invalid value in %s" % RUN_NUMBER_FILE)

        f.close()

    new_f = open(RUN_NUMBER_FILE, 'w')
    new_f.write(str(world.FEATURE_VARIABLE['ID']))
    new_f.close()

    world.FEATURE_VARIABLE['ID'] = str(world.FEATURE_VARIABLE['ID'])

    base_dir = os.path.dirname(__file__)
    file_path = os.path.join(base_dir, FILE_DIR)
    # we have to set the path for the files
    world.FEATURE_VARIABLE['FILES'] = file_path

@after.each_scenario
def remove_iframes(scenario):
    world.nbframes = 0

@after.all
def disconnect_to_db(total):
    #world.browser = webdriver.PhantomJS()

    if not os.path.isdir(RESULTS_DIR):
        os.mkdir(RESULTS_DIR)

    printscreen_path = os.path.join(RESULTS_DIR, "last_screen.png")
    content_path = os.path.join(RESULTS_DIR, "last_content.html")

    world.browser.save_screenshot(printscreen_path)

    content = world.browser.page_source
    f = open(content_path, 'w')
    f.write(content.encode('utf-8'))
    f.close()

    world.browser.close()

    base_dir = os.path.dirname(__file__)
    file_path = os.path.join(base_dir, FILE_DIR)
    files_after = os.listdir(file_path)

    files_to_delete = set(files_after) - set(world.files_before)

    for filename in files_to_delete:
        file_to_delte = os.path.join(file_path, filename)

        try:
            os.unlink(file_to_delte)
        except OSError as e:
            pass

#}%}

# Log into/out of/restore an instance{%{

#WARNING: Undocumented!
@step('I go on the homepage')
@output.register_for_printscreen
def go_home_page(step):
    world.browser.get(HTTP_URL_SERVER)

def log_into(database_name, username, password):
    database_name = prefix_db_name(convert_input(world, database_name))
    username = convert_input(world, username)
    password = convert_input(world, password)

    tick = monitor(world.browser, "I cannot login with %s/%s" % (username, password))

    while True:
        tick()

        # we would like to get back to the the login page
        world.browser.delete_all_cookies()
        world.browser.get(HTTP_URL_SERVER)

        # select the database chosen by the user
        elem_selects = get_elements(world.browser, tag_name="select", id_attr="db")

        # we cannot crash because it might be related to a bug when loading the page
        #  we should connect to it again.
        if not elem_selects:
            time.sleep(TIME_TO_SLEEP)
            continue
        elem_select = elem_selects[0]

        elem_options = get_elements(elem_select, tag_name="option", attrs={'value': database_name})
        username_textinputs = get_elements(world.browser, tag_name="input", id_attr="user")
        password_textinputs = get_elements(world.browser, tag_name="input", id_attr="password")
        submit_inputs = get_elements(world.browser, tag_name="button", attrs={'type': 'submit'})

        if not elem_options or not username_textinputs or not password_textinputs or not submit_inputs:
            time.sleep(TIME_TO_SLEEP)
            continue

        elem_options[0].click()

        # fill in the credentials
        username_textinputs[0].send_keys(username)
        password_textinputs[0].send_keys(password)
        submit_inputs[0].click()

        redo = False

        # we have to check
        while True:

            elements_error = get_elements(world.browser, tag_name="div", class_attr="login_error_message")
            elements_error = map(lambda x : x.text, elements_error)

            elements_menu = get_elements(world.browser, tag_name="td", id_attr="main_nav")
            elements_menu = map(lambda x : x.text, elements_menu)

            if elements_menu:
                redo = False
                break
            elif elements_error:
                redo = True
                break

            time.sleep(TIME_TO_SLEEP)

        if not redo:
            break

        ## if you want to open the debugger before starting any action in UniField
        #world.browser.find_element_by_tag_name('body').send_keys(Keys.COMMAND + Keys.ALT + 's')

    world.logged_in = True

@step('I log into instance "([^"]*)" as "([^"]*)" with password "([^"]*)"')
@output.register_for_printscreen
def connect_on_database(step, database_name, username, password):
    log_into(database_name, username, password)

@step('I log into instance "([^"]*)"')
@output.register_for_printscreen
def connect_on_database(step, database_name):
    log_into(database_name, UNIFIELD_ADMIN, UNIFIELD_PASSWORD)

@step('I log out')
@output.add_printscreen
def log_out(step):
    world.browser.get("%(url)s/openerp/logout" % dict(url=HTTP_URL_SERVER))

    world.logged_in = False

#}%}

# Synchronisation {%{

@step('I synchronize "([^"]*)"')
@output.register_for_printscreen
def synchronize_instance(step, instance_name):
    instance_name = prefix_db_name(convert_input(world, instance_name))

    from oerplib.oerp import OERP
    from oerplib.error import RPCError

    class XMLRPCConnection(OERP):
        '''
        XML-RPC connection class to connect with OERP
        '''

        def __init__(self, db_name):
            '''
            Constructor
            '''
            # Prepare some values
            server_port = XMLRPC_PORT
            server_url = SRV_ADDRESS
            uid = UNIFIELD_ADMIN
            pwd = UNIFIELD_PASSWORD
            # OpenERP connection
            super(XMLRPCConnection, self).__init__(
                server=server_url,
                protocol='xmlrpc',
                port=server_port,
                timeout=TIME_BEFORE_FAILURE_SYNCHRONIZATION
            )
            # Login initialization
            self.login(uid, pwd, db_name)

    try:
        connection = XMLRPCConnection(instance_name)

        conn_obj = connection.get('sync.client.sync_server_connection')
        sync_obj = connection.get('sync.client.sync_manager')

        conn_ids = conn_obj.search([])
        conn_obj.write(conn_ids, {'login': UNIFIELD_ADMIN, 'password': UNIFIELD_PASSWORD})
        conn_obj.connect(conn_ids)
        sync_ids = sync_obj.search([])
        sync_obj.sync(sync_ids)
    except RPCError as e:
        message = str(e)

        #FIXME: This is a dirty hack. We don't want to fail if there is a revision
        #  available. That's part of a normal scenario. As a result, the code
        #  shouldn't raise an exception.
        if 'revision(s) available' in message:
            return

        raise
#}%}

# Open a menu/tab {%{
@step('I open tab menu "([^"]*)"')
@output.register_for_printscreen
def open_tab(step, tab_to_open):
    tab_to_open_normalized = to_camel_case(tab_to_open)

    elem_menu = get_element(world.browser, tag_name="div", id_attr="applications_menu")
    button_label = get_element_from_text(elem_menu, tag_name="span", text=tab_to_open_normalized, wait="Cannot find tab menu %s" % tab_to_open)
    button_label.click()

    wait_until_not_loading(world.browser, wait="We cannot open fully tab menu '%s'. Something is still processing" % tab_to_open)

    #world.browser.save_screenshot("after_tab.png")

@step('I open accordion menu "([^"]*)"')
@output.register_for_printscreen
def open_tab(step, menu_to_click_on):
    menu_node = get_element(world.browser, tag_name="td", id_attr="secondary")

    tick = monitor(world.browser)
    while True:
        tick()

        accordion_node = get_element_from_text(menu_node, tag_name="li", text=menu_to_click_on, wait="Cannot find accordion %s" % menu_node)
        block_element = accordion_node.find_elements_by_xpath("following-sibling::*[1]")[0]

        height = block_element.size['height']

        if 'accordion-title-active' in accordion_node.get_attribute("class"):
            break

        accordion_node.click()

        # we have to ensure that the element is not hidden (because of animation...)
        tick2 = monitor(world.browser)
        while True:
            tick2()
            accordion_node = get_element_from_text(menu_node, tag_name="li", text=menu_to_click_on, wait="Cannot find accordion %s" % menu_node)
            block_element = accordion_node.find_elements_by_xpath("following-sibling::*[1]")[0]
            height = block_element.size['height']

            style = block_element.get_attribute("style")

            if style == 'display: block;' or style == 'display: none;':
                break

            time.sleep(TIME_TO_SLEEP)

def open_menu(menu_to_click_on):
    menu_node = get_element(world.browser, tag_name="td", id_attr="secondary")

    menus = menu_to_click_on.split("|")

    after_pos = 0
    i = 0

    tick = monitor(world.browser)
    while i < len(menus):
        menu = menus[i]
        tick()

        elements = get_elements(menu_node, tag_name="a")
        # We don't know why... but some elements appear to be empty when we start using the menu
        #  then, they disapear when we open a menu

        elements = filter(lambda x : x.text.strip() != "" and x.text.strip() != "Toggle Menu", elements)
        visible_elements = filter(lambda x : x.is_displayed(), elements)
        valid_visible_elements = visible_elements[after_pos:]

        text_in_menus = map(lambda x : x.text, valid_visible_elements)

        if menu in text_in_menus:
            pos = text_in_menus.index(menu)

            valid_visible_elements[pos].click()

            if i == len(menus) - 1:
                wait_until_not_loading(world.browser, wait="Cannot open menu %s. Loading takes too much time." % menu)
                return

            # we have to check if it has an impact on number of menus
            tick2 = monitor(world.browser)
            while True:
                tick2()
                elements_after = get_elements(menu_node, tag_name="a")
                elements_after = filter(lambda x : x.text.strip() != "" and x.text.strip() != "Toggle Menu", elements_after)
                visible_elements_after = filter(lambda x : x.is_displayed(), elements_after)
                visible_elements_after = visible_elements_after[after_pos:]

                if len(valid_visible_elements) > len(visible_elements_after):
                    # the number of menus has decreased, we've just closed a menu
                    time.sleep(TIME_TO_SLEEP)
                    break
                elif len(valid_visible_elements) < len(visible_elements_after):
                    after_pos += pos + 1
                    i += 1
                    break

#FIXME: We have to open the window for PhantomJS.
@step('I click on menu "([^"]*)" and open the window$')
@output.register_for_printscreen
def open_tab(step, menu_to_click_on):
    open_menu(menu_to_click_on)

    # we have to open the window!
    world.browser.switch_to_default_content()
    world.browser.switch_to_frame(get_element(world.browser, tag_name="iframe", position=world.nbframes, wait="Cannot find the window"))
    world.nbframes += 1
    wait_until_no_ajax(world)

@step('I click on menu "([^"]*)"$')
@output.register_for_printscreen
def open_tab(step, menu_to_click_on):

    open_menu(menu_to_click_on)

@step('I open tab "([^"]*)"')
@output.add_printscreen
def open_tab(step, tabtoopen):
    msg = "Cannot find tab %s" % tabtoopen
    click_on(world.browser, lambda : get_element_from_text(world.browser, class_attr="tab-title", tag_name="span", text=tabtoopen, wait=msg), msg)
    wait_until_not_loading(world.browser, wait="Cannot open the tab. Loading takes too much time")

#}%}

# Fill fields {%{

@step('I fill "([^"]*)" with "([^"]*)"$')
@output.register_for_printscreen
def fill_field(step, fieldname, content):

    content = convert_input(world, content)

    # Most of the fields use IDs, however, some of them are included in a table with strange fields.
    #  We have to look for both
    idattr, my_input = get_input(world.browser, fieldname)

    if my_input.tag_name == "select":
        #FIXME: Sometimes it doesn't work... the input is not selected
        # or the value is not saved... Is it related to the Selenium's version?
        select = Select(my_input)
        select.select_by_visible_text(content)

        wait_until_no_ajax(world)

        ## This version is quite the same as the previous one except that it sometimes fail
        #   to select the right text (but the selected value is correct)
        option = get_element_from_text(my_input, tag_name="option", text=content)
        option.click()
    elif my_input.tag_name == "input" and my_input.get_attribute("type") == "file":
        #FIXME: This clear is not allowed in ChromeWebDriver. It is allowed in Firefox.
        #  We should ensure that this method is still available.
        #my_input.clear()
        base_dir = os.path.dirname(__file__)
        content_path = os.path.join(base_dir, FILE_DIR, content)

        if not os.path.isfile(content_path):
            raise UniFieldElementException("%s is not a file" % content_path)
        my_input.send_keys(content_path)
    elif my_input.tag_name == "input" and my_input.get_attribute("type") and my_input.get_attribute("type") == "checkbox":

        if content.lower() not in ["yes", "no"]:
            raise UniFieldElementException("You cannot defined any value except no and yes for a checkbox")

        if content.lower() == "yes":
            if not my_input.is_selected():
                my_input.click()
        else:
            if my_input.is_selected():
                my_input.click()

        #WARNING: the attribute's name is different in PhantomJS and Firefox. Firefox change it into lower case.
        #  That's not the case of PhantomJS (chromium?). We have to take both cases into account.
    elif my_input.get_attribute("autocomplete") and my_input.get_attribute("autocomplete").lower() == "off" and '_text' in idattr:
        select_in_field_an_option(world,
                                  lambda : (get_element(world.browser, id_attr=idattr.replace('/', '\\/'), wait="Cannot find the field for this input"), action_write_in_element),
                                  content)
    else:
        # we have to ensure that the input is selected without any change by a javascript
        tick = monitor(world.browser)
        while True:
            tick()
            input_text = convert_input(world, content)
            my_input.send_keys((100*Keys.BACKSPACE) + input_text + Keys.TAB)

            #world.browser.execute_script("$('#%s').change()" % my_input.get_attribute("id"))
            wait_until_no_ajax(world)

            if my_input.get_attribute("value") == input_text:
                break

            time.sleep(TIME_TO_SLEEP)

    wait_until_no_ajax(world)

@step('I fill "([^"]*)" with "([^"]*)" and open the window$')
@output.register_for_printscreen
def fill_field_and_open(step, fieldname, content):
    fill_field(step, fieldname, content)

    world.browser.switch_to_default_content()
    world.browser.switch_to_frame(get_element(world.browser, position=world.nbframes, tag_name="iframe", wait="I don't find the new window"))
    world.nbframes += 1

    wait_until_no_ajax(world)

@step('I fill "([^"]*)" with table:$')
@output.register_for_printscreen
def fill_field_table(step, fieldname):
    if not step.hashes:
        raise UniFieldElementException("Why don't you define at least one row?")

    TEMP_FILENAME = 'tempfile'

    base_dir = os.path.dirname(__file__)
    content_path = os.path.join(base_dir, FILE_DIR, TEMP_FILENAME)
    f = open(content_path, 'w')

    f.write('<?xml version="1.0"?>')
    f.write('<ss:Workbook xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet">')
    f.write('<ss:Worksheet ss:Name="Sheet1">')
    f.write('<ss:Table>')

    row_number = 1

    for row in step.hashes:
        values = row.items()
        values.sort()


        f.write('<ss:Row>')
        for header, cell in values:
            f.write('<ss:Cell>')

            #FIXME: Boolean are not take into account (condition: ('1', 'T', 't', 'True', 'true'))
            celltype = 'String'
            if re.match('^\d{4}-\d{2}-\d{2}$', cell) is not None:
                celltype = 'DateTime'
            elif re.match('^\d+$', cell) is not None:
                celltype = 'Number'

            localdict = dict(ROW=str(row_number))

            def encode(s):
                return s.encode('utf-8').replace('&', '&amp;')

            f.write('<ss:Data ss:Type="%s">%s</ss:Data>' % (encode(celltype), encode(convert_input(world, cell, localdict))))
            f.write('</ss:Cell>')
        f.write('</ss:Row>')

        row_number += 1

    f.write('</ss:Table>')
    f.write('</ss:Worksheet>')
    f.write('</ss:Workbook>')
    f.close()

    step.given('I fill "%s" with "%s"' % (fieldname, TEMP_FILENAME))

def validate_variable(variable_name):
    '''
    Check if the variable name is valid to be used in testfield.
    '''
    for forbidden_car in ['{', '}']:
        if forbidden_car in variable_name:
            raise UnifieldException("We don't accept %s in variable name" % forbidden_car)

@step('I store column "([^"]*)" in "([^"]*)" for line:$')
def remember_step_in_table(step, column_name, variable):

    wait_until_not_loading(world.browser, wait=world.nbframes == 0)
    wait_until_no_ajax(world)

    if len(step.hashes) != 1:
        raise UniFieldElementException("We cannot store more than one value. You have to define one row")

    # we take the first hash
    rows = list(get_table_row_from_hashes(world, step.hashes[0]))
    if not rows:
        raise UniFieldElementException("The line hasn't been found")

    for table, row_node in rows:
        position_in_table = get_column_position_in_table(table, column_name)

        if position_in_table is not None:
            td_node = get_element(row_node, class_attr="grid-cell", tag_name="td", position=position_in_table)
            validate_variable(variable.strip())
            world.FEATURE_VARIABLE[variable.strip()] = td_node.text.strip()
            return

    raise UnifieldException("No line with column %s has been found" % column_name)

@step('I store "([^"]*)" in "([^"]*)"$')
def remember_step(step, fieldname, variable):

    values = get_values(fieldname)

    if not values:
        raise UniFieldElementException("No field named %s" % fieldname)
    elif len(values) > 1:
        raise UniFieldElementException("Several values found for %s (values: %s)" % (fieldname, ', '.join(values)))

    validate_variable(variable.strip())
    world.FEATURE_VARIABLE[variable.strip()] = values[0].strip()

#}%}

# Active waiting {%{

@step('I click on "([^"]*)" until not available$')
def click_until_not_available2(step, button):
    wait_until_not_loading(world.browser, wait=world.nbframes == 0)

    tick = monitor(world.browser)
    while True:
        tick()
        try:
            elem = get_elements_from_text(world.browser, tag_name=["button", "a"], text=button)
            if elem:
                elem[0].click()
                time.sleep(TIME_TO_WAIT)
            else:
                break
        except (StaleElementReferenceException, ElementNotVisibleException):
            pass

@step('I click on "([^"]*)" until "([^"]*)" in "([^"]*)"$')
def click_until_not_available1(step, button, value, fieldname):

    wait_until_not_loading(world.browser, wait = "Loading before clicking takes too much time" if world.nbframes == 0 else '')
    tick = monitor(world.browser)

    while True:
        tick()
        try:
            world.browser.switch_to_default_content()
            if world.nbframes != 0:
                world.browser.switch_to_frame(get_element(world.browser, position=world.nbframes-1, tag_name="iframe", wait="Cannot find the frame in which the button is located"))

            # what's in the input? Have we just reached the end of the process?
            _, my_input = get_input(world.browser, fieldname)

            if value in my_input.get_attribute("value"):
                return

            elem = get_elements_from_text(world.browser, tag_name=["button", "a"], text=button)
            if elem:
                elem[0].click()
                time.sleep(TIME_TO_WAIT)
            else:
                break
        except (AssertionError, StaleElementReferenceException, ElementNotVisibleException) as e:
            # AssertionError is used if the frame is not the good one (because it was replaced with
            #  another one)
            pass
            print e

# I click on ... {%{
# I click on "Search/New/Clear"

@step('(.*) if a window is open$')
def if_a_window_is_open(step, nextstep):
    if world.nbframes > 0:
        step.given(nextstep)

@step('I click on "([^"]*)" and close the window if necessary$')
@output.add_printscreen
def close_window_if_necessary(step, button):

    # It seems that some action could still be launched when clicking on a button,
    #  we have to wait on them for completion
    wait_until_not_loading(world.browser, wait=world.nbframes == 0)

    # what's the URL of the current frame?
    world.browser.switch_to_default_content()
    # We have to wait here because we sometimes the new iframe is not visible straight away
    previous_iframes = get_elements(world.browser, tag_name="iframe", wait=True)
    last_frame = previous_iframes[-1]
    previous_url = last_frame.get_attribute("src")
    world.browser.switch_to_frame(get_element(world.browser, tag_name="iframe", position=world.nbframes-1, wait="Cannot find the window in which the button is located"))

    msg = "Cannot find button %s" % button
    click_on(world.browser, lambda : get_element_from_text(world.browser, tag_name=["button", "a"], text=button, wait=msg), msg)

    world.browser.switch_to_default_content()
    tick = monitor(world.browser)
    while True:
        tick()
        try:
            current_iframes = get_elements(world.browser, tag_name="iframe")

            if len(current_iframes) != len(previous_iframes):
                # we close the window => we have to remove the window
                world.nbframes -= 1
                world.browser.switch_to_default_content()
                if world.nbframes != 0:
                    world.browser.switch_to_frame(get_element(world.browser, position=world.nbframes-1, tag_name="iframe", wait="Cannot find the previous frame"))
                return

            # if the url is different => we keep the window
            current_url = current_iframes[-1].get_attribute("src")

            if current_url != previous_url:
                #TODO ADD AN EXPLANATION HERE ET BELOW
                #TODO GIVE AN EXPLANATION FOR ALL THE CALLS TO monitor(...) and the others (except get_element(s) and get_elemnets_from_text...)
                world.browser.switch_to_frame(get_element(world.browser, position=world.nbframes-1, tag_name="iframe", wait="I cannot find the new window"))
                return

            time.sleep(TIME_TO_SLEEP)

        except (StaleElementReferenceException, ElementNotVisibleException):
            pass

@step('I click on "([^"]*)"$')
@output.add_printscreen
def click_on_button(step, button):
    # It seems that some action could still be launched when clicking on a button,
    #  we have to wait on them for completion
    # But we cannot do that for frames because the "loading" menu item doesn't exist
    #  at that time.

    if world.logged_in:
        wait_until_not_loading(world.browser, wait=world.nbframes == 0)
    else:
        # But we have to take into account that such element doesn't exist when a user is not logged in...
        wait_until_not_loading(world.browser, wait=False)

    # we have an issue when the user is not logged in... the important buttons are "at the end of the page". We have to
    #  fetch them in another order
    position_element = 0 if world.logged_in else -1
    msg = "Cannot find button %s" % button
    click_on(world.browser, lambda : get_elements_from_text(world.browser, tag_name=["button", "a"], text=button, wait=msg)[position_element], msg)

    if world.nbframes != 0:
        wait_until_not_loading(world.browser, wait=False)

        world.browser.switch_to_default_content()
        world.browser.switch_to_frame(get_element(world.browser, tag_name="iframe", wait="I cannot select the current window", position=world.nbframes-1))

        wait_until_not_loading(world.browser, wait=False)
        wait_until_no_ajax(world)
    else:
        wait_until_not_loading(world.browser, wait=False)
        wait_until_no_ajax(world)
        #world.browser.save_screenshot('mourge.png')

@step('I click on "([^"]*)" and open the window$')
@output.add_printscreen
def click_on_button_and_open(step, button):

    wait_until_not_loading(world.browser, wait=False)
    wait_until_no_ajax(world)
    msg = "Cannot find button %s" % button
    click_on(world.browser, lambda : get_element_from_text(world.browser, tag_name="button", text=button, wait=msg), msg)

    wait_until_not_loading(world.browser, wait=False)

    world.browser.switch_to_default_content()
    world.browser.switch_to_frame(get_element(world.browser, position=world.nbframes, tag_name="iframe", wait="I don't find the new window"))
    world.nbframes += 1

    wait_until_no_ajax(world)

@step('I close the window$')
@output.add_printscreen
def close_the_window(step):

    world.browser.switch_to_default_content()

    elem = get_element_from_text(world.browser, tag_name="span", text="close", wait="Cannot find the button to close the window")
    elem.click()

    world.nbframes -= 1
    if world.nbframes > 0:
        world.browser.switch_to_frame(get_element(world.browser, position=world.nbframes-1, tag_name="iframe", wait="I don't find the previous window"))
    else:
        wait_until_element_does_not_exist(world.browser, lambda : get_element(world.browser, tag_name="iframe"))

# I click on "Save & Close"

@step('I click on "([^"]*)" and close the window$')
@output.add_printscreen
def click_on_button_and_close(step, button):

    msg = "Cannot find the button to close the window"
    click_on(world.browser,  lambda : get_element_from_text(world.browser, tag_name=["button", "a"], text=button, wait=msg), msg)
    world.nbframes -= 1

    world.browser.switch_to_default_content()
    if world.nbframes > 0:
        world.browser.switch_to_frame(get_element(world.browser, position=world.nbframes-1, tag_name="iframe", wait="I don't find the previous window"))
    else:
        wait_until_element_does_not_exist(world.browser, lambda : get_element(world.browser, tag_name="iframe"))

    #wait_until_not_loading(world.browser)
    wait_until_no_ajax(world)

def click_if_toggle_button_is(btn_name, from_class_name):
    btn_name = to_camel_case(btn_name)

    btn_toggle = get_element_from_text(world.browser, tag_name="button", text=btn_name, class_attr=from_class_name, wait="Cannot find toggle button %s" % btn_name)
    elem = btn_toggle.get_attribute("class")
    classes = map(lambda x : x.strip(), elem.split())

    btn_toggle.click()
    wait_until_not_loading(world.browser)
    wait_until_no_ajax(world)

@step('I toggle on "([^"]*)"$')
@output.register_for_printscreen
def toggle_on(step, button):
    click_if_toggle_button_is(button, "filter_with_icon inactive")

@step('I toggle off "([^"]*)"$')
@output.register_for_printscreen
def toggle_off(step, button):
    click_if_toggle_button_is(button, "filter_with_icon active")

#}%}

# Check messages (error, warning, ...) {%{

def get_values(fieldname):
    _, txtinput = get_input(world.browser, fieldname)

    # if it's a text that is not changable
    if txtinput.tag_name in ['span', 'textarea']:
        return [txtinput.text]
    elif txtinput.tag_name in ['input']:
        if txtinput.get_attribute("type") and txtinput.get_attribute("type") == "checkbox":
            return ["yes" if txtinput.is_selected() else "no"]
        else:
            return [txtinput.get_attribute("value")]
    elif txtinput.tag_name in ['select']:
        select = Select(txtinput)
        return map(lambda x : x.text, select.all_selected_options)
    else:
        return []

@step('I should see "([^"]*)" in "([^"]*)"')
@output.register_for_printscreen
def should_see(step, content, fieldname):

    wait_until_not_loading(world.browser, wait=False)

    content = convert_input(world, content)
    reg = create_regex(content)

    content_found = get_values(fieldname)

    if not content_found:
        raise UniFieldElementException("No field named %s" % fieldname)
    elif len(content_found) > 1:
        raise UniFieldElementException("Several values found for %s (values: %s)" % (fieldname, ', '.join(content_found)))

    if re.match(reg, content_found[0], flags=re.DOTALL) is None:
        raise UniFieldElementException("%s doesn't contain %s (values found: %s)" % (fieldname, content, ', '.join(content_found)))

@step('I should see a text status with "([^"]*)"')
@output.register_for_printscreen
def see_status(step, message_to_see):
    wait_until_not_loading(world.browser)
    elem = get_element(world.browser, tag_name="tr", id_attr="actions_row", wait="I don't see any text status")

    reg = create_regex(message_to_see)

    if re.match(reg, elem.text, flags=re.DOTALL) is None:
        print "No '%s' found in '%s'" % (message_to_see, elem.text)
        raise UniFieldElementException("No '%s' found in '%s'" % (message_to_see, elem.text))

@step('I should see a popup with "([^"]*)"$')
@output.register_for_printscreen
def see_popup(step, message_to_see):
    wait_until_not_loading(world.browser)
    elem = get_element(world.browser, tag_name="td", class_attr="error_message_content", wait="I don't find any popup")

    reg = create_regex(message_to_see)

    if re.match(reg, elem.text, flags=re.DOTALL) is None:
        print "No '%s' found in '%s'" % (message_to_see, elem.text)
        raise UniFieldElementException("No '%s' found in '%s'" % (message_to_see, elem.text))

@step('I should see "([^"]*)" in the section "([^"]*)"$')
@output.register_for_printscreen
def see_popup(step, content, section):
    #WARNING: This step is used for UniField automation. We use it to ensure that
    # we can import the files without any error (a text message in a section has to be checked)

    section = get_element_from_text(world.browser, tag_name="h2", class_attr="separator horizontal", text=section, wait="Cannot find section %s" % section)

    table_node = section.find_elements_by_xpath("ancestor::table[1]")[0]

    reg = create_regex(content)
    found = False
    for elem in get_elements(table_node, wait=False):
        if re.match(reg, elem.text, flags=re.DOTALL) is not None:
            found = True

    if not found:
        raise UnifieldException("I haven't found content %s" % content)

#}%}

# Table management {%{

def get_pos_for_fieldname(fieldname):

    tick = monitor(world.browser)
    while True:
        tick()
        # A new table is sometimes created
        try:
            #FIXME we should look for this value in all the tables
            gridtable = get_element(world.browser, tag_name="table", class_attr="grid")
            right_pos = get_column_position_in_table(gridtable, fieldname)

            # we have to wait on the table to be editable (or at least one row)
            if get_elements(gridtable, tag_name="tr", class_attr="editors", wait=False):
                break

            time.sleep(TIME_TO_SLEEP)

        except StaleElementReferenceException as e:
            print e
            pass

    if right_pos is None:
        raise UniFieldElementException("Cannot find column '%s'" % fieldname)
    
    return right_pos

def check_checkbox_action(content, fieldname, action=None):

    content = convert_input(world, content)

    #FIXME: This method should use the same behaviour as "I fill ... with ..."
    def get_text_box():
        row_in_edit_mode = get_element(world.browser, tag_name="tr", class_attr="editors", wait="I don't find any line to edit")

        td_node = get_element(row_in_edit_mode, class_attr="grid-cell", tag_name="td", position=right_pos)

        # do we a select at our disposal?
        a_select = get_elements(td_node, tag_name="select")

        if a_select:
            return a_select[0], action or action_select_option
        else:
            input_type = "text" if get_elements(td_node, tag_name="input", attrs={'type': 'text'}) else "checkbox"
            my_input = get_element(td_node, tag_name="input", attrs={'type': input_type})

            return my_input, action or action_write_in_element

    right_pos = get_pos_for_fieldname(fieldname)

    select_in_field_an_option(world, get_text_box, content)

@step('I fill "([^"]*)" within column "([^"]*)"$')
@output.register_for_printscreen
def fill_column(step, content, fieldname):
    check_checkbox_action(content, fieldname)

@step('I fill "([^"]*)" within column "([^"]*)" and open the window')
@output.register_for_printscreen
def fill_column_with_window(step, content, fieldname):
    fill_column(step, content, fieldname)

    world.browser.switch_to_default_content()
    world.browser.switch_to_frame(get_element(world.browser, tag_name="iframe", position=world.nbframes, wait="I don't find the new window"))
    world.nbframes += 1

    wait_until_no_ajax(world)

@step('I tick all the lines')
@output.register_for_printscreen
def click_on_all_line(step):

    wait_until_not_loading(world.browser, wait=False)
    wait_until_no_ajax(world)

    open_all_the_tables(world)

    for elem in get_elements(world.browser, class_attr='grid-header', tag_name="tr"):
        get_element(elem, tag_name="input", attrs={'type': 'checkbox'}).click()

    wait_until_not_loading(world.browser, wait=False)
    wait_until_no_ajax(world)

def get_action_element_in_line(row_node, action):
    # we have to look for this action the user wants to execute
    if action == 'checkbox':
        actions_to_click = get_elements(row_node, tag_name="input", attrs=dict(type='checkbox'))
    elif action == 'option':
        actions_to_click = get_elements(row_node, tag_name="input", attrs=dict(type='radio'))
    elif action == 'line':
        actions_to_click = [row_node]
    else:
        actions_to_click = get_elements(row_node, attrs={'title': action})

    actions_to_click = filter(lambda x : x.is_displayed(), actions_to_click)

    return actions_to_click

def click_on_line(step, action, window_will_exist=True):
    # This is important because we cannot click on lines belonging
    #  to the previous window
    wait_until_not_loading(world.browser, wait=False)

    if not step.hashes:
        raise UniFieldElementException("You have to click on at least one line")

    import collections
    no_by_fingerprint = collections.defaultdict(lambda : 0)

    for i_hash in step.hashes:

        #FIXME: The key/values could be wrong, because the same hash
        # could exist with a "_". Two different lines could have the same fingerprint.
        key_value = map(lambda (a,b) : '%s/%s' % (str(a), str(b)), i_hash.iteritems())
        key_value.sort()
        hash_key_value = '_'.join(key_value)

        def try_to_click_on_line(step, action):
            table_row_nodes = get_table_row_from_hashes(world, i_hash)

            matched_row_to_click_on = no_by_fingerprint[hash_key_value]
            no_matched_row = 0

            for table, row_node in table_row_nodes:
                actions_to_click = get_action_element_in_line(row_node, action)

                if not actions_to_click:
                    continue

                if no_matched_row == matched_row_to_click_on:
                    action_to_click = actions_to_click[0]
                    if not action_to_click.is_displayed():
                        continue
                    action_to_click.click()
                    no_by_fingerprint[hash_key_value] += 1
                    # we have found the line, the action has already been found.
                    #  everything is great
                    return
                else:
                    no_matched_row += 1

            # we have to provide an error mesage to explain the options
            columns = i_hash.keys()
            options = map(lambda x : x[2], get_options_for_table(world, columns))
            options_txt =', '.join(map(lambda x : '|'.join(x), options))
            raise UniFieldElementException("A line hasn't been found among the following values: %s" % options_txt)

        repeat_until_no_exception(world, try_to_click_on_line, (ElementNotVisibleException, UniFieldElementException, StaleElementReferenceException), step, action)

        if window_will_exist and world.nbframes > 0:
            wait_until_not_loading(world.browser, wait=False)
            wait_until_no_ajax(world)

            world.browser.switch_to_default_content()
            wait_until_not_loading(world.browser, wait=False)
            # We cannot use wait_until_no_ajax because the elements
            #wait_until_no_ajax(world)

            world.browser.switch_to_frame(get_element(world.browser, tag_name="iframe", position=world.nbframes-1, wait="I don't find the new window"))
            wait_until_not_loading(world.browser, wait=False)
            wait_until_no_ajax(world)
        elif window_will_exist:
            # we have to execute that outside the function because it cannot raise an exception
            #  (we would do the action twice)
            wait_until_not_loading(world.browser, wait=False)
            wait_until_no_ajax(world)

@step('I click on line:')
@output.add_printscreen
def click_on_line_line(step):
    click_on_line(step, "line")




@step('I click "([^"]*)" on line:')
@output.register_for_printscreen
def click_on_line_tooltip(step, action):
    click_on_line(step, action)

@step('I click "([^"]*)" on line and close the window:')
@output.add_printscreen
def click_on_line_and_open_the_window(step, action):

    if len(step.hashes) != 1:
        raise UnifieldException("You should click only on one line to close the window")

    click_on_line(step, action, window_will_exist=False)

    wait_until_element_does_not_exist(world.browser, lambda : get_element(world.browser, tag_name="iframe", position=world.nbframes-1))

    wait_until_no_ajax(world)
    wait_until_not_loading(world.browser, wait=world.nbframes == 0)

@step('I click "([^"]*)" on line and open the window:')
@output.add_printscreen
def click_on_line_and_open_the_window(step, action):
    click_on_line(step, action)

    world.browser.switch_to_default_content()
    world.browser.switch_to_frame(get_element(world.browser, tag_name="iframe", position=world.nbframes, wait="I don't find the new window"))
    world.nbframes += 1

    wait_until_no_ajax(world)

def check_that_line(step, should_see_lines, action=None):
    values = step.hashes

    open_all_the_tables(world)

    def try_to_check_line(step):
        for hashes in values:
            lines = list(get_table_row_from_hashes(world, hashes))

            # do we have to filter the rows with the right action?
            if action is not None:
                lines = filter(lambda (_, row) : get_action_element_in_line(row, action), lines)

            if bool(lines) != should_see_lines:
                columns = hashes.keys()
                options = map(lambda x : x[2], get_options_for_table(world, columns))
                options_txt =', '.join(map(lambda x : '|'.join(x), options))
                if should_see_lines:
                    raise UniFieldElementException("I don't find: %s. My options where: %s" % (hashes, options_txt))
                else:
                    raise UniFieldElementException("I found : %s" % hashes)

    repeat_until_no_exception(world, try_to_check_line, (StaleElementReferenceException, UniFieldElementException), step)

@step('I should see in the main table the following data:')
@output.register_for_printscreen
def check_line(step):
    check_that_line(step, True)

@step("I shouldn't be able to click \"([^\"]*)\" on line:")
@output.register_for_printscreen
def check_not_click_on_line(step, action):
    if len(step.hashes) != 1:
        raise UniFieldElementException("You should define what is the line unique line you want to click on")

    # (1) we check that the line exists
    check_that_line(step, True)

    # (2) but we shouldn't be able to click on it
    check_that_line(step, False, action=action)

@step("I shouldn't be able to edit \"([^\"]*)\"$")
@output.register_for_printscreen
def should_be_able_to_edit(step, fieldname):
    _, my_input = get_input(world.browser, fieldname)

    if not my_input.get_attribute("readonly") and not my_input.get_attribute("disabled"):
        raise UniFieldElementException("The field %s is ediable" % fieldname)

@step("I shouldn't be able to edit column \"([^\"]*)\"$")
@output.register_for_printscreen
def should_not_be_able_to_edit(step, fieldname):

    def action_check(txt_input, content):
        if not txt_input.get_attribute("readonly") and not txt_input.get_attribute("disabled"):
            raise UniFieldElementException("The field %s is ediable" % fieldname)

    check_checkbox_action("", fieldname, action_check)

@step('I should not see in the main table the following data:')
@output.register_for_printscreen
def check_line(step):
    check_that_line(step, False)

def search_until_I(step, action_search, see):
    if not step.hashes:
        raise UniFieldElementException("Why don't you define at least one row?")

    def try_to_check_line(myhashes):
        for hashes in myhashes:
            ret = list(get_table_row_from_hashes(world, hashes))
            if not ret:
                return False
        return True

    myhashes = map(lambda x : dict(x), step.hashes)

    step.given('I click on "%s"' % action_search)

    tick = monitor(world.browser, ("I don't find the following row(s): %s" if see else "I still see %s") % myhashes)

    while repeat_until_no_exception(world, try_to_check_line, StaleElementReferenceException, myhashes) != see:
        step.given('I click on "%s"' % action_search)
        time.sleep(TIME_TO_WAIT)
        tick()

@step('I click "([^"]*)" until I don\'t see:')
def click_on_search_until_not(step, action_search):
    search_until_I(step, action_search, False)

@step('I click "([^"]*)" until I see:')
def click_on_search_until(step, action_search):
    search_until_I(step, action_search, True)

@step('I click "([^"]*)" in the side panel$')
@output.add_printscreen
def open_side_panel(step, menuname):
    wait_until_no_ajax(world)
    wait_until_not_loading(world.browser)

    if world.nbframes != 0:
        raise UniFieldElementException("You cannot open the side panel if you have just opened a window")

    # sometimes the click is not done (or at least the side panel doesn't open...)
    #  it seems that this is related to a new
    #FIXME: On Firefox, this click sometimes doesn't work because it click on the window
    #  and not on the small button to open the window...
    element = get_element(world.browser, id_attr="a_main_sidebar", wait="I don't find the side bar")
    tick = monitor(world.browser)
    while 'closed' in element.get_attribute("class"):
        tick()
        script = "$('#%s').click()" % element.get_attribute("id")
        world.browser.execute_script(script)

    elem = get_element_from_text(world.browser, tag_name="a", text=menuname, wait="Cannot find menu '%s' in the side panel" % menuname)
    elem.click()

    wait_until_not_loading(world.browser)

@step('I click "([^"]*)" in the side panel and open the window$')
@output.add_printscreen
def open_side_panel_and_open(step, menuname):

    open_side_panel(step, menuname)

    world.browser.switch_to_default_content()
    world.browser.switch_to_frame(get_element(world.browser, tag_name="iframe", position=world.nbframes, wait="I don't find the new window"))
    world.nbframes += 1

    wait_until_no_ajax(world)

@step('I validate the line')
@output.register_for_printscreen
def choose_field(step):
    wait_until_no_ajax(world)
    wait_until_not_loading(world.browser)

    # We have to ensure that the number of rows changes, otherwise, we could continue
    #  without validating it effectively
    nbrows_before = len(filter(lambda x : x.get_attribute("record") is not None, get_elements(world.browser, tag_name="tr", class_attr='inline_editors')))


    records_before = map(lambda x : x.get_attribute("record"), filter(lambda x : x.get_attribute("record") is not None, get_elements(world.browser, tag_name="tr", class_attr='inline_editors')))

    tick = monitor(world.browser)
    while True:
        tick()
        # We cannot click using Selenium because the button is sometimes outside
        #  of the window. But sometimes we click on "the new update". So we have to choose the first one.
        world.browser.execute_script("$('img[title=Update]').first().triggerHandler('click')")
        #click_on(lambda : get_element(world.browser, tag_name="img", attrs={'title': 'Update'}, wait=True))

        wait_until_no_ajax(world)
        wait_until_not_loading(world.browser)

        try:
            nbrows_after = len(filter(lambda x : x.get_attribute("record") is not None, get_elements(world.browser, tag_name="tr", class_attr='inline_editors')))
            records_after = map(lambda x : x.get_attribute("record"), filter(lambda x : x.get_attribute("record") is not None, get_elements(world.browser, tag_name="tr", class_attr='inline_editors')))

        except StaleElementReferenceException as e:
            print "StaleElementReferenceException"
            continue

        # We have to check if a new ID has just appeard. We cannot just compare the sizes because
        #  a pager could be used. As a result, the number of rows won't change if we add a new one
        #  since one of them will become hidden directly.
        if set(records_after) ^ set(records_before):
            break

        time.sleep(TIME_TO_SLEEP)

        # we don't need to check the change of IDs since it's always validates with the waits above
        break


#}%}

@step('I wait "([^"]*)" seconds$')
def selenium_sleeps(step, seconds):
    #This step is used to instrument UniField. Don't change it!
    import time
    time.sleep(int(seconds))

# Debugging steps {%{
@step('I sleep')
def selenium_sleeps(step):
    import time
    time.sleep(30000)

@step('I wait$')
@output.register_for_printscreen
def selenium_sleeps(step):
    raw_input()

#}%}

# Time evaluators {%{

@step('I store the time difference in "([^"]*)"')
def save_time_difference(step, counter):
    step.need_printscreen = False
    now = datetime.datetime.now()

    total_secs = timedelta_total_seconds(now - world.last_measure)
    world.durations[counter] = total_secs

@step('I save the time')
def save_time(step):
    step.need_printscreen = False
    world.last_measure = datetime.datetime.now()

@step('I store the values for "([^"]*)" in "([^"]*)"')
def save_time_results(step, counters, filename):

    if not os.path.isdir(RESULTS_DIR):
        os.mkdir(RESULTS_DIR)

    step.need_printscreen = False
    values = []

    if 'COUNT' in os.environ:
        values.append(os.environ['COUNT'])

    for counter in counters.split():
        values.append(str(world.durations.get(counter, '')))

    results_path = os.path.join(RESULTS_DIR, '%s.csv' % filename)

    # let's create a title
    ret = ['COUNT'] if 'COUNT' in os.environ else []
    ret += counters.split()
    first_line = ';'.join(ret)
    has_to_add_title = True

    # we have to read the last line to check if a header has to be added
    if os.path.isfile(results_path):
        with open(results_path, 'r') as f:
            lines = f.readlines()

            if lines and lines[0].strip() == first_line.strip():
                has_to_add_title = False

    f = open(results_path, 'a')
    if has_to_add_title:
        f.write(first_line + '\r\n')

    line = ';'.join(values)
    f.write(line + '\r\n')
    f.close()

    meta_path = os.path.join(RESULTS_DIR, '%s.meta' % filename)
    f = open(meta_path, 'w')
    f.write("description=%s" % step.scenario.name)

    if 'DATABASES' in os.environ:
        f.write("\r\ndatabases=%s" % os.environ['DATABASES'])

    f.close()

#}%}

