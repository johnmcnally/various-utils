#!/bin/python
# Name: unifi-version.py
# Description: Display Ubiquiti UniFi Controller installed version and bundled device firmware
# Requires: Python 2.6 or later
# Author: John McNally
# Version: 1.00
# Release date: 12/8/2016

def usage():
    print "usage: unifi-version.py [-h] [-a]\n \
    -a, --all        show all bundled firmware\n \
    -h, --help       show this help message and exit"

# MAIN()
import sys, json

controller_version = open("/opt/UniFi/webapps/ROOT/app-unifi/.version").read()
bundles_path = "/opt/UniFi/dl/firmware/bundles.json"
bundles = json.load(open(bundles_path))
installed_devices = ["UniFi AP-Pro", \
                     "UniFi AP-AC-Pro", \
                     "UniFi AP-AC-Pro Gen2"]

# Installed devices only
if len(sys.argv) == 1:
    print "UniFi Controller {0}".format(controller_version[:controller_version.find("-")])
    for device in installed_devices:
        for bundle in bundles:
            try:
                if bundles[bundle]["display"] == device:
                    print "{0} {1}".format(bundles[bundle]["display"], bundles[bundle]["version"])
            except KeyError:
                continue # if version is missing

# All bundles with a "version" attribute. Skip other bundles
elif len(sys.argv) == 2:
    if sys.argv[1] == "--all" or sys.argv[1] == "-a":
        print "UniFi Controller {0}".format(controller_version[:controller_version.find("-")])
        for bundle in bundles:
            try:
                print "{0} {1}".format(bundles[bundle]["display"], bundles[bundle]["version"])
            except KeyError:
                continue # if version is missing
    elif sys.argv[1] == "--help" or sys.argv[1] == "-h":
        usage()
        sys.exit(0)
    else:
        usage()
        sys.exit(1)

# More than two arguments entered
else:
    usage()
    sys.exit(1)
