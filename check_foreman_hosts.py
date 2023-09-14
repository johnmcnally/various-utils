#!/usr/bin/python3
# Name: check_foreman_hosts.py
# Description: Nagios plugin to check status of Foreman hosts
# Requires: Python 3.6 or later, python-argparse, python-requests
# Author: John McNally, jmcnally@acm.org
# Version: 1.01
# Release date: 9/13/2023

def perform_check(args):
    from datetime import timedelta
    import json
    import requests
    from requests.auth import HTTPBasicAuth
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
    out_of_sync_threshold = 4
    rt_output = ''
    h_string = ''
    url = f"https://{host}/api/v2/dashboard"

    # Send the request
    try:
        r = requests.get(url=url,
                         auth=HTTPBasicAuth(user, password),
                         verify=False,
                         timeout=timeout,
                         headers={'Content-Type': 'application/json'})
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        if args.verbose:
            lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
            print(''.join('!! ' + line for line in lines))
        else:
            print(f"FOREMAN CRITICAL - {exc_value}")
        sys.exit(CRITICAL)

    # Format the response elapsed time
    if warn != 0 or critical != 0:
        rt_output = "in {0:.3f} seconds response time".format(float(r.elapsed.seconds) + float(r.elapsed.microseconds) / 1000000)
        if args.verbose:
            print(f"Request completed {rt_output}")

    # Parse the response text as JSON
    dashboard = json.loads(r.text)

    if args.verbose:
        print("dashboard: ",dashboard)
        print("total: ",dashboard['total_hosts'])
        print("ok: ",dashboard['ok_hosts'])
        print("oos: ",dashboard['out_of_sync_hosts'])
        print("bad: ",dashboard['bad_hosts'])

    # Return the Nagios status code and summary
    if int(dashboard['bad_hosts']) != 0:
        h_string = get_hostnames(args, status='bad_hosts')
        print(f"FOREMAN CRITICAL - {dashboard['bad_hosts']} host(s) in error state: {h_string}")
        sys.exit(CRITICAL)
    elif int(dashboard['out_of_sync_hosts']) > out_of_sync_threshold:
        h_string = get_hostnames(args, status='out_of_sync_hosts')
        print(f"FOREMAN WARNING - {dashboard['out_of_sync_hosts']} host(s) out-of-sync: {h_string}")
        sys.exit(WARNING)
    else:
        if warn == 0 and critical == 0:
            print(f"FOREMAN OK - {dashboard['ok_hosts']} host(s) OK of {dashboard['total_hosts']} total")
            sys.exit(OK)
        elif r.elapsed <= timedelta(seconds=warn):
            print(f"FOREMAN OK - {dashboard['ok_hosts']} host(s) OK of {dashboard['total_hosts']} total {rt_output}")
            sys.exit(OK)
        elif r.elapsed <= timedelta(seconds=critical):
            print(f"FOREMAN WARNING - {dashboard['ok_hosts']} host(s) OK of {dashboard['total_hosts']} total {rt_output} (> {warn} seconds)")
            sys.exit(WARNING)
        elif r.elapsed > timedelta(seconds=critical):
            print(f"FOREMAN CRITICAL - {dashboard['ok_hosts']} host(s) OK of {dashboard['total_hosts']} total {rt_output} (> {critical} seconds)")
            sys.exit(CRITICAL)

def get_hostnames(args, status=''):
    import json
    import requests
    from requests.auth import HTTPBasicAuth
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
    h_string = ''

    if status == 'bad_hosts':
        url = f"https://{host}/api/v2/hosts?search=last_report+%3E+%2230+minutes+ago%22+and+%28status.failed+%3E+0+or+status.failed_restarts+%3E+0%29+and+status.enabled+%3D+true"
    elif status == 'out_of_sync_hosts':
        url = f"https://{host}/api/v2/hosts?search=last_report+%3C+%2230+minutes+ago%22+and+status.enabled+%3D+true"

    # Send the request
    try:
        r = requests.get(url=url,
                         auth=HTTPBasicAuth(user, password),
                         verify=False,
                         timeout=timeout,
                         headers={'Content-Type': 'application/json'})
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        if args.verbose:
            lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
            print(''.join('!! ' + line for line in lines))
        else:
            print(f"FOREMAN CRITICAL - {exc_value}")
        sys.exit(CRITICAL)

    # Parse the response text as JSON
    hosts = json.loads(r.text)['results']
    if args.verbose:
        print(f"{status} hosts: {hosts}")
    for h in hosts:
        h_string = h_string + h['name'] + ' '

    return h_string

def define_parser():
    import argparse
    parser = argparse.ArgumentParser(description='Check status of Foreman hosts', formatter_class=argparse.RawTextHelpFormatter)

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

if __name__ == '__main__':
    import sys, traceback

    parser = define_parser()
    args = parser.parse_args()

    if args.verbose:
        print (args)

    args.func(args)
