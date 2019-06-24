#!/opt/freeware/bin/bash
# Version: 0.1
set -e

# Discover all running process with same process name (first argument)
# Use the process name in /proc/pid/status that's truncated to 15 characters
# because it's the most reliable name used by Zabbix process monitoring items
# See https://www.zabbix.com/documentation/3.0/manual/appendix/items/proc_mem_num_notes

echo -n '{"data":['
# Uses first command line argument to show chosen process with startup arguments
# Filter away processes with no cumulative CPU time with grep -v
# Filter away kernel processes (and also zombie processes) by filtering out processes that don't use any user memory (vsz == 0)
# Captures first, fifth and seventh string (defaults for process name, IIBNODE name and excecuiton group)
# -> Script is currently dependet of the amount of start up parameters
# Output: json
# {
#	  "data": [
#		  {
#			  "{#COMMAND}": "DataFlowEngine",
#			  "{#IIBNODE}": "IBEAISANDBOX",
#		  	"{#EXCECUTIONGROUP}": "SERVICEGRP1"
#	    }
#	  ]
# }

ps -A -o comm= -o time= -o vsz= -o args= | grep "$1" | grep -v ' 00:00:00' | awk '$3 != 0' | awk '{print $1 " " $5 " " $7}' | sed 's/\(.*\) \(.*\) \(.*\)/{"{#COMMAND}":"\1", "{#IIBNODE}":"\2", "{#EXCECUTIONGROUP}":"\3"}/g' | sed '$!s/$/,/' | tr '\n' ' '
echo -n ']}'
