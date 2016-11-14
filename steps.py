from credentials import *

import output
from lettuce import *
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
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

TEMP_FILENAME = 'tempfile'

RUN_NUMBER_FILE = 'run_scenario'
RUN_FEATURE_NUMBER_FILE = 'run_feature'

# We have to handle special steps to be able to loop until a condition is not met {%{

def handle_delayed_step(func):
    def fonc_to_call(*args, **argv):
        if world.steps_to_run is None:
            return func(*args, **argv)
        else:
            world.steps_to_run[-1].append((func, args, argv))
            def dummy(*args, **argv):
                pass
            return dummy
    return fonc_to_call

@before.all
def init_loop():
    world.steps_to_run = None
    world.record_printscreen = True

@step('^I repeat:$')
@handle_delayed_step
def repeat_process(step):
    if world.steps_to_run is None:
        world.steps_to_run = []
    world.steps_to_run.append([])

@step('^Until "([^"]*)" equals "([^"]*)"$')
def until_a_equals_b(step, value1, value2):
    assert world.steps_to_run

    # we are going to run the tests
    steps = world.steps_to_run[-1]

    tick = monitor(world.browser, "I've waited too long on %s to become %s" % (value1, value2))

    import collections

    deque = collections.deque(maxlen=4)

    nb_loop = 1

    while True:
        for func, args, argv in steps:
            world.record_printscreen = False
            func(*args, **argv)

        # check that the value exists
        conv_value1 = convert_input(world, value1)
        conv_value2 = convert_input(world, value2)

        reg = create_regex(conv_value2)

        if re.match(reg, conv_value1, flags=re.DOTALL) is not None:
            break

        deque.appendleft("%s != %s" % (conv_value1, conv_value2))
        possibilities = ', '.join(deque)
        content_error = "I've waited too long on %s to become %s (last possibilities: %s)" % (value1, value2, possibilities)

        nb_loop += 1
        tick(content_error, factor=7)

        time.sleep(TIME_TO_WAIT)

    world.steps_to_run.pop()
    if not world.steps_to_run:
        world.steps_to_run = None

    world.record_printscreen = True

@after.each_scenario
def check_that_no_loop_is_open(scenario):
    if scenario.passed and world.steps_to_run is not None:
        raise UnifieldException("A loop is not closed in your scenario")
#}%}

# Selenium management {%{
@before.all
def connect_to_db():

    #WARNING: we need firefox at least Firefox 43. Otherwise, AJAX call seem to be asynchronous
    from selenium.webdriver.firefox.options import Options
    from selenium.webdriver.firefox.firefox_binary import FirefoxBinary

    base_dir = os.path.dirname(__file__)
    file_path = os.path.join(base_dir, FILE_DIR)

    # we have to clean the environment variables, otherwise Firefox crash with the following
    #  error message: SQLite Version Error
    if 'DYLD_FORCE_FLAT_NAMESPACE' in os.environ:
        del os.environ['DYLD_FORCE_FLAT_NAMESPACE']

    if 'BROWSER' not in os.environ or os.environ['BROWSER'] == "firefox":
        # we are going to download all the files in the file directory
        profile = webdriver.FirefoxProfile()
        profile.set_preference('browser.download.folderList', 2)
        profile.set_preference('browser.download.manager.showWhenStarting', False)
        profile.set_preference('browser.download.dir', file_path)
        profile.set_preference('browser.helperApps.neverAsk.saveToDisk','application/vnd.ms-excel')
        #### If you want to use the gecko driver (the new tool by the Mozilla fundation to
        ####  run interface Selenium with Firefox) you should uncomment these three lines
        ####  and comment the line below. It cannot be used with Firefox 47.
        # caps = DesiredCapabilities.FIREFOX
        # caps["marionette"] = True
        # world.browser = webdriver.Firefox(firefox_profile=profile, capabilities=caps)
        
        world.browser = webdriver.Firefox(firefox_profile=profile)

        
    elif os.environ['BROWSER'] == "chrome":
        world.browser = webdriver.Chrome()
        #FIXME: PhantomJS doesn't like testfield. It seems that keeps on loading pages...
        #elif os.environ['BROWSER'] == "phantomjs":
        #world.browser = webdriver.PhantomJS()
    else:
        raise UnifieldException("Unknown browser: %s" % os.environ["BROWSER"])

    # say if a step involves buttons in the side bar or the menu
    #  (we should show the whole printscreen in that case)
    world.full_printscreen = False
    # the name of the current instance (None if not logged in)
    world.current_instance = None

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

    world.must_fail = None

    def incr_func(param):
        m = re.search('\d+$', param)
        if m is None:
            return param
        number = m.group()
        new_number = '%%0%sd' % len(number) % (int(number) + 1)
        return param[:-len(number)] + new_number

    def now_date(param):
        #TODO: Set the right date when running the scenarios
        #  (not only the DB and UniField)
        now_scenario = datetime.datetime.now()
        the_date = now_scenario.strftime(param)
        return the_date

    world.FUNCTIONS = {'INCR': incr_func, 'NOW': now_date}

# Dirty hack to display an error message when a step goes wrong in the background {%{
@before.each_background
def do_not_crash(background):
    world.must_fail = None

@before.each_feature
def init_id_feature(feature):
    world.idfeature = get_new_id(RUN_FEATURE_NUMBER_FILE)

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
            world.browser.save_screenshot('failure_%d_%d.png' % (world.SCENARIO_VARIABLE['ID'], world.nofailure))
        except:
            pass

@before.each_scenario
def update_idrun(scenario):
    world.SCENARIO_VARIABLE = {}

    world.SCENARIO_VARIABLE['ID'] = get_new_id(RUN_NUMBER_FILE)
    world.SCENARIO_VARIABLE['IDFILE'] = world.idfeature

    base_dir = os.path.dirname(__file__)
    file_path = os.path.join(base_dir, FILE_DIR)
    # we have to set the path for the files
    world.SCENARIO_VARIABLE['FILES'] = file_path

