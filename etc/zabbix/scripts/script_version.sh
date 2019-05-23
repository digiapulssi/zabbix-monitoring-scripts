#!/opt/freeware/bin/bash
# Version: 1.1
set -e

echo -n '{"data":['
# format to json with sed
ls $1 | sed 's/\(.*\)/{"{#SCRIPT}":"\1"}/g' | sed '$!s/$/,/' | tr '\n' ' '
echo -n ']}'
