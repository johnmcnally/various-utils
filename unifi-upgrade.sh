#!/bin/bash
# Name unifi-upgrade.sh
# Description: Upgrade the current installation of Ubiquiti UniFi Controller
# Requires: CentOS 7 or RHEL 7, bash
# Author: John McNally, jmcnally@acm.org
# Version 1.00
# Release date: 10/17/2016

function usage()
{
echo -e "Usage: unifi-upgrade.sh VERSION

Mandatory arguments:
  VERSION             target version of Unifi Controller (nn.nn.nn)"
}

# Initialize variables
script_name=`echo $0 | sed -nr "s/.*\/(.*)/\1/p"`
source="/usr/local/src/tars"
destination="/opt"
unifi_user="ubnt"
https_cipher_string="TLS_ECDHE_RSA_WITH_AES_128_CBC_SHA256,TLS_ECDHE_RSA_WITH_AES_128_CBC_SHA,TLS_ECDHE_RSA_WITH_AES_256_CBC_SHA384,TLS_ECDHE_RSA_WITH_AES_256_CBC_SHA,TLS_RSA_WITH_AES_128_CBC_SHA256,TLS_RSA_WITH_AES_128_CBC_SHA,TLS_RSA_WITH_AES_256_CBC_SHA256,TLS_RSA_WITH_AES_256_CBC_SHA"

# Process args
if [ $# -ne 0 ]; then
  new_version=$1
else
  echo -e "$script_name: Must specify version number"
  usage
  exit 1
fi

# Get the current Unifi version
if [ -f $destination/UniFi/webapps/ROOT/app-unifi/.version ]; then
  current_version=`cat $destination/UniFi/webapps/ROOT/app-unifi/.version`
else
  echo "$script_name: UniFi controller not found at $destination/UniFi"
  exit 1
fi

# Download the target version
wget http://dl.ubnt.com/unifi/$new_version/UniFi.unix.zip -P $source
if [ $?	-ne 0 ]; then
  echo "$script_name: Unable to download UniFi Controller version $new_version to $source"
  exit 1
fi

# Rename the .zip file
mv $source/UniFi.unix.zip $source/UniFi.unix-$new_version.zip

# Stop the MongoDB and Unifi services
systemctl stop unifi
systemctl stop mongod

# Install the new version
mv $destination/UniFi/ $destination/UniFi-$current_version
unzip -q $source/UniFi.unix-$new_version.zip -d $destination
chown -R $unifi_user:$unifi_user $destination/UniFi

# Start the MongoDB and Unifi services
systemctl start mongod
systemctl start unifi
sleep 5

# Add HTTPS cipher string to system.properties and restart the unifi service
# The restart is necessary because system.properties is created when the controller first runs.
echo "unifi.https.ciphers=$https_cipher_string" >> $destination/UniFi/data/system.properties
systemctl restart unifi

echo "UniFi Controller successfully upgraded to version $new_version"

# Add custom NTP server to config.properties
# Note: This file is not created by default
echo config.ntp_server=time.mydomain.com >> $destination/UniFi/data/sites/default/config.properties

exit 0