@after.each_scenario
def remove_iframes(scenario):
    world.nbframes = 0

@after.all
def disconnect_to_db(total):

    if not os.path.isdir(RESULTS_DIR):
        os.mkdir(RESULTS_DIR)

    printscreen_path = os.path.join(RESULTS_DIR, "last_screen.png")
    content_path = os.path.join(RESULTS_DIR, "last_content.html")

    world.browser.save_screenshot(printscreen_path)

    content = world.browser.page_source
    f = open(content_path, 'w')
    f.write(content.encode('utf-8'))
    f.close()

    # we close the current window, but other windows might be open
    world.browser.close()
    world.browser.quit()

@before.each_feature
def save_all_files(feature):
    # we have to save the files in the directory to remove those who are not
    #  useful anymore
    base_dir = os.path.dirname(__file__)
    file_path = os.path.join(base_dir, FILE_DIR)
    world.files_before = os.listdir(file_path) if os.path.isdir(file_path) else set([])

@after.each_feature
def debug_scenarios(feature):
    base_dir = os.path.dirname(__file__)
    file_path = os.path.join(base_dir, FILE_DIR)
    files_after = os.listdir(file_path) if os.path.isdir(file_path) else set([])

    files_to_delete = set(files_after) - set(world.files_before)

    for filename in files_to_delete:
        file_to_delte = os.path.join(file_path, filename)

        try:
            os.unlink(file_to_delte)
        except OSError as e:
            pass

@after.all
def debug_scenarios(total):
    for scenario_result in total.scenario_results:
        scenario = scenario_result.scenario
        if scenario_result.passed:
            print scenario.name, ": OK"
        else:
            print scenario.name, ": FAILED"

#}%}

# Log into/out of/restore an instance{%{

@step('I go on the homepage')
@handle_delayed_step
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
	# be careful to handle both 2.1-3 and previous versions
	password_textinputs = get_elements(world.browser, tag_name="input", id_attr="show_password")
        if len(password_textinputs) == 0:
		# it is older than 2.1-3, so look for password
        	password_textinputs = get_elements(world.browser, tag_name="input", id_attr="password")

	# same for submit_inputs: it is sensitive to version
        submit_inputs = get_elements(world.browser, tag_name="button", attrs={'type': 'submit'})
	if len(submit_inputs) == 0:
		# it is 2.1-3 or after
		submit_inputs = get_elements(world.browser, tag_name="button", attrs={'onclick': 'disable_save()'})

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

    world.current_instance = database_name

@step('I log into instance "([^"]*)" as "([^"]*)" with password "([^"]*)"')
@handle_delayed_step
@output.register_for_printscreen
def connect_on_database(step, database_name, username, password):
    log_into(database_name, username, password)
    world.current_instance = database_name

@step('I log into instance "([^"]*)"')
@handle_delayed_step
@output.register_for_printscreen
def connect_on_database(step, database_name):
    log_into(database_name, UNIFIELD_ADMIN, UNIFIELD_PASSWORD)
    world.current_instance = database_name

@step('I log out')
@handle_delayed_step
@output.add_printscreen
def log_out(step):
    world.browser.get("%(url)s/openerp/logout" % dict(url=HTTP_URL_SERVER))
    world.current_instance = None

#}%}

# Synchronisation {%{

@step('I synchronize "([^"]*)"')
@handle_delayed_step
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
        conn_obj.write(conn_ids, {'login': UNIFIELD_ADMIN, 'password': UNIFIELD_PASSWORD, 'port': XMLRPC_PORT, 'protocol': 'xmlrpc'})
        conn_obj.connect(conn_ids)
        sync_ids = sync_obj.search([])
        sync_obj.sync(sync_ids)
    except RPCError as e:
        message = str(e).encode('utf-8', 'ignore')

        #FIXME: This is a dirty hack. We don't want to fail if there is a revision
        #  available. That's part of a normal scenario. As a result, the code
        #  shouldn't raise an exception.
        if 'revision(s) available' in message:
            return

        raise
#}%}

# Open a menu/tab {%{
@step('I open tab menu "([^"]*)"')
@handle_delayed_step
@output.register_for_printscreen
def open_tab(step, tab_to_open):
    world.full_printscreen = True
    world.browser.get("%(url)s/" % dict(url=HTTP_URL_SERVER))

    # we cannot click on the menu because it's sometimes hidden by a low resolution
    btn_web_dashboard = get_element_from_text(world.browser, tag_name="li", text=tab_to_open, class_attr="web_dashboard", wait="Cannot find tab menu %s" % tab_to_open)
    btn_web_dashboard.click()

    wait_until_not_loading(world.browser, wait="We cannot open fully tab menu '%s'. Something is still processing" % tab_to_open)

