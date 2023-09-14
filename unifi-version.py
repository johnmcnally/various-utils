#!/usr/bin/python3
# Name: unifi-version
# Description: Display Ubiquiti UniFi Controller installed version and bundled device firmware
# Requires: Python 3.6 or later; UniFi Controller 7 or later
# Author: John McNally
# Version: 1.10
# Release date: 3/15/23

def usage():
    print ("usage: unifi-version [-h] [-a]\n \
    -a, --all        show all bundled firmware\n \
    -h, --help       show this help message and exit")

# MAIN()
import sys, json

controller_version = open("/opt/UniFi/webapps/ROOT/app-unifi/.version").read()
controller_version_short = controller_version[:controller_version.find(".",controller_version.rindex("."))]
bundles_path = "/opt/UniFi/dl/firmware/bundles.json"
bundles = json.load(open(bundles_path))
firmware_path = "/opt/UniFi/data/firmware.json"
firmware = json.load(open(firmware_path))
installed_devices = ["UniFi AP-AC-Pro", \
                     "UniFi Flex HD"]

# Installed devices only
if len(sys.argv) == 1:
    print ("UniFi Controller {0}".format(controller_version_short))
    for device in installed_devices:
        for bundle in bundles:
            try:
                if bundles[bundle]["display"] == device:
                    print ("{0} {1}".format(bundles[bundle]["display"], firmware[controller_version_short]["release"][bundle]["version"]))
            except KeyError:
                continue # if version is missing

# All bundles with a "version" attribute. Skip other bundles
elif len(sys.argv) == 2:
    if sys.argv[1] == "--all" or sys.argv[1] == "-a":
        print ("UniFi Controller {0}".format(controller_version_short))
        for bundle in bundles:
            try:
                print ("{0} {1}".format(bundles[bundle]["display"], firmware[controller_version_short]["release"][bundle]["version"]))
            except KeyError:
                continue # if version is missing
    elif sys.argv[1] == "--help" or sys.argv[1] == "-h":
        usage()
        sys.exit(0)
    else:
        usage()
        sys.exit(1)

# More than one argument entered
else:
    usage()
    sys.exit(1)
