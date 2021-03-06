#!/usr/bin/env python
# Execute qx testrunner in Selenium and optionally extract report
# @author: Robert Cosgrove <r.cosgrove@griffith.edu.au>

from selenium import webdriver
import sys, shutil, os, fileinput, re, argparse
from os.path import join, isdir

PATH = os.path.dirname(os.path.abspath(__file__))

OUTPUT_PATH = PATH

# output filename
OUTPUT_NAME = 'qx-testrunner-results'

# xml, json, txt
OUTPUT_FORMAT = ""  

# The maximum seconds to wait for the tests to complete.  
# If the tests hang and don't complete for some reason then you wont find out about it until this expires.
# If the tests are likely to exceed this then it will need to be increased.
MAX_WAIT    = 60 * 5

def main(argv):
    parser = argparse.ArgumentParser(
    description='Execute qx testrunner in Selenium and optionally extract report', 
    epilog='This requires Testrunner to be built with: generate.py test -m TESTRUNNER_VIEW:testrunner.view.Console -m BUILD_PATH:test-console')
    parser.add_argument('runner',
                       help='Can be http(s)://, file:/// or relative to the working dir. Include index.html')
    parser.add_argument('--format', dest='outFormat', default=OUTPUT_FORMAT, choices=['html','json','xml', 'none'],
                       help='xml (basic JUnit), json (direct dump), html (simple readable) none (default)')
    parser.add_argument('--outpath', dest='outPath', default=OUTPUT_PATH, 
                       help='Output path. Default is working dir')
    parser.add_argument('--maxwait', dest='maxWait', default=MAX_WAIT, type=int,
                       help='Maximum time in seconds to wait for tests to complete (default 5 minutes)')

    args = parser.parse_args()

    # treat anything without the following prefix as a path relative to the wd
    r = re.compile(r'^(http://|https://|file://|\w:\\|/)')
    if not r.search(args.runner):
        args.runner = "file:///" + join(os.getcwd(), args.runner)

    print '\nQX Selenium Testrunner'
    print 'Using runner at: ' + args.runner
    sys.stdout.flush()

    try:
        browser = webdriver.Firefox()
        browser.set_window_size(200,50)
        browser.set_window_position(0, 0)
        browser.get(args.runner)
    except Exception, e:
        print e
        browser.close()
        sys.exit(1)

    # run tests
    try:
        js = open(join(PATH, 'qx-selenium.js'))
        browser.execute_script("window.QX_SELENIUM_OUTPUT_FORMAT = String('" + args.outFormat + "');")
        browser.execute_script(js.read())
        browser.implicitly_wait(args.maxWait)
        print browser.find_element_by_id("test_results_min").get_attribute('value')+'\n'

        if args.outFormat and args.outPath and OUTPUT_NAME:
            # get test result output
            resultElm = browser.find_element_by_id("test_results_"+args.outFormat)
            if not resultElm:
                 print "Invalid output format " + args.outFormat
                 sys.exit(1)
            results = resultElm.get_attribute('value')

            # save to file
            outPath = join(args.outPath, OUTPUT_NAME + '.' + args.outFormat)
            out     = open(outPath, 'w')
            out.write(results)
            print 'Written "' + outPath +'"'

        # return failed count
        failedElm = browser.find_element_by_id('test_failed')
        failed    = int(failedElm.get_attribute('value'))
        browser.close()

        if failed > 0:
            print failed + ' tests failed!\n'
            sys.exit(failed)
        else:
            print 'All tests successful!\n'
            sys.exit(0)

    except Exception, e:
        print e
        browser.close()
        sys.exit(1)

if __name__ == "__main__":
   main(sys.argv[1:])