@step('I open accordion menu "([^"]*)"')
@handle_delayed_step
@output.register_for_printscreen
def open_tab(step, menu_to_click_on):
    world.full_printscreen = True
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
    # we have to wait for the page refresh. It sometimes happen when we close a window and it refreshes
    #  the main "frame". If we click on a menu, it doesn't seem to be taken into account
    wait_until_not_loading(world.browser, wait="It seems that the current process is still executing")

    menu_node = get_element(world.browser, tag_name="td", id_attr="secondary")

    menus = menu_to_click_on.split("|")

    after_pos = 0
    i = 0

    tick = monitor(world.browser)
    while i < len(menus):
        menu = menus[i]
        tick()

        elements = get_elements(menu_node, tag_name="tr", class_attr="row")
        # We don't know why... but some elements appear to be empty when we start using the menu
        #  then, they disapear when we open a menu

        elements = filter(lambda x : x.text.strip() != "" and x.text.strip() != "Toggle Menu", elements)
        visible_elements = filter(lambda x : x.is_displayed(), elements)
        valid_visible_elements = visible_elements[after_pos:]

        text_in_menus = map(lambda x : x.text, valid_visible_elements)

        if menu in text_in_menus:
            pos = text_in_menus.index(menu)

            if i == len(menus)-1:
                valid_visible_elements[pos].click()
            else:
                # Do we have to click on the small caret to open the submenu
                #  and not the menu itself. Otherwise, we could open a
                #  window that is linked to an parent menu.
                # We also have to click on the caret to close the menu otherwise the number
                #  of submenu entries won't change and we will be stuck while waiting for a change
                carets_element_expand = get_elements(valid_visible_elements[pos], tag_name="span", class_attr="expand")
                carets_element_collapse = get_elements(valid_visible_elements[pos], tag_name="span", class_attr="collapse")
                if carets_element_expand or carets_element_collapse:
                    (carets_element_expand + carets_element_collapse)[0].click()
                else:
                    # there is no caret, so we can click on the menu (there is no submenu)
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
@handle_delayed_step
@output.register_for_printscreen
def open_tab(step, menu_to_click_on):
    world.full_printscreen = True
    open_menu(menu_to_click_on)

    # we have to open the window!
    world.browser.switch_to_default_content()
    world.browser.switch_to_frame(get_element(world.browser, tag_name="iframe", position=world.nbframes, wait="Cannot find the window"))
    world.nbframes += 1
    wait_until_no_ajax(world)

@step('I click on menu "([^"]*)"$')
@handle_delayed_step
@output.register_for_printscreen
def open_tab(step, menu_to_click_on):
    world.full_printscreen = True

    open_menu(menu_to_click_on)

@step('I open tab "([^"]*)"')
@handle_delayed_step
@output.add_printscreen
def open_tab(step, tabtoopen):
    msg = "Cannot find tab %s" % tabtoopen
    click_on(world, lambda : get_element_from_text(world.browser, class_attr="tab-title", tag_name="span", text=tabtoopen, wait=msg), msg)
    wait_until_not_loading(world.browser, wait="Cannot open the tab. Loading takes too much time")

#}%}

# Fill fields {%{

def internal_fill_field(fieldname, content, position=0):

    content = convert_input(world, content)

    # Most of the fields use IDs, however, some of them are included in a table with strange fields.
    #  We have to look for both
    idattr, my_input = get_input(world.browser, fieldname, position=position)

    if my_input.tag_name == "select":
        select = Select(my_input)
        select.select_by_visible_text(content)

        wait_until_no_ajax(world)

        # we cannot use the get_element_from_text because this method doesn't
        #  detect html entities that "look like space"
        the_option = None
        for option in get_elements(my_input, tag_name="option"):
            if content == option.text:
                the_option = option

        if the_option is None:
            raise UniFieldElementException("No option %s found in the select field" % content)
        the_option.click()
    elif my_input.tag_name == "input" and my_input.get_attribute("type") == "file":
        base_dir = os.path.dirname(__file__)
        content_path = os.path.join(base_dir, FILE_DIR, content)

        if not os.path.isfile(content_path):
            raise UniFieldElementException("%s is not a file" % content_path)

        # we have to check if we have to inject the local variables in this file (only for text files)
        filename, ext = os.path.splitext(content)

        if ext.lower() in ['.xml', '.xls', '.xlsx', '.csv']:
            try:
                #FIXME: We hope that this file is not too big
                lines = open(content_path, 'r').readlines()
                new_content = ''
                for row_number, line in enumerate(lines):
                    localdict = dict(ROW=str(row_number))
                    new_content += convert_input(world, line, localdict)

                base_dir = os.path.dirname(__file__)
                realfilename = '%s%s' % (TEMP_FILENAME, ext.lower())
                content_path = os.path.join(base_dir, FILE_DIR, realfilename)
                f = open(content_path, 'w')
                f.write(new_content)
                f.close()
            except (OSError, IOError) as e:
                raise Exception("Unable to inject local variables in %s (reason: %s)" % (content, str(e)))

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

@step('I fill "([^"]*)" with "([^"]*)"$')
@handle_delayed_step
@output.register_for_printscreen
def fill_field(step, fieldname, content):
    refresh_window(world)
    repeat_until_no_exception(world, internal_fill_field, StaleElementReferenceException, fieldname, content, position=0)

@step('I fill:$')
@handle_delayed_step
@output.register_for_printscreen
def fill_set_of_fields(step):
    refresh_window(world)

    import collections
    pos_by_label = collections.defaultdict(lambda : 0)

    for field in step.hashes:
        if 'label' not in field:
            raise UniFieldElementException("You have to set the label for each value")
        if 'value' not in field:
            raise UniFieldElementException("You have to set the label for each value")

        current_pos = pos_by_label[field['label']]

        idattr, my_input = get_input(world.browser, field['label'], position=current_pos)

        internal_fill_field(field['label'], field['value'], position=current_pos)

        pos_by_label[field['label']] += 1

@step('I fill "([^"]*)" with "([^"]*)" and open the window$')
@handle_delayed_step
@output.register_for_printscreen
def fill_field_and_open(step, fieldname, content):
    refresh_window(world)
    internal_fill_field(fieldname, content, position=0)

    world.browser.switch_to_default_content()
    world.browser.switch_to_frame(get_element(world.browser, position=world.nbframes, tag_name="iframe", wait="I don't find the new window"))
    world.nbframes += 1

    wait_until_no_ajax(world)

