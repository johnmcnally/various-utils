#!/bin/bash
# Name: check_bgp.sh
# Description: Nagios plugin to check BGP state. Also returns total prefixes, sent updates and received updates as performance data
# Requires: net-snmp, net-snmp-utils
# Author: John McNally, jmcnally@acm.org
# Release date: 8/29/2024

do_state() {
  # State info
  state=`/usr/bin/snmpget -v1 -On -c $community $hostname .1.3.6.1.2.1.15.3.1.2.$neighbor | cut -d ':' -f 2 | sed 's/ *//'`
  admin_status=`/usr/bin/snmpget -v1 -On -c $community $hostname .1.3.6.1.2.1.15.3.1.3.$neighbor | cut -d ':' -f 2 | sed 's/ *//'`
  remote_as=`/usr/bin/snmpget -v1 -On -c $community $hostname .1.3.6.1.2.1.15.3.1.9.$neighbor | cut -d ':' -f 2 | sed 's/ *//'`
  established_time=`/usr/bin/snmpget -v1 -On -c $community $hostname .1.3.6.1.2.1.15.3.1.16.$neighbor | cut -d ':' -f 2 | sed 's/ *//'`
  est_time_fmt=`date -ud "@$established_time" +"$(( $established_time/3600/24 ))d%Hh%Mm%Ss"`

  # Output verbose
  if [[ $verbose == true ]]; then
    echo "neighbor=$neighbor, community=$community, hostname=$hostname, file=$file, warning=$warning, critical=$critical, verbose=$verbose"
    echo "state=$state, admin_status=$admin_status, remote_as=$remote_as, established_time=$established_time"
  fi

  if [[ $admin_status -eq 1 ]]; then
    echo "WARNING - $neighbor (AS$remote_as) state is administratively down."
    exit $WARNING
  fi

  case $state in
    1 ) echo "CRITICAL - $neighbor (AS$remote_as) state is idle(1)."
        exit $CRITICAL;;
    2 ) echo "CRITICAL - $neighbor (AS$remote_as) state is connect(2)."
        exit $CRITICAL;;
    3 ) echo "CRITICAL - $neighbor (AS$remote_as) state is active(3)."
        exit $CRITICAL;;
    4 ) echo "CRITICAL - $neighbor (AS$remote_as) state is opensent(4)."
        exit $CRITICAL;;
    5 ) echo "CRITICAL - $neighbor (AS$remote_as) state is openconfirm(5)."
        exit $CRITICAL;;
    6 ) do_perf_data
        echo "OK - $neighbor (AS$remote_as) state is established(6). Established for $est_time_fmt. prefixes=$prefixes, received=$received, sent=$sent | prefixes=$prefixes, received=$received, sent=$sent"
        exit $OK;;
  esac
}

do_perf_data() {
  # Prefixes don't need history to be determined
  prefixes=`/usr/bin/snmpget -v1 -On -c $community $hostname 1.3.6.1.4.1.9.9.187.1.2.4.1.1.$neighbor.1.1 | head -n1 | cut -d ':' -f 2 | sed 's/ *//'`

  # Messages recieved and sent are counters, so they need last value to determine the difference
  current_received=`snmpget -v1 -On -c $community $hostname .1.3.6.1.2.1.15.3.1.12.$neighbor | cut -d ':' -f 2 | sed 's/ *//'`
  current_sent=`snmpget -v1 -On -c $community $hostname .1.3.6.1.2.1.15.3.1.13.$neighbor | cut -d ':' -f 2 | sed 's/ *//'`

  if [[ -e $file/check_bgp_${hostname}_${neighbor} ]]; then
    last_output=`/bin/cat $file/check_bgp_${hostname}_${neighbor}`
    last_sent=`echo $last_output | cut -f4 -d":"`
    last_received=`echo $last_output | cut -f6 -d":"`
  else
    last_sent=0
    last_received=0
  fi

  # Determine values
  received=`expr $current_received - $last_received`
  sent=`expr $current_sent - $last_sent`

  # Write data file
  echo "neighbor:$neighbor:sent:$current_sent:received:$current_received" > $file/check_bgp_${hostname}_${neighbor}

  # Check for negative values (possible after a router reboot)
  if [[ received -lt 0 ]] || [[ sent -lt 0 ]]; then
    echo "UNKNOWN - value out of range"
    exit $UNKNOWN
  fi

  # Output verbose
  if [[ $verbose == true ]]; then
    echo "last_output=$last_output, last_sent=$last_sent, last_received=$last_received"
  fi

  if [[ $warning -ne 0 ]]; then
    if [[ $prefixes -lt $warning ]]; then
      echo "WARNING - prefixes=$prefixes < $warning | prefixes=$prefixes, received=$received, sent=$sent"
      exit $WARNING
    fi
  fi

  if [[ $critical -ne 0 ]]; then
    if [[ $prefixes -lt $critical ]]; then
      echo "CRITICAL - prefixes=$prefixes < $critical | prefixes=$prefixes, received=$received, sent=$sent"
      exit $CRITICAL
    fi
  fi
}

# MAIN()

# Variables
state=0
admin_status=0
remote_as=0
established_time=0
est_time_fmt=''
prefixes=0
current_received=0
current_sent=0
file='/tmp'
warning=0
critical=0
usage="Usage: $0 -H <hostname> -C <community> -n <neighbor> [ -f <file> -w <warning> -c <critical> -v -h ]"

# Nagios Status Codes
OK=0
WARNING=1
CRITICAL=2
UNKNOWN=3

# Process arguments
while getopts ":n:C:H:f:w:c:vh" options; do
  case $options in
    n ) neighbor="$OPTARG";;
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

if [[ $hostname == '' ]] || [[ $community == '' ]] || [[ $neighbor == ''  ]]; then
  echo "ERROR - mandatory argument(s) missing"
  echo $usage
  exit $UNKNOWN
fi

do_state
