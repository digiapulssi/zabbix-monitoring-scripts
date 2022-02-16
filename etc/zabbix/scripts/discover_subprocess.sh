#!/bin/sh
# Version: 1.0
set -e


if [ "$#" -ne 3 ]
then
  echo "Missing or too many command line arguments. Usage: discover.subprocess[<process_name>, <first_nth_column>, <second_nth_column>]"
  exit 1
fi

# Discover all running processes with the given process name (first cmdline parameter)
# Print the startup arguments of the processes using awk
# The first argument is fifth column in ps command output
PROCESS="$1"
PARAM1_COL=`expr $2 + 4`
PARAM2_COL=`expr $3 + 4`

echo -n '{"data":['

# Uses first command line argument to filter processes
# Filter away processes with no cumulative CPU time with grep -v
# Filter away kernel processes (and also zombie processes) by filtering out processes that don't use any user memory (vsz == 0)

# Example output of ps command:
# DataFlowEngine  00:01:16 2822924 DataFlowEngine ACEBET1 00000000-0000-0000-0000-000000000000 EJSGRP1
# DataFlowEngine  00:00:22 3427168 DataFlowEngine ACEBET1 00000000-0000-0000-0000-000000000000 HTTPGRP1
# DataFlowEngine  00:00:07 2466424 DataFlowEngine ACEBET1 00000000-0000-0000-0000-000000000000 MONITORGRP1

ps -A -o comm= -o time= -o vsz= -o args= | egrep "^$PROCESS " | grep -v ' 00:00:00' | awk '$3 != 0' | awk -v a="$PARAM1_COL" -v b="$PARAM2_COL" '{print $1 " " $a " " $b}' | sed 's/\(.*\) \(.*\) \(.*\)/{"{#COMMAND}":"\1", "{#PARAM1}":"\2", "{#PARAM2}":"\3"}/g' | sed '$!s/$/,/' | tr '\n' ' '

echo -n ']}'
