
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import Select
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchFrameException, NoSuchElementException, StaleElementReferenceException
import datetime
import time
import re
import os

# The time (in seconds) that we wait when we know that an action has still to be performed
TIME_TO_SLEEP = 0.3
# The time that we wait when we now that a change is almost immediate
TIME_TO_WAIT = 1.0

def prefix_db_name(db_name):
    from credentials import DB_PREFIX
    if DB_PREFIX and not db_name.startswith(DB_PREFIX):
        return '%s_%s' % (DB_PREFIX, db_name)
    return db_name


def get_absolute_path(relative_file):
    path, _ = os.path.split(__file__)
    return os.path.join(path, relative_file)

# the maximum amount of time that we expect to wait on one element
def get_TIME_BEFORE_FAILURE():
    if 'TIME_BEFORE_FAILURE' in os.environ:
        if os.environ['TIME_BEFORE_FAILURE'].isdigit():
            return int(os.environ['TIME_BEFORE_FAILURE'])
        else:
            return None
    else:
        return 50
TIME_BEFORE_FAILURE_SYNCHRONIZATION = 1000.0 if get_TIME_BEFORE_FAILURE() is not None else (3600*24*7)

def timedelta_total_seconds(timedelta):
    return (timedelta.microseconds + 0.0 + (timedelta.seconds + timedelta.days * 24 * 3600) * 10 ** 6) / 10 ** 6

def create_regex(raw_text):
    if '*' in raw_text:
        parts = raw_text.split('*')
        parts = map(lambda x : re.escape(x), parts)
        reg = '.*' + '.*'.join(parts) + '.*'

        return reg
    else:
        return '^%s$' % re.escape(raw_text)

class UnifieldException(Exception):
    pass

class TimeoutException(UnifieldException):
    pass

class UniFieldElementException(UnifieldException):
    pass


# Get an element {%{

def monitor(browser, explanation=''):
    start_datetime = datetime.datetime.now()
    here = {'val': 0, 'start_datetime': start_datetime, 'browser': browser}
    LIMIT_COUNTER = 30
    found_message = set([])

    def counter(message_if_error=None):
        here['val'] += 1

        now = datetime.datetime.now()
        time_spent_waiting = timedelta_total_seconds(now - here['start_datetime'])

        TIME_BEFORE_FAILURE = get_TIME_BEFORE_FAILURE()

        timeout_detected = TIME_BEFORE_FAILURE is not None and time_spent_waiting > TIME_BEFORE_FAILURE

        if here['val'] > LIMIT_COUNTER or timeout_detected:
            browser = here['browser']

            if isinstance(browser, WebElement):
                while not isinstance(browser, WebDriver):
                    browser = browser.parent

            browser.save_screenshot("waiting_too_long.png")

            for entry in browser.get_log('browser'):
                key = (entry['timestamp'], entry['message'])
                if key not in found_message:
                    # we have to add the entry in the file
                    f = open("waiting_too_long.txt", 'a')
                    strdate = datetime.datetime.strftime(datetime.datetime.now(), '%Y/%m/%d %H:%M:%S')
                    f.write(strdate + ": " + str(entry) + '\r\n')
                    f.close()
                found_message.add(key)

            content = browser.page_source
            f = open("waiting_too_long.html", 'w')
            f.write(content.encode('utf-8'))
            f.close()

        if timeout_detected:
            raise TimeoutException(message_if_error or explanation or "We have waited for too long on an element")

    return counter

