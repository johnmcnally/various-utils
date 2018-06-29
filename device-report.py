# Name: device-report.py
# Description: Generate Crashplan PROe device report
# Requires: Code42 CrashPlan PROe 4.2 or later
#           Python 2.6 or later, python-requests, python-argparse, python-dateutil
# Author: John McNally, jmcnally@acm.org
# Version: 1.0
# Release date: 3/10/2017

# Function - Define the parser for command-line arguments
def define_parser():
    import argparse
    parser = argparse.ArgumentParser(description='Generate Crashplan PROe device report', formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('-f', '--format', default='list', choices=['list', 'csv'],
                        help='format of report: list or csv (comma-separated values)')
    parser.add_argument('-o', '--output', default='mail', choices=['mail', 'print'],
                        help='mail -- send via email\nprint -- send to stdout')
    parser.add_argument('-r', '--recipient', default='sysadmin@psfc.coop',
                        help='recipient for email output. Default is "sysadmin@psfc.coop"')
    parser.add_argument('-t', '--type', default='status', choices=['status', 'version'],
                        help='type of report: status or version')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='increase output verbosity')
    parser.set_defaults(func=generate_report)

    return(parser)

# Function - Convert date/time string to specified format
def format_date(datestring, formatstring):
    from datetime import date
    import dateutil.parser
    d = dateutil.parser.parse(datestring)
    return d.strftime(formatstring)

# Function - Send report via email
def send_email (report, format, recipient):
    import smtplib, re
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.MIMEBase import MIMEBase
    from email import Encoders

    match = re.match('^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$', recipient)
    if match == None:
        print('ERROR: Bad Syntax in ' + recipient)
        raise ValueError('Bad Syntax')

    sender = "CrashPlan PROe <admin@crashplan.intranet.psfc.coop>"

    msg = MIMEMultipart()
    msg['Subject'] = "Device Status"
    msg['From'] = sender
    msg['To'] = recipient

    if format == 'list':
        msg.attach (MIMEText(report))
    elif format == 'csv':
        part = MIMEBase ('application', 'text')
        part.set_payload (report)
        Encoders.encode_base64 (part)
        part.add_header ('Content-Disposition', 'attachment; filename="Crashplan Device Report.csv"')
        msg.attach (part)

    s = smtplib.SMTP('localhost')
    s.sendmail(sender, [recipient], msg.as_string())
    s.quit()
    return

# Function - Prepare and execute the HTTP request
def request_computers(type):
    import requests
    from requests.auth import HTTPBasicAuth
    from requests.packages.urllib3.exceptions import InsecureRequestWarning
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    HTTPParams = {
        'status': {'srtKey': 'lastBackup', 'srtDir': 'desc'},
        'version': {'srtKey': 'name', 'srtDir': 'asc'}
    }

    url = 'https://backups.intranet.psfc.coop:4285/api/Computer'
    parameters = {'active': 'true',
                  'incBackupUsage': 'true',
                  'srtKey': HTTPParams[type]['srtKey'],
                  'srtDir': HTTPParams[type]['srtDir']}
    username = 'sysadmin@psfc.coop'
    password = 'Balm-fiche'
    r = requests.get(url, params=parameters, verify=False, auth=HTTPBasicAuth(username, password))

    # Return the response as JSON
    return (r.json())

# Function - Append computer detail info to report
def append_to_report (computer, str, format):
    try:
        if format == 'list':
            str += \
                "Computer: %s\n" % computer["name"] + \
                "Alert State: %s\n" % computer["backupUsage"][0]["alertStates"][0] + \
                "OS/Version: %s/%s\n" % (computer["osName"], computer["osVersion"]) + \
                "Last Backup Date: %s\n" % format_date(computer["backupUsage"][0]["lastBackup"],'%m/%d/%y, %I:%M %p') + \
                "Percent Complete: %d\n\n" % computer["backupUsage"][0]["percentComplete"]
        elif format == 'csv':
            str += \
                "%s," % computer["name"] + \
                "%s," % computer["remoteAddress"].split(':')[0] + \
                "%s," % computer["osName"] + \
                "%s," % computer["osVersion"] + \
                "%s," % computer["productVersion"] + \
                "%s," % computer["javaVersion"] + \
                "%s," % computer["backupUsage"][0]["alertStates"][0] + \
                "%s," % format_date(computer["backupUsage"][0]["lastBackup"],'%m/%d/%y %I:%M %p') + \
                "%d\n" % computer["backupUsage"][0]["percentComplete"]
    except:
        pass # IndexError or value missing from dictionary
    return (str)

def generate_report(args):
    # Initialize global variables
    totalOK = 0
    totalWarning = 0
    totalCritical = 0
    details = ""
    report = ""

    computers = request_computers(args.type)

    # Iterate through each computer in the dictionary
    for computer in computers["data"]["computers"]:
        if computer["alertState"] == 2:
            totalCritical += 1
            details = append_to_report(computer, details, args.format)
        elif computer["alertState"] == 1:
            totalWarning += 1
            details = append_to_report(computer, details, args.format)
        elif computer["alertState"] == 0:
            totalOK += 1
            if args.type == 'version':
                details = append_to_report(computer, details, args.format)

    # Assemble the complete report
    if args.format == 'list':
        report += \
            "Total OK: %d\n" % totalOK + \
            "Total Warning: %d\n" % totalWarning + \
            "Total Critical: %d\n" % totalCritical
        if details != "":
            report += \
                "\nDETAILS\n" + \
                "----------------------------------------\n" + \
                details
    elif args.format == 'csv':
        report += \
            "Computer,IP Address,OS Name,OS Version,Crashplan Version,Java Version,Alert State,Last Backup Date,Percent Complete\n" + \
            details

    # Output the report
    if args.output == 'mail':
        send_email(report, args.format, args.recipient)
    elif args.output == 'print':
        print report
    return

def main():
    import sys, traceback

    try:
        parser = define_parser()
        args = parser.parse_args()

        if args.verbose:
            print args

        args.func(args)
    except:
        if args.verbose:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
            print ''.join('!! ' + line for line in lines)
    return

if __name__ == '__main__':
    main()
