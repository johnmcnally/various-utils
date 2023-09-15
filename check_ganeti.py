#!/usr/bin/python3
# Name: check_ganeti.py
# Description: Nagios plugin to check Ganeti service status
# Requires: Python 3.6 or later
# Author: John McNally, jmcnally@acm.org
# Version: 1.0
# Release date: 9/15/2023

import platform, re, sys, traceback
from subprocess import getoutput

# Nagios Status Codes
OK=0
WARNING=1
CRITICAL=2
UNKNOWN=3

# Other variables
active_count=0
status_code=OK
output_text=""
os_major_version=""
ganeti_major_version=""
role_text=""

def do_systemd():
    global active_count
    global output_text
    global status_code
    status_text=""

    if role_text == 'master':
        services = ['ganeti-luxid',
                    'ganeti-noded',
                    'ganeti-rapi',
                    'ganeti-wconfd'
                   ]
    else: # not ganeti master
        services = ['ganeti-noded']

    if ganeti_major_version == 2:
        services.insert(0, 'ganeti-confd')

    for service in services:
        status_text = getoutput(f"systemctl show {service} -p SubState").split("=")[1].lower()
#        print(f"{service}: {status_text}")
        if status_text == 'running':
            active_count += 1
        else:
            status_code = CRITICAL
            output_text = f"{output_text} {service} {status_text};"

def do_initd():
    global active_count
    global output_text
    global status_code
    status_text=""

    if role_text == 'master':
        services = ['ganeti-masterd',
                    'ganeti-noded',
                    'ganeti-rapi'
                   ]
    else: # not ganeti master
        services = ['ganeti-noded']

    status_text = getoutput('service ganeti status')

    for service in services:
        if re.findall(f"{service}.+is running", status_text):
            active_count += 1
        else:
            status_code = CRITICAL
            output_text = f"{output_text} {service} {status_text};"

if __name__ == '__main__':
    file = open(r"/etc/redhat-release", "r")
    os_major_version = int(re.findall('[0-9]', file.readline())[0])

    file = open(r"/var/lib/ganeti/ssconf_release_version", "r")
    ganeti_major_version = int(re.findall('[0-9]', file.readline())[0])

    file = open(r"/var/lib/ganeti/ssconf_master_node", "r")
    if platform.node() == file.readline().strip():
        role_text = 'master'
    else:
        role_text = 'non-master'

    if os_major_version >= 7:
        do_systemd()
    elif os_major_version <= 6:
        do_initd()
    else:
        print("GANETI UNKNOWN - OS version unsupported")
        status_code = UNKNOWN

    if status_code == OK:
        print(f"GANETI OK - {active_count} service(s) active on {role_text} node")
    elif status_code == CRITICAL:
        print(f"GANETI CRITICAL -{output_text}")

    sys.exit(status_code)