def get_input(browser, fieldname):
    # Most of the fields use IDs, however, some of them are included in a table with strange fields.
    #  We have to look for both
    my_input = None
    idattr = None

    tick = monitor(browser, "Cannot find field %s" % fieldname)

    while not my_input:

        #FIXME: I don't understand how that works... we shouldn't wait since the field description
        #  could be something else than a label (see below)
        labels = get_elements_from_text(browser, tag_name="label", text=fieldname)

        # we have a label!
        if labels:
            label = labels[0]
            idattr = label.get_attribute("for")
            my_input = get_element(browser, id_attr=idattr.replace('/', '\\/'), wait=True)
            break

        # do we have a strange table?
        table_header = get_elements_from_text(browser, class_attr='separator horizontal', tag_name="div", text=fieldname)

        if not table_header:
            tick()
            time.sleep(TIME_TO_SLEEP)
            continue

        # => td
        table_header = table_header[0]

        table_node = table_header.find_elements_by_xpath("ancestor::tr[1]")
        if not table_node:
            tick()
            time.sleep(TIME_TO_SLEEP)
            continue

        element = table_node[0].find_elements_by_xpath("following-sibling::*[1]")
        if not element:
            tick()
            time.sleep(TIME_TO_SLEEP)
            continue

        for tagname in ["select", "input", "textarea"]:
            inputnode = element[0].find_elements_by_tag_name(tagname)
            if inputnode:
                my_input = inputnode[0]
                break

        inputnodes = get_elements(element[0], tag_name="p", class_attr="raw-text")
        if inputnodes:
            tick()
            my_input = inputnodes[0]
            break

        if not my_input:
            tick()
            break

        tick()
        time.sleep(TIME_TO_SLEEP)

    return idattr, my_input

def get_elements(browser, tag_name=None, id_attr=None, class_attr=None, attrs=dict(), wait='', atleast=0):
    '''
    This method fetch a node among the DOM based on its attributes.

    You can indicate wether this method is expected to wait for this element to appear.

    Be careful: this method also returns hidden elements!
    '''

    css_selector = ""

    css_selector += tag_name if tag_name is not None else "*"
    css_selector += ("." + class_attr) if class_attr is not None else ""
    css_selector += ("#" + id_attr) if id_attr is not None else ""

    if attrs:
        css_selector += "["
        item_number = 0

        for attr_name, value_attr in attrs.items():
            css_selector += "%(attr)s='%(value)s'" % dict(attr=attr_name, value=value_attr)

            item_number += 1
            if item_number != len(attrs):
                css_selector += ","

        css_selector += "]"

    if not wait:
        elements = browser.find_elements_by_css_selector(css_selector)
    else:
        tick = monitor(browser, wait)

        while True:

            try:
                elements = browser.find_elements_by_css_selector(css_selector)
                if len(elements) > atleast:
                    break

                time.sleep(TIME_TO_SLEEP)
            except:
                time.sleep(TIME_TO_SLEEP)

            tick()

    return elements

def get_element(browser, tag_name=None, id_attr=None, class_attr=None, attrs=dict(), wait='', position=None):
    elements = get_elements(browser, tag_name, id_attr, class_attr, attrs, wait, atleast=position or 0)

    if position is None:
        only_visible = filter(lambda x : x.is_displayed(), elements)

        return only_visible[0] if only_visible else elements[0]
    else:
        return elements[position]

def to_camel_case(text):
    words = text.split()
    words = map(lambda x : x[:1].upper() + x[1:].lower(), words)
    return ' '.join(words)

def get_elements_from_text(element, tag_name, text, class_attr='', wait=''):
    '''
    This method fetch a node among the DOM based on its text.

    To find it, you must provide the name of the tag and its text.

    You can indicate wether this method is expected to wait for this element to appear.
    '''
    class_attr = (" and @class = '%s'" % class_attr) if class_attr else ''

    if not isinstance(tag_name, list):
        tag_name = [tag_name]
    possibilities = []

    #FIXME: It won't work in French...
    from_translate = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
    to_translate = 'abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyz'

    for my_tag in tag_name:
        data = dict(class_attr=class_attr,
                    tagname=my_tag,
                    text=text.lower(),
                    from_translate=from_translate,
                    to_translate=to_translate)

        # we need to look for nodes "in the given node" when we select an option
        #  in a select and we don't want to select the other option

        xpath1_query = ".//%(tagname)s[translate(normalize-space(.), '%(from_translate)s', '%(to_translate)s') ='%(text)s'%(class_attr)s]" % data
        xpath2_query = ".//%(tagname)s//*[translate(normalize-space(.), '%(from_translate)s', '%(to_translate)s') ='%(text)s'%(class_attr)s]" % data
        possibilities.append(xpath1_query)
        possibilities.append(xpath2_query)

    xpath_query = '|'.join(possibilities)

    if not wait:
        ret = element.find_elements_by_xpath(xpath_query)
        return filter(lambda x : x.is_displayed(), ret)
    else:
        tick = monitor(element, wait)

        while True:

            elems = element.find_elements_by_xpath(xpath_query)
            only_visible = filter(lambda x : x.is_displayed(), elems)

            if only_visible:
                return only_visible

            time.sleep(TIME_TO_SLEEP)
            tick()

