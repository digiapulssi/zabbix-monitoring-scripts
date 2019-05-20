#/opt/freeware/bin/bash
# Version 1.1
set -e
# @args process_name
#
# exmaple data:
# zabbix_agentd 00:00:17
# zabbix_agentd 00:00:13
#
# @output elapsed CPU time of the given process, summing up all CPU times of processes with identical name
# example output:
# 30
# If process is not found from running processes, returned value is 0

# 1. 'ps -A -o comm= -o time= ' prints all process columns
# 2. 'grep "^$1 "' grep rows where wanted process name
# 3. 'sed 's/^.*\([0-9:]\{8\}\)$/\1/g'' sed everything else than numbers off
# 4. 'sed 's/:/ /g'' sed ':' characters out from time and replace with whitespace
# 5. 'awk '{print $3 + $2 * 60 + $1 * 3600}'' sum seconds minutes and hours together
# 6. 'xargs' for converting standard input into arguments
# 7. 'sed 's/ /+/g'' replaces whitespaces with '+'. So the results is like mathematic formula.

val=$(ps -A -o comm= -o time= | grep "^$1 " | sed 's/^.*\([0-9:]\{8\}\)$/\1/g' | sed 's/:/ /g' | awk '{print $3 + $2 * 60 + $1 * 3600}' | xargs | sed 's/ /+/g' | bc)

if [ -z ${val} ] ; then
        echo "0"
else
        echo $val
fi
