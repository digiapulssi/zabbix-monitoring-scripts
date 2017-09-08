#!/bin/sh
set -e

# Discover all running process names
# Use the process name in /proc/pid/status that's truncated to 15 characters
# because it's the most reliable name used by Zabbix process monitoring items
# See https://www.zabbix.com/documentation/3.0/manual/appendix/items/proc_mem_num_notes

echo -n '{"data":['
ps -A -o comm= | awk '!a[$0]++' | sed 's/\(.*\)/"#{COMMAND}":"\1"/g' | sed '$!s/$/,/'
echo -n ']}'