def get_element_from_text(browser, tag_name, text, class_attr='', wait=False):
    '''
    This method fetch a node among the DOM based on its text.

    To find it, you must provide the name of the tag and its text.

    You can indicate wether this method is expected to wait for this element to appear.
    '''
    #FIXME: We cannot crash if an element is not found (especially an IndexError...)
    return get_elements_from_text(browser, tag_name, text, class_attr, wait)[0]

def get_column_position_in_table(maintable, columnname):
    message = "Cannot find column %s in table" % columnname

    elems = get_elements_from_text(maintable, tag_name="th", text=columnname, wait=message)
    if not elems:
        return None
    elem = elems[0]

    #FIXME: This is the maintable! It doesn't work that way.
    # The parent element is the element that generated this node but
    # it isn't the parent element in the DOM
    parent = elem.parent
    right_pos = None

    idtable = maintable.get_attribute("id")
    #FIXME: a table should always have an id, but... but who knows...
    assert idtable is not None

    data = dict(id=idtable)
    elements = maintable.find_elements_by_css_selector('#%(id)s thead th' % data)

    for pos, children in enumerate(elements):
        if children.get_attribute("id") == elem.get_attribute("id"):
            right_pos = pos
            break

    return right_pos

def open_all_the_tables(world):
    #TODO: The pager is outside the table we look for above. As a result, we look
    #  for the external table, but that's not very efficient since we have to load
    #  them again afterwards...

    def _open_all_the_tables():
        pagers = get_elements(world.browser, class_attr="gridview", tag_name="table")
        pagers = filter(lambda x : x.is_displayed(), pagers)
        for pager in pagers:
            elem = get_element(pager, class_attr="pager_info", tag_name="span")

            import re
            m = re.match('^\d+ - (?P<from>\d+) of (?P<to>\d+)$', elem.text.strip())
            do_it = False

            if m is None:
                do_it = True
            else:
                gp = m.groupdict()
                do_it = gp['from'] != gp['to']

            if do_it:
                elem.click()

                # we cannot select an unlimited number of items. So we stick to 500
                #  even if we know that the row we are looking for is in the next page... (comes from US-1207)
                element = get_element(pager, tag_name="select", attrs=dict(action="filter"))
                select = Select(element)
                select.select_by_visible_text("500")

                wait_until_not_loading(world.browser, wait="I cannot load the whole table")

    repeat_until_no_exception(world, _open_all_the_tables, StaleElementReferenceException)

def get_options_for_table(world, columns):
    '''
    Return all the rows that have been found in one of the table
     with, at least, the given column in the table.
    '''

    open_all_the_tables(world)

    maintables = get_elements(world.browser, tag_name="table", class_attr="grid")
    maintables = filter(lambda x : x.is_displayed(), maintables)

    rows = []

    for maintable in maintables:

        #FIXME: We now that when a column is not found in one array, we look in the
        #        next one. This is not good since we could detect a column in another
        #        table...
        position_per_column = {}
        for column in columns:
            # We cannot normalize columns here because some columns don't follow
            #  the common convention
            pos_in_table = get_column_position_in_table(maintable, column)
            position_per_column[column] = pos_in_table

        if None in position_per_column.values():
            continue

        lines = get_elements(maintable, tag_name="tr", class_attr="grid-row")

        # we look for the first line with the right value
        for row_node in lines:
            values = []

            # we have to check all the columns
            for column in columns:
                position = position_per_column[column]
                td_node = get_element(row_node, class_attr="grid-cell", tag_name="td", position=position)

                values.append(td_node.text.strip())

            # we want to skip the empty lines
            if any(map(lambda x : bool(x), values)):
                yield maintable, row_node, values