@step('I store the downloaded file as "([^"]*)" when (.*)$')
@handle_delayed_step
def store_last_file(step, to_filename, other_step):
    import os.path
    import os

    base_dir = os.path.dirname(__file__)
    file_path = os.path.join(base_dir, FILE_DIR)

    tick = monitor(world.browser, "No new file found")

    files_before = os.listdir(file_path) if os.path.isdir(file_path) else set([])

    before = world.steps_to_run
    world.steps_to_run = None

    step.given(other_step)

    world.steps_to_run = before

    while True:
        files_after = os.listdir(file_path) if os.path.isdir(file_path) else set([])

        files_in_addition = set(files_after) - set(files_before)

        if not files_in_addition:
            tick()
            continue

        if len(files_in_addition) > 1:
            raise Exception("There are more than one new files: %s" % ', '.join(files_in_addition))

        newest_filename = list(files_in_addition)[0]

        to_path = os.path.join(file_path, to_filename)
        if os.path.exists(to_path):
            os.unlink(to_path)

        from_path = os.path.join(file_path, newest_filename)

        os.rename(from_path, to_path)

        break

@step('I fill "([^"]*)" with table:$')
@handle_delayed_step
@output.register_for_printscreen
def fill_field_table(step, fieldname):
    if not step.hashes:
        raise UniFieldElementException("Why don't you define at least one row?")

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
            elif re.match('^\d+(\.\d+)?$', cell) is not None:
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
@handle_delayed_step
def remember_step_in_table(step, column_name, variable):
    refresh_window(world)

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
            world.SCENARIO_VARIABLE[variable.strip()] = td_node.text.strip()
            return

    raise UnifieldException("No line with column %s has been found" % column_name)

@step('I store "([^"]*)" in "([^"]*)"$')
@handle_delayed_step
def remember_step(step, fieldname, variable):

    values = get_values(fieldname)

    if not values:
        raise UniFieldElementException("No field named %s" % fieldname)
    elif len(values) > 1:
        raise UniFieldElementException("Several values found for %s (values: %s)" % (fieldname, ', '.join(values)))

    validate_variable(variable.strip())
    world.SCENARIO_VARIABLE[variable.strip()] = values[0].strip()

#}%}

# Active waiting {%{

@step('I click on "([^"]*)" until not available$')
@handle_delayed_step
def click_until_not_available2(step, button):
    refresh_window(world)
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
@handle_delayed_step
def click_until_not_available1(step, button, value, fieldname):
    refresh_window(world)

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

# }%}

# I click on ... {%{
# I click on "Search/New/Clear"

@step('(.*) if a window is open$')
@handle_delayed_step
def if_a_window_is_open(step, nextstep):
    if world.nbframes > 0:
        step.given(nextstep)

@step('I click on "([^"]*)" and close the window if necessary$')
@handle_delayed_step
@output.add_printscreen
def close_window_if_necessary(step, button):
    refresh_window(world)

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
    click_on(world, lambda : get_element_from_text(world.browser, tag_name=["button", "a"], text=button, wait=msg), msg)

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
                # We have to ensure that the URL changes. If it's the case, then we can continue with this new window.
                #  Otherwise, it means that it's still the previous window.
                world.browser.switch_to_frame(get_element(world.browser, position=world.nbframes-1, tag_name="iframe", wait="I cannot find the new window"))
                return

            time.sleep(TIME_TO_SLEEP)

        except (StaleElementReferenceException, ElementNotVisibleException):
            pass

@step('I click on "([^"]*)"$')
@handle_delayed_step
@output.add_printscreen
def click_on_button(step, button):
    refresh_window(world)
    # It seems that some action could still be launched when clicking on a button,
    #  we have to wait on them for completion
    # But we cannot do that for frames because the "loading" menu item doesn't exist
    #  at that time.

    if world.current_instance is not None:
        wait_until_not_loading(world.browser, wait=world.nbframes == 0)
    else:
        # But we have to take into account that such element doesn't exist when a user is not logged in...
        wait_until_not_loading(world.browser, wait=False)

    # we have an issue when the user is not logged in... the important buttons are "at the end of the page". We have to
    #  fetch them in another order
    position_element = 0 if world.current_instance is not None else -1
    msg = "Cannot find button %s" % button
    click_on(world, lambda : get_elements_from_text(world.browser, tag_name=["button", "a"], text=button, wait=msg)[position_element], msg)

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
@handle_delayed_step
@output.add_printscreen
def click_on_button_and_open(step, button):
    refresh_window(world)

    wait_until_not_loading(world.browser, wait=False)
    wait_until_no_ajax(world)
    msg = "Cannot find button %s" % button

    click_on(world, lambda : get_element_from_text(world.browser, tag_name=["button", "a"], text=button, wait=msg), msg)

    wait_until_not_loading(world.browser, wait=False)

    world.browser.switch_to_default_content()
    world.browser.switch_to_frame(get_element(world.browser, position=world.nbframes, tag_name="iframe", wait="I don't find the new window"))
    world.nbframes += 1
    
    wait_until_no_ajax(world)

@step('I close the window$')
@handle_delayed_step
@output.add_printscreen
def close_the_window(step):
    refresh_window(world)

    world.browser.switch_to_default_content()

    elem = get_element_from_text(world.browser, tag_name="span", text="close", wait="Cannot find the button to close the window")
    elem.click()

    world.nbframes -= 1
    if world.nbframes > 0:
        world.browser.switch_to_frame(get_element(world.browser, position=world.nbframes-1, tag_name="iframe", wait="I don't find the previous window"))
    else:
        wait_until_element_does_not_exist(world.browser, lambda : get_element(world.browser, tag_name="iframe", position=world.nbframes))

# I click on "Save & Close"

