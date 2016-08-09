# testfield [![Build Status](https://travis-ci.org/hectord/testfield.svg?branch=master)](https://travis-ci.org/hectord/testfield)
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

There are only a few steps to instrument the whole application. They are described [here](https://github.com/hectord/testfield/wiki/Steps).

### Use variables
You can use the variable {{ID}} in all your tests. This value is an integer that is new at each run. It can be used to create unique identifiers (for example: a stock name, a register name, and so on). Our goal is that every test should be designed to be run as many times as we want on the same database. It shouldn’t interact with results coming from other tests. 

You can also declare variables when executing a scenario. It's especially useful when an output changes at every run. As a writer, you are the only one aware of this complexity. It will be abstracted away from the readers who will see only the "real" value during the run (see the web interface description below)

Finally, you can also use functions to alter variables while executing a scenario. Two modifies have been created:
* **INCR**: increment the last integer contained in the value. If the value of a variable called _ENTYNUMBER_ is _COR209_.  _{{ENTRYNUMBER}}_ is _COR209_ _{{**INCR**(ENTRYNUMBER)}}_ is _COR300_.
* **NOW**: use the current date. the only parameter is a date format that will be used to express the current date.

### Use steps

All the steps are described [here](https://github.com/hectord/testfield/wiki/Steps). The are grouped by:
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

## How do I install it? (for the geeks)

testfield can be installed on your computer. The installation procedure is available below.

Alternatively, you might use a docker image available on [dockerhub](https://hub.docker.com/r/hectord/autotestfield/).

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
+ set up your own environment (either in a docker container as in [docker-unifield](https://github.com/TeMPO-Consulting/docker-unifield) or directly on your computer). If you do that, you'll have to restore the test databases.
+ use Unifield after running the tests in a Docker container. Don't forget to let the environment as it is after the tests with "setup".

Prior to testfield's installation, you need to ensure that you have already set up [faketime](https://github.com/wolfcw/libfaketime) (>= 0.9.6) on your computer. It must be in your path. To check that, please run:
```
faketime "2010-01-01" date
```
You should see: ```Fri Jan  1 00:00:00 CET 2010```.

+ Clone the repository
```
git clone testfield
```
+ Create a virtualenv, activate it and install the Python packages
```
virtualenv myenv
source myenv/bin/activate
cd testfield
pip install -r requirements.txt
```
+ Set the configuration variable in `config.sh` in order to connect testfield to Unifield.
+ Update the credentials
```
./generate_credentials.sh
```
+ Launch testfield. By default, your Firefox instance will be used. testfield doesn't work with the last version of Firefox (47.0 now). You need Firefox <= 46.0 or Firefox >= 48.0 with [Mozilla Marionette](https://developer.mozilla.org/en-US/docs/Mozilla/QA/Marionette).
```
./runtests_local.sh
```

