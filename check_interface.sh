#!/bin/bash
# Name: check_interface.sh
# Description: Nagios plugin to check interface status, returns sent and received bits per second as performance data
# Requires: net-snmp, net-snmp-utils
# Author: John McNally, jmcnally@acm.org
# Release date: 8/24/2024

# Variables
status=0
prefixes=0
current_received=0
current_sent=0
file='/tmp'
warning=0
critical=0
usage="Usage: $0 -H <hostname> -C <community> -d <descr> [ -f <file> -w <warning> -c <critical> -v -h ]"
ifindex=0

# Nagios Status Codes
OK=0
WARNING=1
CRITICAL=2
UNKNOWN=3

# Process arguments
while getopts ":d:C:H:f:w:c:vh" options; do
  case $options in
    d ) descr="$OPTARG";;
    C ) community="$OPTARG";;
    H ) hostname="$OPTARG";;
    f ) file="$OPTARG";;
    w ) warning="$OPTARG";;
    c ) critical="$OPTARG";;
    v ) verbose=true;;
    h ) echo $usage
        exit 0;;
    \?) echo "Invalid option: -$OPTARG" 2>&1
        echo $usage
        exit 1;;
    * ) echo $usage
        exit 1;;
  esac
done

if [[ $hostname == '' ]] || [[ $community == '' ]] || [[ $descr == ''  ]]; then
  echo "ERROR - mandatory argument(s) missing"
  echo $usage
  exit $UNKNOWN
fi

ifindex=`/usr/bin/snmpwalk -v 2c -On -c $community $hostname .1.3.6.1.2.1.2.2.1.2 | grep $descr | cut -d '=' -f 1 | rev | cut -d'.' -f 1 | xargs`

if [[ $ifindex == '' ]]; then
  echo "ERROR - Interface $descr not found."
  exit $UNKNOWN
fi

ifstatus=`/usr/bin/snmpget -v 2c -On -c $community $hostname .1.3.6.1.2.1.2.2.1.8.$ifindex | cut -d ' ' -f 4 | cut -d '(' -f 1`

if [[ $ifstatus == 'down' ]]; then
  echo "CRITICAL - Interface $descr (index $ifindex) is down."
  exit $CRITICAL
fi

current_date=`date +%s`
current_received=`snmpget -v 2c -On -c $community $hostname .1.3.6.1.2.1.31.1.1.1.6.$ifindex | cut -d ':' -f 2 | sed 's/ *//'`
current_sent=`snmpget -v 2c -On -c $community $hostname .1.3.6.1.2.1.31.1.1.1.10.$ifindex | cut -d ':' -f 2 | sed 's/ *//'`

# Read previous values from tmp file
if [[ -e $file/check_interface_${hostname}_${ifindex} ]]; then
 last_output=`/bin/cat $file/check_interface_${hostname}_${ifindex}`
 last_date=`echo $last_output | cut -f2 -d":"`
 last_sent=`echo $last_output | cut -f4 -d":"`
 last_received=`echo $last_output | cut -f6 -d":"`
else
  last_date=$current_date
  last_sent=0
  last_received=0
fi

# Determine performance values
elapsed=`expr $current_date - $last_date`
received=`expr $current_received - $last_received`
sent=`expr $current_sent - $last_sent`

received_bps=`echo "$received * 8 / $elapsed" | bc`
sent_bps=`echo "$sent * 8 / $elapsed" | bc`

# Write data file
echo "current_date:$current_date:sent:$current_sent:received:$current_received" > $file/check_interface_${hostname}_${ifindex}

# Check for negative values (possible after a router reboot)
if [[ received -lt 0 ]] || [[ sent -lt 0 ]]; then
  echo "UNKNOWN - value out of range"
  exit $UNKNOWN
fi

# Output verbose
if [[ $verbose == true ]]; then
  echo "descr=$descr, community=$community, hostname=$hostname, file=$file, warning=$warning, critical=$critical, verbose=$verbose"
  echo "current_date=$current_date, current_sent=$current_sent, current_received=$current_received"
  echo "last_date=$last_date, last_sent=$last_sent, last_received=$last_received"
  echo "ifindex=$ifindex elapsed=$elapsed, received=$received, sent=$sent"
fi

if [[ $critical -ne 0 ]]; then
  if [[ $received_bps -gt $critical ]]; then
    echo "CRITICAL - received_bps=$received_bps > $critical | received_bps=$received_bps, sent_bps=$sent_bps"
    exit $CRITICAL
  fi
fi

if [[ $warning -ne 0 ]]; then
  if [[ $received_bps -gt $warning ]]; then
    echo "WARNING - received_bps=$received_bps > $warning | received_bps=$received_bps, sent_bps=$sent_bps"
    exit $WARNING
  fi
fi

# Normal output
echo "OK - Interface $descr (index $ifindex) is up. received_bps=$received_bps, sent_bps=$sent_bps | received_bps=$received_bps, sent_bps=$sent_bps"
exit $OK