@step('I click on "([^"]*)" and close the window$')
@handle_delayed_step
@output.add_printscreen
def click_on_button_and_close(step, button):
    '''
    refresh_window(world)

    msg = "Cannot find the button to close the window"
    click_on(world, lambda : get_element_from_text(world.browser, tag_name=["button", "a"], text=button, wait=msg), msg)
    world.nbframes -= 1

    world.browser.switch_to_default_content()
    
    if world.nbframes > 0:
        world.browser.switch_to_frame(get_element(world.browser, position=world.nbframes-1, tag_name="iframe", wait="I don't find the previous window"))
    else:
        #wait_until_element_does_not_exist(world.browser, lambda : get_element(world.browser, tag_name="iframe", position=world.nbframes))
        wait_until_element_does_not_exist(world.browser, lambda : get_element(world.browser, tag_name="div", class_attr="ui-dialog", position=world.nbframes))
    
    #wait_until_not_loading(world.browser)
    wait_until_no_ajax(world)
    '''
    
    refresh_nbframes(world)
    refresh_window(world)
    
    msg = "Cannot find the button to close the window"
    button_element = get_element_from_text(world.browser, tag_name=["button", "a"], text=button, wait=msg)
    click_on(world, lambda : button_element, msg)
    
    world.browser.switch_to_default_content()
    
    try:
        wait_until_element_does_not_exist(world.browser, lambda : get_element(world.browser, tag_name="iframe", position=world.nbframes-1))
    except (TimeoutException) as e:
        
        # in case of TimeoutException, let's try one another time.
        button_element = get_element_from_text(world.browser, tag_name=["button", "a"], text=button, wait=msg)
        click_on(world, lambda : button_element, msg)
        wait_until_element_does_not_exist(world.browser, lambda : get_element(world.browser, tag_name="iframe", position=world.nbframes-1))
        
    refresh_nbframes(world)
    refresh_window(world)
    
    wait_until_not_loading(world.browser, wait=False)
        

def toggle_button_to(btn_name, check):
    
    btn_name = to_camel_case(btn_name)
    msg = "Cannot find toggle button %s" % btn_name
    
    btn_toggle = get_element_from_text(world.browser, tag_name="button", text=btn_name, wait=msg)
    
    #Check only with the word "inactive" in the button class name because "active" is included in "inactive" 
    if check == "active" and "inactive" in btn_toggle.get_attribute("class"):
        click_on(world, lambda : btn_toggle, msg)
    elif check == "inactive" and "inactive" not in btn_toggle.get_attribute("class"):
        click_on(world, lambda : btn_toggle, msg)
        
    wait_until_not_loading(world.browser)
    wait_until_no_ajax(world)

@step('I toggle on "([^"]*)"$')
@handle_delayed_step
@output.register_for_printscreen
def toggle_on(step, button):
    toggle_button_to(button, "active")

@step('I toggle off "([^"]*)"$')
@handle_delayed_step
@output.register_for_printscreen
def toggle_off(step, button):
    toggle_button_to(button, "inactive")

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
@handle_delayed_step
@output.register_for_printscreen
def should_see(step, content, fieldname):
    refresh_window(world)

    wait_until_not_loading(world.browser, wait=False)

    content = convert_input(world, content)
    reg = create_regex(content)

    tick = monitor(world.browser)

    while True:
        
        content_found = get_values(fieldname)
        error = None

        if not content_found:
            error = "No field named %s" % fieldname
        elif len(content_found) > 1:
            error = "Several values found for %s (values: %s)" % (fieldname, ', '.join(content_found))

        if re.match(reg, content_found[0], flags=re.DOTALL) is None:
            error = "%s doesn't contain %s (values found: %s)" % (fieldname, content, ', '.join(content_found))

        if error is None:
            break

        tick(message_if_error=error)

@step('I should see a text status with "([^"]*)"')
@handle_delayed_step
@output.register_for_printscreen
def see_status(step, message_to_see):
    wait_until_not_loading(world.browser)
    tick = monitor(world.browser)
    found = False

    reg = create_regex(message_to_see)

    while not found:
        elements = get_elements(world.browser, tag_name="tr", id_attr="actions_row")
        elements += get_elements(world.browser, tag_name="td", class_attr="item-htmlview")
        options = []

        for element in elements:
            if re.match(reg, element.text, flags=re.DOTALL):
                found = True
                break
            else:
                options.append(element.text)

        if not found:
            time.sleep(TIME_TO_SLEEP)
            msg = "No '%s' found among %s" % (message_to_see, ', '.join(options))
            tick(msg)


@step('I should see a popup with "([^"]*)"$')
@handle_delayed_step
@output.register_for_printscreen
def see_popup(step, message_to_see):

    wait_until_not_loading(world.browser)
    tick = monitor(world.browser, "I don't find any popup")

    message_found = False

    while not message_found:

        for noframe in xrange(world.nbframes+1):
            if noframe == 0:
                world.browser.switch_to_default_content()
            else:
                frame = get_element(world.browser, tag_name="iframe", position=noframe-1, wait="I don't find a window")
                world.browser.switch_to_frame(frame)

            wait_until_not_loading(world.browser)

            elements = get_elements(world.browser, tag_name="td", class_attr="error_message_content")

            if elements:
                elem = elements[0]
                reg = create_regex(message_to_see)

                if re.match(reg, elem.text, flags=re.DOTALL) is None:
                    print "No '%s' found in '%s'" % (message_to_see, elem.text)
                    raise UniFieldElementException("No '%s' found in '%s'" % (message_to_see, elem.text))

                # we cannot click on OK because the button might be hidden by another window
                # We are going to try to close the popup by the good way
                world.browser.execute_script('$("a#fancybox-close").click();')
                
                # If the popup is not closed, we try the bad way
                world.browser.execute_script('if($("div#fancybox-wrap").is(":visible")){$("div#fancybox-overlay, div#fancybox-wrap").hide();}')
                

                wait_until_element_does_not_exist(world.browser, lambda : get_element(world.browser, tag_name="td", class_attr="error_message_content"))

                message_found = True
                break
            else:
                tick()

    if world.nbframes:
        world.browser.switch_to_default_content()
        world.browser.switch_to_frame(get_element(world.browser, tag_name="iframe", position=world.nbframes-1, wait="I don't find the previous window"))
    else:
        world.browser.switch_to_default_content()


