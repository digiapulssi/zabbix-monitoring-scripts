#!/bin/bash
set -e

# This script makes a tar.gz package for scripts installation under AIX
pushd etc/zabbix/
tar zcvf ../../zabbix-monitoring-scripts-aix.tar.gz *
popd
