#!/bin/sh
# Version: 1.0
set -e

# Discover all running process names
# Use the process name in /proc/pid/status that's truncated to 15 characters
# because it's the most reliable name used by Zabbix process monitoring items
# See https://www.zabbix.com/documentation/3.0/manual/appendix/items/proc_mem_num_notes

echo -n '{"data":['
# Filter away processes with no cumulative CPU time with grep -v
# Filter away kernel processes (and also zombie processes) by filtering out processes that don't use any user memory (vsz == 0)
# Take only 15 characters (to leave out the time portion) with cut
# Remove duplicates with awk, format to json with sed
ps -A -o comm= -o time= -o vsz= | grep -v ' 00:00:00' | awk '$3 != 0' | cut -c-15 | sed 's/ *$//' | awk '!a[$0]++' | sed 's/\(.*\)/{"{#COMMAND}":"\1"}/g' | sed '$!s/$/,/' | tr '\n' ' '
echo -n ']}'