@step('I should see a window with "([^"]*)"$')
@handle_delayed_step
@output.register_for_printscreen
def see_window(step, message_to_see):
       
    tick = monitor(world.browser, "I don't find any window")

    # Variables initialization
    message_found = False
    reg = create_regex(message_to_see)
    
    # We're going to check in browser and iFrames
    for noframe in xrange(world.nbframes+1):
        
        # Check in browser
        if noframe == 0:
            world.browser.switch_to_default_content()
        # Check in iFrame
        else:
            frame = get_element(world.browser, tag_name="iframe", position=noframe-1, wait="I don't find a window")
            world.browser.switch_to_frame(frame)
    
        # We are looking for all textarea in the window
        elements = world.browser.find_elements_by_css_selector("form#view_form table.fields textarea")
        
        # If at least one element has been found 
        if elements:
            
            for element in elements:
    
                # Compare element text en text we are looking for
                if re.match(reg, element.text, flags=re.DOTALL) is None:
                    continue
                else:
                    message_found = True
                    break
        
    # Not found, raise an error
    if not message_found:
        raise UniFieldElementException("No '%s' found" % (message_to_see))
    
    # Close the window
    step.given('I close the window')

    #if world.nbframes:
    #    world.browser.switch_to_default_content()
    #    world.browser.switch_to_frame(get_element(world.browser, tag_name="iframe", position=world.nbframes-1, wait="I don't find the previous window"))
    #else:
    #    world.browser.switch_to_default_content()

#WARNING: Undocumented!
@step('I should see "([^"]*)" in the section "([^"]*)"$')
@handle_delayed_step
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

def get_pos_for_fieldname_4_editon(fieldname):

    tick = monitor(world.browser)
    while True:
        table_found = None
        right_pos = None

        tick()
        # A new table is sometimes created
        try:
            gridtables = get_elements(world.browser, tag_name="table", class_attr="grid")
            found = False

            for gridtable in gridtables:
                # We have to ensure that the row is editable, otherwise we have to look
                #  for another table
                if not get_elements(gridtable, tag_name="tr", class_attr="editors", wait=False):
                    continue

                right_pos = get_column_position_in_table(gridtable, fieldname)

                # we have to wait on the table to be editable (or at least one row)
                if right_pos is not None:
                    table_found = gridtable
                    found = True
                    break

            if found:
                break

            time.sleep(TIME_TO_SLEEP)

        except StaleElementReferenceException as e:
            print e
            pass

    if right_pos is None:
        raise UniFieldElementException("Cannot find column '%s'" % fieldname)
    
    return table_found, right_pos

def check_checkbox_action(content, fieldname, action=None):

    content = convert_input(world, content)

    table_found, right_pos = get_pos_for_fieldname_4_editon(fieldname)

    def get_text_box():
        row_in_edit_mode = get_element(table_found, tag_name="tr", class_attr="editors", wait="I don't find any line to edit")

        td_node = get_element(row_in_edit_mode, class_attr="grid-cell", tag_name="td", position=right_pos)

        # do we a select at our disposal?
        a_select = get_elements(td_node, tag_name="select")
        use_select = False

        if bool(a_select):
            # we have to check that the action is contained
            for elem in a_select[0].find_elements_by_tag_name("option"):
                if elem.text.strip().lower() == content.lower():
                    use_select = True

        if use_select:
            return a_select[0], action or action_select_option
        else:
            input_type = "text" if get_elements(td_node, tag_name="input", attrs={'type': 'text'}) else "checkbox"
            my_input = get_element(td_node, tag_name="input", attrs={'type': input_type})

            return my_input, action or action_write_in_element

    select_in_field_an_option(world, get_text_box, content)

@step('I fill "([^"]*)" within column "([^"]*)"$')
@handle_delayed_step
@output.register_for_printscreen
def fill_column(step, content, fieldname):
    refresh_window(world)
    repeat_until_no_exception(world, check_checkbox_action, StaleElementReferenceException, content, fieldname)

@step('I fill "([^"]*)" within column "([^"]*)" and open the window')
@handle_delayed_step
@output.register_for_printscreen
def fill_column_with_window(step, content, fieldname):
    refresh_window(world)
    fill_column(step, content, fieldname)

    wait_until_no_ajax(world)
    wait_until_not_loading(world.browser, wait=False)

    world.browser.switch_to_default_content()
    world.browser.switch_to_frame(get_element(world.browser, tag_name="iframe", position=world.nbframes, wait="I don't find the new window"))
    world.nbframes += 1

    wait_until_no_ajax(world)

@step('I tick all the lines')
@handle_delayed_step
@output.register_for_printscreen
def click_on_all_line(step):
    refresh_window(world)

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
@handle_delayed_step
@output.add_printscreen
def click_on_line_line(step):
    refresh_window(world)
    click_on_line(step, "line")

@step('I click "([^"]*)" on line:')
@handle_delayed_step
@output.register_for_printscreen
def click_on_line_tooltip(step, action):
    refresh_window(world)
    click_on_line(step, action)

@step('I click "([^"]*)" on line and close the window:')
@handle_delayed_step
@output.add_printscreen
def click_on_line_and_open_the_window(step, action):

    if len(step.hashes) != 1:
        raise UnifieldException("You should click only on one line to close the window")
    refresh_window(world)

    click_on_line(step, action, window_will_exist=False)

    world.nbframes -= 1

    world.browser.switch_to_default_content()

    wait_until_no_ajax(world)

    wait_until_element_does_not_exist(world.browser, lambda : get_element(world.browser, tag_name="iframe", position=world.nbframes))

    if world.nbframes > 0:
        world.browser.switch_to_frame(get_element(world.browser, position=world.nbframes-1, tag_name="iframe", wait="I don't find the previous window"))

    wait_until_no_ajax(world)
    wait_until_not_loading(world.browser, wait=world.nbframes == 0)

