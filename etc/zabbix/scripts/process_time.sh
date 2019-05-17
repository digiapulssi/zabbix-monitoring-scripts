#/opt/freeware/bin/bash
set -e
# @args process's name
# @input eg. '00:00:17'
#            '00:00:13'
# @output 30
# 1. 'ps -A -o comm= -o time= ' prints all process columns
# 2. 'grep "^$1 "' grep rows where wanted process name
# 3. 'sed 's/^.*\([0-9:]\{8\}\)$/\1/g'' sed everything else than numbers off
# 4. 'sed 's/:/ /g'' sed ':' characters out from time and replace with whitespace
# 5. 'awk '{print $3 + $2 * 60 + $1 * 3600}'' sum seconds minutes and hours together

ps -A -o comm= -o time= | grep "^$1 " | sed 's/^.*\([0-9:]\{8\}\)$/\1/g' | sed 's/:/ /g' | awk '{print $3 + $2 * 60 + $1 * 3600}' | xargs | sed 's/ /+/g' | bc
