
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
import time

TIME_TO_SLEEP = 0

# Get an element {%{
def get_elements(browser, tag_name=None, id_attr=None, class_attr=None, attrs=dict(), wait=False, atleast=0):
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
    while True:
      try:
        elements = browser.find_elements_by_css_selector(css_selector)
        if len(elements) > atleast:
            break

        #print("Wait 4 '%s'" % css_selector)
        browser.save_screenshot("get_elements.png")
        time.sleep(TIME_TO_SLEEP)
      except:
        #print("Wait 4 '%s'" % css_selector)
        browser.save_screenshot("get_elements.png")
        time.sleep(TIME_TO_SLEEP)

  return elements

def get_element(browser, tag_name=None, id_attr=None, class_attr=None, attrs=dict(), wait=False, position=None):
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

def get_elements_from_text(browser, tag_name, text, class_attr='', wait=True):
  '''
  This method fetch a node among the DOM based on its text.

  To find it, you must provide the name of the tag and its text.

  You can indicate wether this method is expected to wait for this element to appear.
  '''
  class_attr = (" and @class = '%s'" % class_attr) if class_attr else ''

  if not isinstance(tag_name, list):
    tag_name = [tag_name]
  possibilities = []

  for my_tag in tag_name:
    data = dict(class_attr=class_attr, tagname=my_tag, text=text)

    # we need to look for nodes "in the given node" when we select an option
    #  in a select and we don't want to select the other option
    xpath1_query = ".//%(tagname)s[normalize-space(.)='%(text)s'%(class_attr)s]" % data
    xpath2_query = ".//%(tagname)s//*[normalize-space(.)='%(text)s'%(class_attr)s]" % data
    possibilities.append(xpath1_query)
    possibilities.append(xpath2_query)

  xpath_query = '|'.join(possibilities)

  if not wait:
    ret = browser.find_elements_by_xpath(xpath_query)
    return filter(lambda x : x.is_displayed(), ret)
  else:
    while True:
      elems = browser.find_elements_by_xpath(xpath_query)
      only_visible = filter(lambda x : x.is_displayed(), elems)

      if only_visible:
        return only_visible

      #print("Wait 4 '%s'" % xpath_query)
      time.sleep(TIME_TO_SLEEP)

      browser.save_screenshot("get_elements_from_text.png")

def get_element_from_text(browser, tag_name, text, class_attr='', wait=True):
  '''
  This method fetch a node among the DOM based on its text.

  To find it, you must provide the name of the tag and its text.

  You can indicate wether this method is expected to wait for this element to appear.
  '''
  #FIXME: We cannot crash if an element is not found (especially an IndexError...)
  return get_elements_from_text(browser, tag_name, text, class_attr, wait)[0]

def get_column_position_in_table(maintable, columnname):
    elems = get_elements_from_text(maintable, tag_name="th", text=columnname, wait=False)
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

def get_table_row_from_hashes(world, keydict):
    columns = keydict.keys()

    #TODO: The pager is outside the table we look for above. As a result, we look
    #  for the external table, but that's not very efficient since we have to load
    #  them again afterwards...

    pagers = get_elements(world.browser, class_attr="gridview", tag_name="table")
    pagers = filter(lambda x : x.is_displayed(), pagers)
    for pager in pagers:
        elem = get_element(pager, class_attr="pager_info", tag_name="span")
        elem.click()

        element = get_element(pager, tag_name="select", attrs=dict(action="filter"))
        select = Select(element)
        select.select_by_visible_text("unlimited")

        wait_until_not_loading(world.browser, wait=False)
    
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

            # we have to check all the columns
            for column, position in position_per_column.iteritems():
                td_node = get_element(row_node, class_attr="grid-cell", tag_name="td", position=position)

                value = keydict[column]
                new_value = convert_input(world, value)

                if td_node.text.strip() != new_value:
                    break
            else:
                rows.append(row_node)

    return rows

#}%}

