# testfield [![Build Status](https://travis-ci.org/Unifield/testfield.svg?branch=master)](https://travis-ci.org/Unifield/testfield)
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

The language we use is straightforward since the user interface has always the same structure.  Clicking on a button is always done the same way.  As a result, we only need to name the button and use the right syntax (a/k/a **a step**) to perform the click:
> I click on "ABC"

There are only a few steps to instrument the whole application. They are described [here](https://github.com/Unifield/testfield/wiki/Steps).

### Use variables
You can use the variable {{ID}} in all your tests. This value is an integer that is new at each run. It can be used to create unique identifiers (for example: a stock name, a register name, and so on). Our goal is that every test should be designed to be run as many times as we want on the same database. It shouldn’t interact with results coming from other tests. 

You can also declare variables when executing a scenario. It's especially useful when an output changes at every run. As a writer, you are the only one aware of this complexity. It will be abstracted away from the readers who will see only the "real" value during the run (see the web interface description below)

Finally, you can also use functions to alter variables while executing a scenario. Two modifies have been created:
* **INCR**: increment the last integer contained in the value. If the value of a variable called _ENTYNUMBER_ is _COR209_.  _{{ENTRYNUMBER}}_ is _COR209_ _{{**INCR**(ENTRYNUMBER)}}_ is _COR300_.
* **NOW**: use the current date. The only parameter is a date format that will be used to express the current date.

### Use steps

All the steps are described [here](https://github.com/Unifield/testfield/wiki/Steps). The are grouped by:
+ First steps: how to log into/out of a database (with or without password)
+ Synchronization: synchronize an instance
+ Go to the right interface: browse the interface (menu, tabs and so on)
+ Fill fields (outside a tabular format): edit fields (except in a table)
+ Click: click on UI elements
+ Checks: check that a content appears or doesn't appear on the current interface
+ File management: store files downloaded in the interface
+ Tables: manage tables
+ Save values: save values available in the interface
+ Translation: steps to change and check translations in the interface for a given field
+ Debug: debug a scenario
+ Benchmarking: steps to benchmark unifield (how long does a set of steps last?)

## How do I install it to debug tests?

In this configuration, you want to interactively see Firefox working
against a stable, remote Unifield isntance. You will be able to run and
debug one test at a time.

Do these things to setup your environment:

```
cd $HOME
git clone https://github.com/Unifield/testfield.git
virtualenv -p python2.6 venv
. venv/bin/activate
pip install -r testfield/requirements.txt
cd testfield
./generate_credentials.sh sandbox ANDRES   <-- Choose one from: ANDRES, MARJUKKA, TEMPO, SARAH (agree with your colleagues first...)
fetch/owncloud/fetch.sh
```

Open the one test you want to work on in your editor, and add a tag
to it like "@fix_me".

At this point, if you run ```./runtests_local.sh -t fix_me``` all
the tests in meta_features will be converted into features, and then
the one feature you marked with @fix_me will run in a Firefox that pops
up on your screen. You can edit steps.py to change it's behavior, for
example adding this to debug it:

```
import pdb
pdb.set_trace()
```

It is easiest to work on one file at a time. On each run of runtests_local.sh,
the features directory will be re-created according to what is in the
meta_features directory.

## How do I install it? (for the geeks)

testfield can be installed on your computer. The installation procedure is available below.

Alternatively, you might use a docker image available on [dockerhub](https://hub.docker.com/r/unifield/testfield/).

### The easy way (Docker)

Go to the docker directory and initialize testfield:
> sudo ./init-test.sh

This script is going to create an **output** directory to store the results and a script called **run.sh**. This script is your single entrypoint for testfield.

By default, the environment used for the tests and the benchmarks is always the same. It's the standard one built by our testers. You might decide to use the lightweight one to test the tool (that's what happens in Travis CI). This environment contains only a few tests that contain most of the steps included in testfield. To achieve that, you'll run that command prior to any test:
```
export TESTFIELD_TEST_KEY=GqurD9dOcYqlFrl
```

You can run testfield in several ways:

1. run the tests written by the business analysts
   > ./run.sh test TEST_NAME [server_branch] [web_branch] [params]

   where:
   + _test_ is the verb (mandatory)
   + _TEST\_NAME_ is the name that is going to be used to export the results. It must be unique.
   + _server\_branch_ is the server branch under test. You can select a revision in the branch with _"server\_branch\|XXX"_ where **XXX** is the revision number (an integer). Don't forget the double quotes otherwise your bash will interpret it as a pipe. lp:unifield-server is used if no branch is specified.
   + _web\_branch_ is the web branch under test. You can select a revision in the branch with _"web\_branch\|XXX"_ where **XXX** is the revision number (an integer). Don't forget the double quotes otherwise your bash will interpret it as a pipe. lp:unifield-web is used if no branch is specified.
   + _params_ are the parameters that will be passed to lettuce. You can select a tag with **-t my_tag** to run the tests with the specified tag. All the tests are run if you don't specify any tag.

2. run the tests and let the environment as it is (database and application) afterwards to ease troubleshooting
   > ./run.sh setup TEST_NAME [server_branch] [web_branch] [params]

   The parameters are the same as the ones for "test".

3. run the benchmarks
   > ./run.sh benchmark BENCHMARK_NAME [server_branch] [web_branch] [params]

   where:
   + _benchmark_ is the verb (mandatory)
   + _BENCHMARK\_NAME_ is the name that is going to be used to export the results. It must be unique.
   + _server\_branch_ (same as above)
   + _web\_branch_ (same as above)
   + _params_ are the parameters that will be passed to lettuce (same as above). We warmly encourage you to use the tag called testperf (-t testperf) to run only scenarios that assess the application performance. This is less important when you use another environment tailored for benchmarking (using the TESTFIELD_TEST_KEY environment variable) because only benchmarking scenarios are included.

4. display the results on a website
   > ./run.sh web

   Run a website on port 8080 to display performance and test results that have been run.

### The challenging way (install everything on your computer)

You might decide to run testfield directly on your computer to debug a specific version of Unifield. It's especially useful for troubleshooting.

To achieve that, you need an up and running version of Unifield with the dumps matching the tests you want to run. You can either:
+ set up your own environment (either in a docker container as in [docker-unifield](https://github.com/Unifield/docker-unifield) or directly on your computer). If you do that, you'll have to restore the test databases.
+ use Unifield after running the tests in a Docker container. Don't forget to let the environment as it is after the tests with "setup".

Prior to testfield's installation, you need to ensure that you have already set up [faketime](https://github.com/wolfcw/libfaketime) (>= 0.9.6) on your computer (```git clone https://github.com/wolfcw/libfaketime.git && cd libfaketime``` ```make```, ```sudo make install``` and so on). It must be in your path. To check that, please run:
```
faketime "2010-01-01" date
```
You should see: ```Fri Jan  1 00:00:00 CET 2010```.

+ Clone the repository
```
git clone https://github.com/Unifield/testfield.git
```
+ Create a virtualenv (*outside the testfield repository you've just cloned*), activate it and install the Python packages
```
# if you haven't installed virtualenv yet
sudo pip install virtualenv
virtualenv myenv
source myenv/bin/activate
cd testfield
# we have to install numpy separately
pip install numpy==1.5
pip install -r requirements.txt
# if you want to install Unifield on your system:
pip install -r requirements_unifield.txt
```
+ Set the configuration variable in `config.sh` in order to connect testfield to Unifield (only the local configuration section if you want to launch the tests against an existing version of Unifield, otherwise you'll have to update the DB configuration variables: ```SERVER_TMPDIR=/tmp```, ```DBPATH=/usr/lib/postgresql/8.4/bin/```, ```FORCED_DATE=yes```)
+ Update the credentials
```
./generate_credentials.sh
```
+ Download the functional tests (optional, otherwise you'll have to create the following directories: files meta_features instances)
```
./fetch/owncloud/fetch.sh
```
+ Install Firefox (if necessary). By default, your Firefox instance will be used. testfield doesn't work with the last version of Firefox (47.0 now). You need Firefox <= 46.0 or Firefox >= 48.0 with [Mozilla Marionette](https://developer.mozilla.org/en-US/docs/Mozilla/QA/Marionette). If you execute testfield on a server, you'll have to install Xvfb ```sudo apt-get install Xvfb```.
+ Launch testfield.
```
# if you want to launch testfield against an existing version of Unifield
./runtests_local.sh
# if you want to launch testfield against a new version of Unifield
./runtests_server.sh test MY_FIRST_TESTS
```
+ When the test or benchmark is done, you can see the result on the webserver included in [testfield on port 8080](http://localhost:8080).
```
cd website
python performance.py
```

### Windows 10 install 
* First of all, you have to download or clone the repository.
```
git clone https://github.com/Unifield/testfield.git
```
* Download and install Python 2.7 (possible the newest release, but there shouldn't be newer than this):
    
    https://www.python.org/downloads/release/python-2718/

* Install Microsoft Visual C++ Compiler for Python 2.7:
    
    https://msfintl.sharepoint.com/sites/grp-msf-unifield-st/Shared%20Documents/IT/Testfield/C++%209.0%20compiler/VCForPython27.msi

* If you installed compiler and still occurring troubles, you can try one of these options:
    * Install compiler for all user, you will probably need to run this in cmd.exe (Win + R => cmd.exe)
        * ``` msiexec /i "C:\Path\to\installer\VCForPython27.msi" ALLUSERS=1```
    * Move vcvarsall.bat into this location:
        * ```o	C:\Program Files (x86)\Common Files\Microsoft\Visual C++ for Python\9.0```

* Install these Python packages:
    ```pip install ```
 ```
        bottle==0.12.9
        lettuce==0.2.21
        numpy==1.11.0
        matplotlib==1.5.1
        selenium==2.53.1
        python-Levenshtein==0.10.2
        Babel==2.1.1
        FormEncode==1.2.2
        CherryPy==3.1.2
        Mako==0.2.5
        OERPLib==0.8.4
        openerp-client-lib==1.0.3
        ordereddict==1.1
        reportlab==2.4
        simplejson==2.0.9
        bzr==2.7.0
        PyYAML==3.11
        passlib==1.6.5
        python-dateutil==2.5.3
        pylzma==0.4.8
        xlwt==1.1.2
        bcrypt==3.1.1
        cffi==1.8.3
        six==1.10.0
```

* Install Firefox version to another folder than you would do usually
```https://ftp.mozilla.org/pub/firefox/releases/46.0/win32/en-US/```
* Disable auto update function of Firefox in the settings - Firefox will try to update to version 47 when
it's launched for the first time. It's possible that you will need to disable auto update and then reinstall.
Firefox will remember previous settings. 
* Change PATH to your Firefox (will not be necessary soon) in the following file:

    ```C:\Python27\Lib\site-packages\selenium\webdriver\firefox\firefox_binary.py```
    * Insert following line into the `__init__` function, change value to be your PATH to Firefox 46 binary
    
    `firefox_path = "C:\\Program Files (x86)\\Mozilla Firefox\\firefox.exe"`
    
* Ask colleagues for credential.py and edit following:
    
    `DB_PREFIX: Change to your DB prefix (KATERINA, SARAH etc.)`

* In the file steps.py comment `XMLRPCConnection(database_name)` line in the function `log_into()`
    * This is  temporary fix for a bug. As soon as the bug is fixed, this won't be necessary.
    
* Some of the possible problems:
    * The code was developed under Linux environment, so it has Unix ends of lines. This won't work with 
    Windows. Some of the packages cannot deal with it. If you're using Git Bash (or just setup your git config) you should choose option to 
    convert lines' ends or using this option:
        
        `git config --global core.autocrlf true`