@step('I click "([^"]*)" on line and open the window:')
@handle_delayed_step
@output.add_printscreen
def click_on_line_and_open_the_window(step, action):
    refresh_window(world)
    click_on_line(step, action)

    world.browser.switch_to_default_content()
    world.browser.switch_to_frame(get_element(world.browser, tag_name="iframe", position=world.nbframes, wait="I don't find the new window"))
    world.nbframes += 1

    wait_until_no_ajax(world)

def check_that_line(step, should_see_lines, action=None):
    values = step.hashes

    open_all_the_tables(world)

    def try_to_check_line(step):

        refresh_window(world)

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
@handle_delayed_step
@output.register_for_printscreen
def check_line(step):
    refresh_window(world)
    check_that_line(step, True)

@step("I shouldn't be able to click \"([^\"]*)\"")
@handle_delayed_step
@output.register_for_printscreen
def check_not_click_on_line(step, action):
    refresh_window(world)

    # we have an issue when the user is not logged in... the important buttons are "at the end of the page". We have to
    #  fetch them in another order
    msg = "This button is still available and might be clicked on %s" % action
    tick = monitor(world.browser, msg)

    while True:
        elements = get_elements_from_text(world.browser, tag_name=["button", "a"], text=action, wait=None)
        # we have to ensure that the button is clickable. Otherwise it means that the steps
        #  is "done"
        
        # we sometimes fetch node nested in the button or a area. We have to fetch the parent
        real_elements = []
        for element in elements:
            if element.tag_name in ["button", "a"]:
                real_elements.append(element.tag_name)
            else:
                table_node = element.find_elements_by_xpath("ancestor::button[1]|ancestor::a[1]")
                real_elements.append(table_node[0])
        real_elements = filter(lambda x : not x.get_attribute("readonly") and not x.get_attribute("disabled"), real_elements)

        if real_elements:
            time.sleep(TIME_TO_SLEEP)
            tick()
        else:
            break

@step("I shouldn't be able to click \"([^\"]*)\" on line:")
@handle_delayed_step
@output.register_for_printscreen
def check_not_click_on_line(step, action):
    refresh_window(world)

    if len(step.hashes) != 1:
        raise UniFieldElementException("You should define what is the line unique line you want to click on")

    # (1) we check that the line exists
    check_that_line(step, True)

    # (2) but we shouldn't be able to click on it
    check_that_line(step, False, action=action)

@step("I shouldn't be able to edit \"([^\"]*)\"$")
@handle_delayed_step
@output.register_for_printscreen
def should_be_able_to_edit(step, fieldname):
    refresh_window(world)

    _, my_input = get_input(world.browser, fieldname)

    if not my_input.get_attribute("readonly") and not my_input.get_attribute("disabled"):
        raise UniFieldElementException("The field %s is ediable" % fieldname)

@step("I shouldn't be able to edit column \"([^\"]*)\"$")
@handle_delayed_step
@output.register_for_printscreen
def should_not_be_able_to_edit(step, fieldname):
    refresh_window(world)

    def action_check(txt_input, content):
        if not txt_input.get_attribute("readonly") and not txt_input.get_attribute("disabled"):
            raise UniFieldElementException("The field %s is ediable" % fieldname)

    check_checkbox_action("", fieldname, action_check)

@step('I should not see in the main table the following data:')
@handle_delayed_step
@output.register_for_printscreen
def check_line(step):
    refresh_window(world)
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
        refresh_window(world)
        step.given('I click on "%s"' % action_search)
        time.sleep(TIME_TO_WAIT)
        tick()

@step('I click "([^"]*)" until I don\'t see:')
@handle_delayed_step
def click_on_search_until_not(step, action_search):
    search_until_I(step, action_search, False)

@step('I click "([^"]*)" until I see:')
@handle_delayed_step
def click_on_search_until(step, action_search):
    search_until_I(step, action_search, True)


def open_side_panel_internal(step, menuname):
    wait_until_no_ajax(world)
    wait_until_not_loading(world.browser)

    if world.nbframes != 0:
        raise UniFieldElementException("You cannot open the side panel if you have just opened a window")

    # sometimes the click is not done (or at least the side panel doesn't open...)
    #  it seems that this is related to a new
    element = get_element(world.browser, id_attr="a_main_sidebar", wait="I don't find the side bar")
    tick = monitor(world.browser)
    while 'closed' in element.get_attribute("class"):
        tick()
        script = "$('#%s').click()" % element.get_attribute("id")
        world.browser.execute_script(script)

    elem = get_element_from_text(world.browser, tag_name="a", text=menuname, wait="Cannot find menu '%s' in the side panel" % menuname)
    elem.click()

    wait_until_not_loading(world.browser)

@step('I click "([^"]*)" in the side panel$')
@handle_delayed_step
@output.add_printscreen
def open_side_panel(step, menuname):
    open_side_panel_internal(step, menuname)

@step('I click "([^"]*)" in the side panel and open the window$')
@handle_delayed_step
@output.add_printscreen
def open_side_panel_and_open(step, menuname):

    open_side_panel_internal(step, menuname)

    world.browser.switch_to_default_content()
    world.browser.switch_to_frame(get_element(world.browser, tag_name="iframe", position=world.nbframes, wait="I don't find the new window"))
    world.nbframes += 1

    wait_until_no_ajax(world)

def do_action_and_open_popup(world, action, *params, **vparams):

    handles_before = set(world.browser.window_handles)

    action(*params, **vparams)

    world.nbframes = 0

    # we have to wait to select the new popup
    tick = monitor(world.browser, "I don't see the new popup")

    while True:
        handles_after = set(world.browser.window_handles)
        new_handles = handles_after - handles_before

        # have we found a new popup?
        if new_handles:
            for previous_handle in handles_before:
                world.browser.switch_to.window(previous_handle)
                world.browser.close()

            new_handles = list(new_handles)
            new_handle = new_handles[0]
            world.browser.switch_to.window(new_handle)
            world.nbframes = 0
            break

        time.sleep(TIME_TO_SLEEP)

