#/opt/freeware/bin/bash
set -e
ps -A -o comm= -o time= | grep "^$1 " | sed 's/^.*\([0-9:]\{8\}\)$/\1/g' | sed 's/:/ /g' | awk '{print $3 + $2 * 60 + $1 * 3600}' | xargs | sed 's/ /+/g' | bc

