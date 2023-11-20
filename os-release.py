#!/usr/bin/python3
# Name: os-release.py
# Description: Determine if a particular release of Rocky, Alma or CentOS Linux is available
# Requires: Python 3.10 or later, python3-lxml, python3-requests, python3-dateutil
# Author: John McNally, jmcnally@acm.org
# Version: 1.05
# Release date: 11/18/2023

import sys; sys.path.insert(0, "/usr/lib/python3.6/site-packages")
import re
import requests
from lxml import html
import collections
collections.Callable = collections.abc.Callable

def get_page(os):
    # OS mirror URLs
    urls = {
        'Alma' : [
            'http://nyc.mirrors.clouvider.net/almalinux/',
            'http://mirror.cogentco.com/pub/linux/almalinux/',
            'http://iad.mirror.rackspace.com/almalinux/',
            'http://mirror.interserver.net/almalinux/'
        ],
        'CentOS' : [
            'http://mirror.centos.org/centos/',
            'http://mirrors.lga7.us.voxel.net/centos/',
            'http://mirror.cc.columbia.edu/pub/linux/centos/',
            'http://mirror.es.its.nyu.edu/centos/'
        ],
        'Rocky' : [
            'http://dl.rockylinux.org/pub/rocky/',
            'http://mirror.cogentco.com/pub/linux/rocky/',
            'http://iad.mirror.rackspace.com/rocky/',
            'http://nyc.mirrors.clouvider.net/rocky/'
        ]
    }

    for url in urls[os]:
        try:
            page = requests.get(url, timeout=10)
            return(str(page.content))
        except:
            # Unable to connect to any URL
            return None

def parse_structured(page, os, target_version):
    tree = html.fromstring(page)
    versions = tree.xpath('//tr/td[2]/a/text()')
    dates = tree.xpath('//tr/td[3]/text()')

    for i in range(len(versions)):
        if target_version in versions[i]:
            version = versions[i].strip('/')
            date = format_date(dates[i].strip(),'%B %-d, %Y at %-I:%M %p')
            print(f"{os} {version} was released or updated on {date}")

def parse_unstructured(page, os, target_version):
    lines = page.split("\r\n")

    for line in lines:
        if (target_version in line) and ('RC' not in line):
            m = re.search('\s\s+(.+?)\s\s+', line)
            if m:
                date = format_date(m.group(1), '%B %-d, %Y at %-I:%M %p')
                print (f"{os} {target_version} was released or updated on {date}")
            else:
                print (f"{os} {target_version} was released or updated, date undetermined")

def format_date(datestring, formatstring):
    from datetime import date
    import dateutil.parser
    d = dateutil.parser.parse(datestring)
    return d.strftime(formatstring)

def usage():
    print ("usage: os-release.py [ [ -a | -c | -r ] VERSION ] | -h ]\n \
    -a           OS AlmaLinux\n \
    -c           OS CentOS\n \
    -r           OS Rocky Linux\n \
    VERSION	 target OS version (n.n)\n \
    -h           show this help message and exit")

# MAIN()

if len(sys.argv) == 3:
    if sys.argv[1] == '-h':
        usage()
        sys.exit(0)
    else:
        match sys.argv[1]:
            case '-a' : os = 'Alma'
            case '-c' : os = 'CentOS'
            case '-r' : os = 'Rocky'
            case _:
                print("ERROR: must specify OS: -a, -c or -r")
                sys.exit(1)

        target_version = sys.argv[2]
else:
    usage()
    sys.exit(1)

page = get_page(os)

if page is None:
    print (f"ERROR: Unable to connect to any {os} mirror")
    sys.exit(1)

if os == 'CentOS':
    parse_structured(page, os, target_version)
else:
    parse_unstructured(page, os, target_version)
