#!/usr/bin/python
# Name: device-status.py
# Description: Send CrashPlan PROe device status report
# Requires: Code42 CrashPlan PROe 4.2 or later
#           Python 2.6 or later, python-requests, python-dateutil
# Author: John McNally, jmcnally@acm.org
# Version: 1.01
# Release date: 9/6/2016

# Function - Convert date/time string to specified format
def format_date(datestring, formatstring):
    from datetime import date
    import dateutil.parser
    d = dateutil.parser.parse(datestring)
    return d.strftime(formatstring)

# Function - Append computer detail info to report
def appendToReport (str):
    str += \
        "Computer: %s\n" % computer["name"] + \
        "Alert: %s\n" % computer["backupUsage"][0]["alertStates"][0] + \
        "OS/Version: %s/%s\n" % (computer["osName"], computer["osVersion"]) + \
        "Last Backup Date: %s\n" % format_date(computer["backupUsage"][0]["lastBackup"],'%m/%d/%y, %I:%M %p') + \
        "Percent Complete: %d\n\n" % computer["backupUsage"][0]["percentComplete"]
    return (str)

# Function - Send report via email
def sendEmail (body):
    import smtplib
    from email.mime.text import MIMEText
    sender = "CrashPlan PROe <user@crashplan.mydomain.com"
    recipient = "recipient@mydomain.com"
    msg = MIMEText(body)

    msg['Subject'] = "Device Status"
    msg['From'] = sender
    msg['To'] = recipient

    s = smtplib.SMTP('localhost')
    s.sendmail(sender, [recipient], msg.as_string())
    s.quit()
    return

# Function - Prepare and execute the HTTP request
def requestComputers():
    import requests
    from requests.auth import HTTPBasicAuth
    from requests.packages.urllib3.exceptions import InsecureRequestWarning
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    url = 'https://backups.intranet.psfc.coop:4285/api/Computer'
    parameters = {'active': 'true',
                  'incBackupUsage': 'true',
                  'srtKey': 'lastBackup',
                  'srtDir': 'desc'}
    username = 'user@mydomain.com'
    password = 'Changeme'
    r = requests.get(url, params=parameters, verify=False, auth=HTTPBasicAuth(username, password))

    # Return the request as JSON
    return (r.json())

# MAIN()
import sys, traceback

try:
    # Initialize global variables
    totalOK = 0
    totalWarning = 0
    totalCritical = 0
    details = ""
    report = ""

    dictionary = requestComputers()

    # Iterate through each computer in the dictionary
    for computer in dictionary["data"]["computers"]:
        if computer["alertState"] == 2:
            totalCritical += 1
            details = appendToReport(details)
        elif computer["alertState"] == 1:
            totalWarning += 1
            details = appendToReport(details)
        elif computer["alertState"] == 0:
            totalOK += 1

    # Assemble the complete report
    report += \
        "Total OK: %d\n" % totalOK + \
        "Total Warning: %d\n" % totalWarning + \
        "Total Critical: %d\n" % totalCritical
    if details != "":
        report += \
            "\nDETAILS\n" + \
            "----------------------------------------\n" + \
        details

    # Send the report by email
    sendEmail(report)

except:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
    print ''.join('!! ' + line for line in lines)