@step('I click on "([^"]*)" and open the popup$')
@handle_delayed_step
@output.add_printscreen
def open_side_panel_and_open_popup(step, button):
    refresh_window(world)

    def click_on_button(step, button):
        position_element = 0 if world.current_instance is not None else -1
        msg = "Cannot find button %s" % button
        click_on(world, lambda : get_elements_from_text(world.browser, tag_name=["button", "a"], text=button, wait=msg)[position_element], msg)

    do_action_and_open_popup(world, click_on_button, step, button)


@step('I click "([^"]*)" in the side panel and open the popup$')
@handle_delayed_step
@output.add_printscreen
def open_side_panel_and_open_popup(step, menuname):
    refresh_window(world)

    def open_side_panel_popup(step, menuname):
        open_side_panel(step, menuname)
        wait_until_no_ajax(world)

    do_action_and_open_popup(world, open_side_panel_popup, step, menuname)

@step('I debug')
@handle_delayed_step
@output.register_for_printscreen
def i_debug(step):
    import pdb
    pdb.set_trace()
    
@step('I validate the line')
@handle_delayed_step
@output.register_for_printscreen
def choose_field(step):
    refresh_window(world)
    wait_until_no_ajax(world)
    wait_until_not_loading(world.browser)

    click_on(world, lambda : get_element(world.browser, tag_name="img", attrs={'title': 'Update'}, wait=True), "Cannot find the button to validate the line")

    wait_until_no_ajax(world)
    wait_until_not_loading(world.browser)

# Language management {%{


def get_input_for_language_field(language, field):

    table_node = get_element(world.browser, tag_name="table", class_attr="grid", wait="Cannot see the translation table")
    row_header = get_element(table_node, tag_name="tr", class_attr="grid-header", wait="I cannot find the grid header")
    headers = get_elements(row_header, tag_name="td", class_attr="grid-cell")

    if not headers:
        raise UniFieldElementException("No language found")

    # we have to remove the first column which is always the Field
    languages = headers[1:]
    languages = map(lambda x : x.text, languages)
    if language not in languages:
        raise UniFieldElementException("We cannot find the language %s among %s" % (language, ', '.join(languages)))
    position_language = languages.index(language)

    descriptions_found = []

    ret = None

    for row in get_elements(table_node, tag_name="tr", class_attr="grid-row"):
        cells = get_elements(row, tag_name="td", wait="I don't find the given fields")
        field_row = cells[0].text

        if field_row and field_row[-1] == ':':
            field_row = field_row[:-1]

        if field_row == field:
            cell = cells[position_language+1]
            ret = get_element(cell, tag_name="input")
            break
        else:
            descriptions_found.append(field_row)
    else:
        raise UnifieldException("Unable to find the given description %s among %s" % (field, ', '.join(descriptions_found)))
    
    return ret

@step('I set "([^"]*)" for language "([^"]*)" and field "([^"]*)"')
@handle_delayed_step
@output.register_for_printscreen
def set_translation_value(step, value, language, field):
    value = convert_input(world, value)

    elem = get_input_for_language_field(language, field)
    elem.send_keys((100*Keys.BACKSPACE) + value + Keys.TAB)

@step('I should see "([^"]*)" for language "([^"]*)" and field "([^"]*)"')
@handle_delayed_step
@output.register_for_printscreen
def check_translation_value(step, value, language, field):

    value = convert_input(world, value)

    elem = get_input_for_language_field(language, field)

    reg = create_regex(value)

    found = elem.get_attribute("value")

    if re.match(reg, found, flags=re.DOTALL) is None:
        raise UniFieldElementException("I don't find the right value: '%s' found, '%s' expected" % (found, value))

#}%}

@step('I open the translation window for "([^"]*)"')
@handle_delayed_step
@output.register_for_printscreen
def open_translation_window(step, fieldname):

    tick = monitor(world.browser, "I cannot open the translation window for field %s" % fieldname)

    while True:
        try:
            # Most of the fields use IDs, however, some of them are included in a table with strange fields.
            #  We have to look for both
            idattr, my_input = get_input(world.browser, fieldname)

            # it seems that the translation icon is always included in a textbox
            span_textbox = my_input.find_elements_by_xpath("following-sibling::*[1]")

            if not span_textbox or span_textbox[0].get_attribute("class") != "translatable":
                raise UniFieldElementException("We don't find the translation icon for this field")

            span_textbox[0].click()

            break
        except (StaleElementReferenceException, ElementNotVisibleException) as e:
            print e
            pass

        tick()

    # we have to open the window!
    world.browser.switch_to_default_content()
    world.browser.switch_to_frame(get_element(world.browser, tag_name="iframe", position=world.nbframes, wait="Cannot find the window"))
    world.nbframes += 1
    wait_until_no_ajax(world)

#}%}

# Debugging steps {%{
@step('I sleep')
@handle_delayed_step
def selenium_sleeps(step):
    import time
    time.sleep(30000)

@step('I wait$')
@handle_delayed_step
@output.register_for_printscreen
def selenium_sleeps(step):
    raw_input()


@step('I wait "([^"]*)" seconds$')
@handle_delayed_step
def selenium_sleeps(step, seconds):
    #This step is used to instrument UniField. Don't change it!
    import time
    time.sleep(int(seconds))

#}%}

# Time evaluators {%{

@step('I store the time difference in "([^"]*)"')
@handle_delayed_step
def save_time_difference(step, counter):
    step.need_printscreen = False
    now = datetime.datetime.now()

    total_secs = timedelta_total_seconds(now - world.last_measure)
    world.durations[counter] = total_secs

@step('I save the time')
@handle_delayed_step
def save_time(step):
    step.need_printscreen = False
    world.last_measure = datetime.datetime.now()

@step('I store the values for "([^"]*)" in "([^"]*)"')
@handle_delayed_step
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