def get_table_row_from_hashes(world, keydict):
    '''
    Returns all the rows that contains the columns given in the
     dictionary's key (keydict) with the right values.
    '''
    #TODO: Check that we don't find twice the same row...
    #TODO: Check that all the lines are in the same table...
    columns = list(keydict.keys())

    for maintable, row_node, values in get_options_for_table(world, columns):
        everything_matches = True

        for column_name, value in zip(columns, values):
            valreg = convert_input(world, keydict[column_name])
            reg = create_regex(valreg)

            if re.match(reg, value, flags=re.DOTALL) is None:
                everything_matches = False

        if everything_matches:
            yield maintable, row_node

#}%}

# Wait {%{
def wait_until_no_ajax(world, message="A javascript operation is still ongoing"):
    tick = monitor(world.browser, message)
    while True:
        # sometimes, openobject doesn't exist in some windows
        try:

            # we have to check if the frame is still visible because we sometimes reload another one
            #  If we run a javascript code in the old frame it blocks.
            try:
                world.browser.find_element_by_tag_name("html")
                world.browser.find_element_by_tag_name("html").is_displayed()
            except (NoSuchElementException, NoSuchFrameException) as e:
                # we have to reload the new frame
                world.browser.switch_to_default_content()
                if world.nbframes != 0:
                    world.browser.switch_to_frame(get_element(world.browser, position=world.nbframes-1, tag_name="iframe", wait="Cannot find the frame in which the button is located"))

            ret = world.browser.execute_script('''

                function check(tab){
                    for(i in tab){
                        if(tab[i]){
                            return false;
                        }
                    }
                    return true;
                }

                if(!check(window.TOT)){
                    return "BLOCKED IN WINDOW";
                }
                if(!check(window.TOT2)){
                    return "BLOCKED 2 IN WINDOW";
                }

                elements = window.document.getElementsByTagName('iframe');

                totcount = (typeof window.openobject == 'undefined') ? 0 : window.openobject.http.AJAX_COUNT;
                totcount += (typeof window.TIMEOUT_COUNT == 'undefined') ? 0 : window.TIMEOUT_COUNT;
                totcount += (typeof $ == 'undefined') ? 0 : $.active;

                for(var i = 0; i < elements.length; i++){
                    if(!check(elements[i].contentWindow.TOT)){
                        return "BLOCKED IN INFRAME " + i;
                    }
                    if(!check(elements[i].contentWindow.TOT2)){
                        return "BLOCKED IN INFRAME WINDOW " + i;
                    }

                    var local_ajaxcount1 = (typeof elements[i].contentWindow.openobject == 'undefined' || typeof elements[i].contentWindow.openobject.http == 'undefined') ? 0 : elements[i].contentWindow.openobject.http.AJAX_COUNT;
                    if(local_ajaxcount1 > 0){
                        return "BLOCKED IN AJAXCOUNT WINDOW";
                    }

                    var local_ajaxcount2 = (typeof elements[i].contentWindow.$ == 'undefined') ? 0 : elements[i].contentWindow.$.active;

                    if(local_ajaxcount2 > 0){
                        return "VOILAAA";
                    }


                    totcount += (typeof elements[i].contentWindow.TIMEOUT_COUNT == 'undefined') ? 0 : elements[i].contentWindow.TIMEOUT_COUNT;

                    totcount += local_ajaxcount1;
                    totcount += local_ajaxcount2;
                }

                return totcount;
            ''')
        except WebDriverException as e:
            raise

        tick()
        time.sleep(TIME_TO_SLEEP)

        if str(ret) != "0":
            continue

        return

def repeat_until_no_exception(world, action, exceptions, *params):
    # We use a monitor only after the first exception because we don't know
    tick = monitor(world.browser, "We have waited for too long")

    while True:
        try:
            return action(*params)
        except exceptions as e:
            tick(str(e))
            time.sleep(TIME_TO_SLEEP)

def wait_until_element_does_not_exist(browser, get_elem, message=''):
    '''
    This method tries to click on the elem(ent) until the click doesn't raise en exception.
    '''

    tick = monitor(browser, message)

    while True:
        tick()
        try:
            #browser.save_screenshot("wait_until_element_does_not_exist.png")
            if not get_elem() or not get_elem().is_displayed():
                return
        except Exception as e:
            return
        time.sleep(TIME_TO_SLEEP)

