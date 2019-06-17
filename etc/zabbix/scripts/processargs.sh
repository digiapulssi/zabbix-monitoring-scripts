#!/opt/freeware/bin/bash
# Version: 0.1
set -e

# Discover all running process with same process name (first argument)
# Use the process name in /proc/pid/status that's truncated to 15 characters
# because it's the most reliable name used by Zabbix process monitoring items
# See https://www.zabbix.com/documentation/3.0/manual/appendix/items/proc_mem_num_notes

echo -n '{"data":['
# Uses first command line argument to show chosen process with started startup arguments
# Filter away processes with no cumulative CPU time with grep -v
# Filter away kernel processes (and also zombie processes) by filtering out processes that don't use any user memory (vsz == 0)
# Removes everything between first string (process name) and last string (commandline argument)
# Output: json
#   {"data":[
#     {#COMMAND}: "<process_name>",
#     {#ARGS}: "<last_arg>"
#   ]}

ps -A -o comm= -o time= -o vsz= -o args= | grep "$1" | grep -v ' 00:00:00' | awk '$3 != 0' | sed 's/ \(.*\) / /g' | sed 's/\(.*\) \(.*\)/{"{#COMMAND}":"\1"}, {"{#ARGS}":"\2"}/g' | sed '$!s/$/,/' | tr '\n' ' '
echo -n ']}'
