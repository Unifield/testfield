# testfield
The main purpose of testfield is to be able to instrument a fork of OpenERP 6 with a lightweight language that can be used by business analysts to write specifications and integration tests. Our goal is to achieve continuous integration without involving too much work from the developper side.

Here is an example of a test:
```
Feature: Manage inventories

Scenario: Import inventory
  Given I log into instance "HQ1C1"
  And I open tab menu "Warehouse"
  I open accordion menu "Inventory Management"
  I click on menu "Physical Inventories"
  I click on "New"
  I fill "Inventory Reference" with "test{{ID}}"
  I click on "add attachment"
  I fill "File to import" with table:
    | Product Code | Product Description          | Location      | Batch | Expiry Date | Quantity |
    | DVACVHEA1S   | VACCINE HEPATITIS A, 1 adult | Stock         |       |             |          |
    | DVACVHEA1V   | VACCINE HEPATITIS A, vial    | Stock         |       |             |          |
  I click on "Import lines"
  I click on "Confirm Inventory"
  I click on "Validate Inventory"  
```

This tool is based on [Lettuce](https://github.com/gabrielfalcao/lettuce) and [Selenium](https://github.com/SeleniumHQ/selenium).

## How do I use it? (for business analysts)

### Use variables
You can use the variable {{ID}} in all your tests. This value is an integer that is new at each run. It can be used to create unique identifiers (for example: a stock name, a register name, and so on). Our goal is that every test should be designed so that we can run it as many times as we want on the same database. It shouldn’t interact with results coming from other tests. 

You can also declare variables when executing a scenario. It's especially useful when an output changes at every run. As a writer, you are the only one aware of this complexity. It will be abstract away from the readers who will see only the "real" value during the run (see the web interface description below)

Finally, can also use functions to alter variables while executing a scenario. There are two modifiers:
* **INCR**: increment the last integer contained in the value. If the value of a variable called _ENTYNUMBER_ is _COR209_.  _{{ENTRYNUMBER}}_ is _COR209_ _{{**INCR**(ENTRYNUMBER)}}_ is _COR300_.
* **NOW**: use the current date. the only parameter is a date format that will be used to express the current date.

### Use steps

#### First steps

| Step                      | Interface                                  |
| -------------             |:------------------------------------------:|
| I log on the homepage<br><br>**Example**: I go on the homepage | <img src="/media/image1.png" width="500" > |
| I log into _"INSTANCE_NAME"_ as _"USERNAME"_ with password _"PASSWORD"_<br><br>**Example**: I log into "HQ1" as "supply-manager" with password "1234" | <img src="/media/image2.png" width="500" > |
| I log into _"INSTANCE_NAME"_<br><br>**Example**: I log into _"HQ1"_ | <img src="/media/image3.png" width="500" > |

#### Synchronization

| Step                      | Interface                                  |
| -------------             |:------------------------------------------:|
| I synchronize "INSTANCE NAME"<br><br>**Example**: I synchronize _"HQ1"_<br><br>**:information_source:** : You don’t need to be logged in when you synchronize. It will work anyway. | <img src="/media/image4.png" width="500" > |

#### Go to the right interface

| Step                      | Interface                                  |
| -------------             |:------------------------------------------:|
| I open tab menu _"TAB MENU NAME"_<br><br>**Example**: I open tab menu _"PURCHASES"_ | <img src="/media/image5.png" width="500" > |
| I open accordion menu _"ACCORDION NAME"_<br><br>**Example**: I open accordion menu _"Claim"_<br><br><br>**:warning:** : Don’t try to open an accordion that is already open | <img src="/media/image6.png" width="500" > |
| I click on menu _"MENU NAME"_ and open the window. <br>**Example**: I click on menu _"Purchase Order Follow-Up"_ and open the window<br>**:warning:** : You must use this step when a window opens after clicking on the menu (as show here). Otherwise, your next step will be blocked.<br><br>If you need to open submenus, separate the menu’s names by a "\|"<br>**Example**: I click on menu _"Theoretical Kit\|Theoretical Kit Item"_ and open the window | <img src="/media/image8.png" width="500" > <img src="/media/image9.png" width="500" > |
| I click on menu _"MENU NAME"_<br><br>**Example**: I click on menu _"Financial Accounting\|Journals\|Journals"_<br><br>If you need to open submenus, separate the menu’s names by a "\|". | <img src="/media/image10.png" width="500" > |

#### Fill fields (outside a tabular format)

| Step                      | Interface                                  |
| -------------             |:------------------------------------------:|
| I fill _"FIELD NAME"_ with _"VALUE"_<br>**Example**: I fill “Code” with _“MY_CODE”_<br><br>**:warning:** :  If you want to set a value in a select box you have to use the exact name as used in the interface.<br>**:warning:** : If you want to change the value of a checkbox you have to choose between “yes” and “no”. | <img src="/media/image11.png" width="500" > |
| I fill "FIELD NAME" with table: <br><br>**Example**:<br><img src="/media/image34.png" width="250"><br> **:warning:** : The first line has to be filled with letters in the right order (from left to right, from ‘A’ to ...).<br> **:warning:** : The dates have to use this format YYYY-MM-DD (for example: 2016-05-01).<br> **:warning:** : We don’t handle boolean values yet. This feature will come a bit later. | <img src="/media/image12.png" width="500" > |

#### Click

#### Checks

#### Tables

#### Save values

#### Debug

<!--

| Step                      | Interface                                   |
| -------------             |:-------------------------------------------:|
| I click on _"BUTTON"_<br>**Example**: I click on "New" | <img src="/media/image7.png" width="500" > |
| I click on _"BUTTON"_ and open the window<br> **Example**: I click on “New” and open the window<br><br> **:warning:** : You must use this step when a window opens after clicking on the menu (as show here). Otherwise, your next step will be blocked. | - |
| I click on _"BUTTON"_ and close the window<br>**Example**: I click on “Save & Close” and close the window | <img src="/media/image13.png" width="500" > |
| I click on _"BUTTON"_ until not available<br>**Example**: I click on “Update” until not available<br><br>This step is used when you have to wait on a process to complete. It’s the case in most of the import process. | - |
| I click on _"BUTTON"_ until _"CONTENT"_ in _"FIELD"_ | - |
| ... if a window is open<br>The step described before that is run only if a window has been opened. Otherwise we just skip it. | - |
| I click on _"BUTTON"_ and close the window if necessary | - |
| I click _"BUTTON"_ until I see: | <img src="/media/image14.png" width="500" > |
| I click _"BUTTON"_ until I don’t see: | <img src="/media/image15.png" width="500" > |
| -                         | <img src="/media/image16.png" width="500" > |
| -                         | <img src="/media/image17.png" width="500" > |
| -                         | <img src="/media/image18.png" width="500" > |
| -                         | <img src="/media/image19.png" width="500" > |
| -                         | <img src="/media/image20.png" width="500" > |
| -                         | <img src="/media/image21.png" width="500" > |
| -                         | <img src="/media/image22.png" width="500" > |
| -                         | <img src="/media/image23.png" width="500" > |
| -                         | <img src="/media/image24.png" width="500" > |
| -                         | <img src="/media/image25.png" width="500" > |
| -                         | <img src="/media/image26.png" width="500" > |
| -                         | <img src="/media/image27.png" width="500" > |
| -                         | <img src="/media/image28.png" width="500" > |
| -                         | <img src="/media/image29.png" width="500" > |
| -                         | <img src="/media/image30.png" width="500" > |
| -                         | <img src="/media/image31.png" width="500" > |
| -                         | <img src="/media/image32.png" width="500" > |
| -                         | <img src="/media/image33.png" width="500" > |
-->

## How do I install it? (for the geeks)

+ faketime (0.9.6)
+ unbuffer (optional)
+ python
 + lettuce
 + OERPLib
 + Pillow
 + bottle
+ PostgreSQL (9.X or 8.X)

Alternatively, you might use a docker image available on [dockerhub](https://hub.docker.com/r/hectord/autotestfield/).
