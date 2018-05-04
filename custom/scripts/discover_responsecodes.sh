#!/bin/bash
# Version: 1.0

# This script takes path to apache configuration folder as an argument and reads lines only with 'ProxyPass' or 'Location'.
# It saves string between first and second slash to "URIS" array.
# After that it loops through "STATUSCODES" array and "URIS" array and prints all combinations as json.

set -e
STATUSCODES=(100 101 102 200 201 202 203 204 205 206 207 208 226 300 301 302 303 304 305 306 307 308 400 401 402 403 404 405 406 407 408 409 410 411 412 413 414 415 416 417 418 419 420 421 422 423 424 426 428 429 431 440 444 449 450 451 494 495 496 497 498 499 500 501 502 503 504 505 506 507 508 509 510 511 520 598 599)

# Reads files from folder line by line and takes backends from ProxyPass or Location lines and push them into array.
URIS=()
while IFS= read -r line; do
    URIS+="$line "
done < <( grep -r 'ProxyPass\|Location' $1 | grep -Po '(?<=[[:blank:]])\/[^\/ \s]*' | awk '!a[$0]++' )

IFS=$' ' read -ra URIS <<< "$URIS"

echo -n '{"data":['

var1=0
var3=$[ ${#URIS[@]} - 1 ]

while [ $var1 -lt "${#URIS[@]}" ]
do
   for (( var2 = 0; $var2 <= 76; var2++ ))
   do
      # trims last "," from last line.
      if [[ $var1 -eq $var3 && $var2 -eq 76 ]]
      then
        echo '{"{#URI}":"'${URIS[$var1]}'","{#RESPONSE}": "'${STATUSCODES[$var2]}'"}' | tr '\n' ' '
      else
        echo '{"{#URI}":"'${URIS[$var1]}'","{#RESPONSE}": "'${STATUSCODES[$var2]}'"},' | tr '\n' ' '
      fi
   done
   var1=$[ $var1 + 1 ]
done
echo -n ']}'
