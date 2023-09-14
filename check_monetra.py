#!/usr/bin/python3
# Name: check_monetra.py
# Description: Nagios plugin to check Monetra Payment Server health
# Requires: Python 3.6 or later, python-argparse, python-requests
# Author: John McNally, jmcnally@acm.org
# Version: 1.1.0
# Release date: 4/20/2023

def perform_check(args):
    from datetime import timedelta
    import xml.etree.ElementTree as ET

    import requests
    from requests.packages.urllib3.exceptions import InsecureRequestWarning
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    # Nagios Status Codes
    OK = 0
    WARNING = 1
    CRITICAL = 2
    UNKNOWN = 3

    # Variables
    host = args.host
    user = args.user
    password = args.password
    timeout = args.timeout
    warn = args.warn
    critical = args.critical
    code = ''
    msoft_code = ''
    verbiage = ''
    rt_output = ''

    url = "https://{0}:8666".format(host)

    xml_in  = "<?xml version=\"1.0\" ?>\n \
    <MonetraTrans>\n \
    \t<Trans identifier=\"1\">\n \
    \t\t<action>chkpwd</action>\n \
    \t\t<username>MADMIN:{0}</username>\n \
    \t\t<password>{1}</password>\n \
    \t</Trans>\n \
    </MonetraTrans>\n".format(user,password)

    if args.verbose:
        print (xml_in)

    # Post the request
    try:
        r = requests.post(url=url,
                          data=xml_in,
                          verify=False,
                          timeout=timeout,
                          headers={'Content-Type': 'application/xml'})
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        if args.verbose:
            lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
            print (''.join('!! ' + line for line in lines))
        else:
            print ("MONETRA CRITICAL - {0}".format(exc_value))
        sys.exit(CRITICAL)

    # Format the response elapsed time
    if warn != 0 or critical != 0:
        rt_output = "in {0:.3f} seconds response time".format(float(r.elapsed.seconds) + float(r.elapsed.microseconds) / 1000000)
        if args.verbose:
            print ("Request completed {0}".format(rt_output))

    # Parse the response text as XML
    xml_out = r.text
    if args.verbose:
        print (xml_out)

    root = ET.fromstring(xml_out)

    for status in root.findall('DataTransferStatus'):
        code = status.get('code')
    for response in root.findall('Resp'):
        msoft_code = response.find('msoft_code').text
    for response in root.findall('Resp'):
        verbiage = response.find('verbiage').text

    # Return the Nagios status code and summary
    if code == 'SUCCESS':
        if msoft_code == 'INT_SUCCESS':
            if warn == 0 and critical == 0:
                print ("MONETRA OK - {0}".format(verbiage))
                sys.exit(OK)
            elif r.elapsed <= timedelta(seconds=warn):
                print ("MONETRA OK - {0} {1}".format(verbiage, rt_output))
                sys.exit(OK)
            elif r.elapsed <= timedelta(seconds=critical):
                print ("MONETRA WARNING - {0} {1} {2} (> {3} seconds)".format(code, verbiage, rt_output, warn))
                sys.exit(WARNING)
       	    elif r.elapsed > timedelta(seconds=critical):
                print ("MONETRA CRITICAL - {0} {1} {2} (> {3} seconds)".format(code, verbiage, rt_output, critical))
                sys.exit(CRITICAL)
        else:
            print ("MONETRA WARNING - {0} {1} {2}".format(code, msoft_code, verbiage))
            sys.exit(WARNING)
    else:
        print ("MONETRA CRITICAL - {0} {1} {2}".format(code, msoft_code, verbiage))
        sys.exit(CRITICAL)

def define_parser():
    import argparse
    parser = argparse.ArgumentParser(description='Check Monetra Payment Server health', formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('-H', '--host', required=True,
                        help='hostname or IP address of server')
    parser.add_argument('-u', '--user', required=True,
                        help='username for authentication to server\nNOTE: Use a low-privilege admin account for this purpose')
    parser.add_argument('-p', '--password', required=True,
                        help='password for authentication to server')
    parser.add_argument('-t', '--timeout', default=10,
                        help='connection timeout. Default is 10 seconds')
    parser.add_argument('-w', '--warn', default=0, type=float,
                        help='warning threshold for request duration in seconds')
    parser.add_argument('-c', '--critical', default=0, type=float,
                        help='critical threshold for request duration in seconds')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='increase output verbosity')
    parser.set_defaults(func=perform_check)

    return(parser)

# MAIN()
import sys, traceback

parser = define_parser()
args = parser.parse_args()

if args.verbose:
    print (args)

args.func(args)
