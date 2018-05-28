#!/bin/bash
set -e

kontena_api_v1() {
  RESPONSE=$(curl -k -s \
    -H "Authorization: Bearer $AUTH_TOKEN" \
  	-H "Accept: application/json" \
  	"$1")

  echo $RESPONSE
}

CMD=$1
MASTER_ADDRESS=$2
AUTH_TOKEN=$3
GRID=$4

if [ "$CMD" == "discover" ]; then
  kontena_api_v1 https://$MASTER_ADDRESS/v1/grids/$GRID/nodes | jq '.nodes | map({"{#NODE}": .name}) | { "data": . }'
elif [ "$CMD" == "stat" ]; then
  NODE=$5
  STAT=$6
  kontena_api_v1 https://$MASTER_ADDRESS/v1/nodes/$GRID/$NODE | jq '.'$STAT
fi
