#!/bin/bash
set -e
# static part of the url with message type and hours params given
url='https://api.sok.fi/sok/ext/eaimonitoringflows/v1/messages?messageType='${1}'&hours='${2}   #tuotanto

RECEIVER=${3}
METRIC=${4}

## Get message count from url where Receiver is given string and Status is NOT given string.
curl -s -k -H "x-ibm-client-id:b01d833d-2417-4cc8-addc-056a8770095a" $url | jq '[.[] | select(.Receiver == "'$RECEIVER'") | select(.Status != "'$METRIC'")] | length'
