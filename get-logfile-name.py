#!/usr/bin/python
# Prints the full path to the syslog-ng log file for the UniFi wireless access point, specified by name.
# Note: Name, model, MAC address and version are retrieved from file "device_constants.py"

# An example of the a valid log file path:
# /usr/local/groundwork/common/var/log/syslog-ng/("U7PG2,788a208667f5,v3.9.40.9098")/("U7PG2,788a208667f5,v3.9.40.9098").log

import device_constants
import sys

if len(sys.argv) > 1:
    mydevice = sys.argv[1]
    for device in device_constants.DEVICES:
        if mydevice == device['name']:
            print '{0}/("{1},{2},v{3}")/("{1},{2},v{3}").log'.format(device_constants.SYSLOG_ROOT,device['model'],device['mac'],device['version'])
else:
    print >> sys.stderr, 'ERROR: Must enter device name'
    sys.exit(1)