def wait_until_not_displayed(browser, get_elem, message, accept_failure=False):
    '''
    This method tries to click on the elem(ent) until the click doesn't raise en exception.
    '''

    tick = monitor(browser, message or "An element doesn't disappear")
    while True:
        tick()
        try:
            elem = get_elem()
            if not elem.is_displayed():
                return
        except Exception as e:
            if accept_failure:
                return
            else:
                print(e)
                raise
        time.sleep(TIME_TO_SLEEP)

def wait_until_not_loading(browser, wait="Loading takes too much time"):
    try:
        wait_until_not_displayed(browser, lambda : get_element(browser, tag_name="div", id_attr="ajax_loading", wait=wait), message=wait, accept_failure=not wait)
    except:
        return
#}%}

def convert_input(world, content, localdict=dict()):
    new_content = content
    regex = '({{((?:\w+\()*)(\w+)((?:\)*))}})'

    for full, functions, word, after in re.findall(regex, content):

        # does the word exist?
        if word not in localdict and word not in world.FEATURE_VARIABLE:
            #FIXME if it doesn't exist we cannot crash because the tables
            #  are expanded even if we don't manage to expand ROW. As a result
            #  a crash could stop all the tests because of the output component...
            continue

        if after.count(')') != functions.count('('):
            raise UnifieldException("You don't close/open all the parentheses in")

        real_value = localdict.get(word, world.FEATURE_VARIABLE.get(word))

        functions = functions.split('(')
        functions.reverse()

        for function in functions:
            if function:
                if function not in world.FUNCTIONS:
                    raise UnifieldException("Unknown function: %s" % function)
                real_value = world.FUNCTIONS[function](real_value)

        #FIXME could we replace something that is not valid? yes...
        #FIXME worse than that... we could find a match in something that has already
        #       been replaced...
        new_content = new_content.replace(full, real_value, 1)

    regex = '({%(\w+)%})'
    for name, varname in re.findall(regex, new_content):
        if varname in os.environ:
            new_content = new_content.replace(name, os.environ[varname], 1)

    return new_content

# Do something {%{
def click_on(browser, elem_fetcher, msg):
    '''
    This method tries to click on the elem(ent) until the click doesn't raise en exception.
    '''
    tick = monitor(browser, msg or "An element cannot be clicked")
    while True:
        try:
            elem = elem_fetcher()
            if elem and elem.is_displayed():
                elem.click()
            return
        except Exception as e:
            print(e)
        tick()
        time.sleep(TIME_TO_SLEEP)

def action_write_in_element(txtinput, content):

    #TODO: Merge that with fill_field
    if txtinput.tag_name == "input" and txtinput.get_attribute("type") and txtinput.get_attribute("type") == "checkbox":
        if content.lower() not in ["yes", "no"]:
            raise UniFieldElementException("You cannot defined any value except no and yes for a checkbox")

        if content.lower() == "yes":
            if not txtinput.is_selected():
                txtinput.click()
        else:
            if txtinput.is_selected():
                txtinput.click()
    else:
        txtinput.clear()
        txtinput.send_keys((100*Keys.BACKSPACE) + content + Keys.TAB)

def action_select_option(txtinput, content):
    txtinput.click()
    option = get_element_from_text(txtinput, tag_name="option", text=content, wait='Cannot find option %s' % content)
    option.click()
    txtinput.click()

def select_in_field_an_option(world, fieldelement, content):
    '''
    Find a field according to its label
    '''

    field, action = fieldelement()
    idattr = field.get_attribute("id")

    value_before = None
    ## we look for the value before (to check after)
    end_value = "_text"
    if idattr[-len(end_value):] == end_value:
        idvalue_before = idattr[:-len(end_value)]
        txtidinput = get_element(world.browser, id_attr=idvalue_before.replace('/', '\\/'), wait=True)
        value_before = txtidinput.get_attribute("value")

    txtinput, _ = fieldelement()

    action(txtinput, content)

    # We have to wait until the information is completed
    wait_until_no_ajax(world)

#}%}

