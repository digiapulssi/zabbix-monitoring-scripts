#!/opt/freeware/bin/bash
# Version: 0.5
set -e

# Discover all running process with same process name (first cmdline parameter)
# Prints process's firt startup argument (second cmdline parameter)
# Prints process's second startup argument (third cmdline parameter)
echo -n '{"data":['
# Uses first command line argument to show chosen process with startup arguments
# Filter away processes with no cumulative CPU time with grep -v
# Filter away kernel processes (and also zombie processes) by filtering out processes that don't use any user memory (vsz == 0)
# Captures first, $2:th and $3:th string
# Usage:
# >> ./processargs.sh DataFlowEngine 5 7
# Output:
# << {
#	<<  "data": [
#	<<	  {
#	<<		  "{#COMMAND}": "DataFlowEngine",
#	<<		  "{#IIBNODE}": "IBEAISANDBOX",
#	<<	  	"{#EXCECUTIONGROUP}": "SERVICEGRP1"
#	<<    }
#	<<  ]
# << }

ps -A -o comm= -o time= -o vsz= -o args= | grep "$1" | grep -v ' 00:00:00' | awk '$3 != 0' | awk -v a="$2" -v b="$3" '{print $1 " " $a " " $b}' | sed 's/\(.*\) \(.*\) \(.*\)/{"{#COMMAND}":"\1", "{#IIBNODE}":"\2"}, "{#EXCECUTIONGROUP}":"\
3"}/g' | sed '$!s/$/,/' | tr '\n' ' '