# Wait {%{
def wait_until_no_ajax(browser):
    while True:
        time.sleep(TIME_TO_SLEEP)
        # sometimes, openobject doesn't exist in some windows
        ret = browser.execute_script('''

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

            elements = window.document.getElementsByTagName('iframe');

            for(var i = 0; i < elements.length; i++){
                if(!check(elements[i].contentWindow.TOT)){
                    return "BLOCKED IN INFRAME " + i;
                }
            }

            return (typeof openobject == 'undefined') ? 0 : openobject.http.AJAX_COUNT;
        ''')

        #return ((typeof openobject == 'undefined') ? 0 : openobject.http.AJAX_COUNT) +
               #(window.TOT == null ? 0 : window.TOT) +
               #(($("iframe").first().size() == 0 || typeof $("iframe")[0].contentWindow.TOT == 'undefined') ? 0 : $("iframe")[0].contentWindow.TOT)

        if str(ret) != "0":
            #print "BOUCLE BLOCK", ret
            continue

        return

def repeat_until_no_exception(action, exception, *params):
    while True:
        try:
            return action(*params)
        except exception:
            raise
            time.sleep(TIME_TO_SLEEP)

def wait_until_element_does_not_exist(browser, get_elem):
  '''
  This method tries to click on the elem(ent) until the click doesn't raise en exception.
  '''

  while True:
    try:
      browser.save_screenshot("wait_until_element_does_not_exist.png")
      if not get_elem() or not get_elem().is_displayed():
        return
    except Exception as e:
      return
    time.sleep(TIME_TO_SLEEP)

def wait_until_not_displayed(browser, get_elem, accept_failure=False):
  '''
  This method tries to click on the elem(ent) until the click doesn't raise en exception.
  '''

  while True:
    try:
      browser.save_screenshot("wait_until_not_displayed.png")
      elem = get_elem()
      if not elem.is_displayed():
        return
    except Exception as e:
      if accept_failure:
        print "FAILURE ACCEPTED", e
        return
      else:
        print(e)
        raise
    time.sleep(TIME_TO_SLEEP)

def wait_until_not_loading(browser, wait=True):
  try:
    wait_until_not_displayed(browser, lambda : get_element(browser, tag_name="div", id_attr="ajax_loading", wait=wait), accept_failure=not wait)
  except:
    #print "GRRRRRR"
    return
#}%}

def convert_input(world, content, localdict=dict()):
    content = content.replace("{{ID}}", str(world.idrun))
    for key, value in localdict.iteritems():
        content = content.replace("{{%s}}" % key, value)
    return content

# Do something {%{
def click_on(elem_fetcher):
  '''
  This method tries to click on the elem(ent) until the click doesn't raise en exception.
  '''

  while True:
    try:
      elem = elem_fetcher()
      if elem and elem.is_displayed():
        elem.click()
      return
    except Exception as e:
      #print(e)
      pass
    time.sleep(TIME_TO_SLEEP)

def action_write_in_element(txtinput, content):
    txtinput.clear()
    txtinput.send_keys((100*Keys.BACKSPACE) + content + Keys.TAB)

def action_select_option(txtinput, content):
    txtinput.click()
    option = get_element_from_text(txtinput, tag_name="option", text=content, wait=True)
    option.click()
    txtinput.click()

def select_in_field_an_option(browser, fieldelement, content):
    '''
    Find a field according to its label
    '''

    field, action, confirm = fieldelement()
    idattr = field.get_attribute("id")

    value_before = None
    ## we look for the value before (to check after)
    end_value = "_text"
    if idattr[-len(end_value):] == end_value:
        idvalue_before = idattr[:-len(end_value)]
        txtidinput = get_element(browser, id_attr=idvalue_before.replace('/', '\\/'), wait=True)
        value_before = txtidinput.get_attribute("value")

    txtinput, _, _ = fieldelement()

    action(txtinput, content)

    if confirm:

        # We have to wait until the value is updated in the field
        if value_before is not None:
            value_after = value_before
            while value_after == value_before:
                #FIXME: What happens if I change a field without changing its value?...
                txtidinput = get_element(browser, id_attr=idvalue_before.replace('/', '\\/'), wait=True)
                value_after = txtidinput.get_attribute("value")

                #click_on(lambda : get_element_from_text(browser, tag_name="span", text=content, wait=True))
        else:
            #FIXME: What happens if the name already exist in the interface?
            #click_on(lambda : get_element_from_text(browser, tag_name="span", text=content, wait=True))
            pass

        # the popup menu should disappear
        #wait_until_element_does_not_exist(browser, get_element_from_text(browser, tag_name="span", text=content))

    # We have to wait until the information is completed
    wait_until_no_ajax(browser)

#}%}

