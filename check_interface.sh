#!/bin/bash
# Name: check_interface.sh
# Description: Nagios plugin to check interface status, returns sent and
#              received bits per second as performance data
# Requires: net-snmp, net-snmp-utils
# Author: John McNally, jmcnally@acm.org
# Release date: 9/9/2024

function do_status() {
  if [[ $hostname == '' ]] || [[ $community == '' ]] || [[ $descr == ''  ]]; then
    echo "ERROR - mandatory argument(s) missing"
    usage
    exit $UNKNOWN
  fi

  result=`/usr/bin/snmpbulkwalk -v 2c -On -c $community $hostname .1.3.6.1.2.1.2.2.1.2 2>&1`

  if [[ $? != 0  ]]; then
    echo "UNKNOWN - $result"
    exit $UNKNOWN
  fi

  ifindex=`echo $result | grep -Po "\.\K\d+?(?= = STRING: $descr)" | xargs | cut -d ' ' -f 1`

  if [[ $ifindex == '' ]]; then
    echo "ERROR - Interface $descr not found."
    exit $UNKNOWN
  fi

  ifadminstatus=`/usr/bin/snmpget -v 2c -On -c $community $hostname .1.3.6.1.2.1.2.2.1.7.$ifindex | cut -d ' ' -f 4 | cut -d '(' -f 1`
  ifstatus=`/usr/bin/snmpget -v 2c -On -c $community $hostname .1.3.6.1.2.1.2.2.1.8.$ifindex | cut -d ' ' -f 4 | cut -d '(' -f 1`

  # Output verbose
  if [[ $verbose == true ]]; then
    echo "descr=$descr, community=$community, hostname=$hostname, file=$file, warning=$warning, critical=$critical, verbose=$verbose"
    echo "ifindex=$ifindex, ifadminstatus=$ifadminstatus, ifstatus=$ifstatus"
  fi

  if [[ $ifadminstatus == 'down' ]]; then
    echo "WARNING - Interface $descr (index $ifindex) is administratively down."
    exit $WARNING
  fi

  if [[ $ifstatus == 'down' ]]; then
    echo "CRITICAL - Interface $descr (index $ifindex) is down."
    exit $CRITICAL
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
  do_perf_data
  echo "OK - Interface $descr (index $ifindex) is up. received_bps=$received_bps, sent_bps=$sent_bps | received_bps=$received_bps, sent_bps=$sent_bps"
  exit $OK
}

function do_perf_data() {
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

  # Determine values
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
    echo "current_date=$current_date, current_sent=$current_sent, current_received=$current_received"
    echo "last_date=$last_date, last_sent=$last_sent, last_received=$last_received"
  fi
}

function usage() {
echo -e "Usage: $0 -H <hostname> -C <community> -d <descr> [ -f <file> -w <warning> -c <critical> -v -h ]

Mandatory arguments:
  -H [hostname]         host or IP address to query
  -C [community]        SNMP community name (v1 or 2c)
  -d [descr]            interface description

Optional arguments:
  -f [file]             path to performance data temp file (default is /tmp/)
  -w [warning]          warning threshold (bps)
  -c [critical]         critical threshold (bps)
  -v                    show verbose output
  -h                    show usage"
}

# MAIN()

# Variables
status=0
prefixes=0
current_received=0
current_sent=0
file='/tmp'
warning=0
critical=0
ifindex=0
result=''

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
    h ) usage
        exit 0;;
    \?) echo "Invalid option: -$OPTARG" 2>&1
        usage
        exit 1;;
    * ) usage
        exit 1;;
  esac
done

do_status
