#!/bin/sh
# Version: 1.0

# This script takes path to apache configuration folder as an argument and reads lines only with 'ProxyPass' or 'Location'.
# It takes all backends between first and second slash and prints them out as json format.

set -e

echo -n '{"data":['

# Removes duplicates with awk and formats to json with sed
grep -r 'ProxyPass\|Location' $1 | grep -Po '(?<=[[:blank:]])\/[^\/ \s]*' | awk '!a[$0]++' | sed 's/\(.*\)/{"{#URI}":"\1"}/g' | sed '$!s/$/,/' | tr '\n' ' '
echo -n ']}'
