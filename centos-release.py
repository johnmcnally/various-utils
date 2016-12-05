#!/usr/bin/python
# Name: centos-release.py
# Description: Determine if the specified release of CentOS is available
# Requires: Python 2.6 or later, python-lxml, python-requests, python-dateutil
# Author: John McNally, jmcnally@acm.org
# Version: 1.00
# Release date: 12/5/2016

def get_page():
    import requests
    # CentOS mirrors
    urls = ['http://mirror.centos.org/centos/', \
            'http://mirrors.lga7.us.voxel.net/centos/', \
            'http://mirror.cc.columbia.edu/pub/linux/centos/', \
            'http://mirror.es.its.nyu.edu/centos/']

    for url in urls:
        try:
            page = requests.get(url, timeout=10)
            return(page)
        except:
            sys.exc_clear()

    # Unable to connect to any URL
    return None

def format_date(datestring, format):
    from datetime import date
    import dateutil.parser
    d = dateutil.parser.parse(datestring)
    return d.strftime(format)

# MAIN()
import sys
from lxml import html

target_version = sys.argv[1]
page = get_page()
if page is None:
    print "ERROR: Unable to connect to any CentOS mirror"
    sys.exit(1)

tree = html.fromstring(page.content)
versions = tree.xpath('//tr/td[2]/a/text()')
dates = tree.xpath('//tr/td[3]/text()')

for i in range(len(versions)):
    if target_version in versions[i]:
        version = versions[i].strip('/')
        date = format_date(dates[i].strip(),'%B %-d, %Y at %-I:%M %p')
        print "CentOS {0} was released or updated on {1}".format(version,date)
        sys.exit(0)

# target_version was not found
#print "CentOS {0} is not available".format(target_version)
