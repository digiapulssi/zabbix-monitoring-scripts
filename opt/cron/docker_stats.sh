#!/bin/bash
# Script for running docker monitoring script actions and posting results via trapper items.
#
# USAGE:
# Discover running containers:
#   /opt/cron/docker_stats.sh discovery
# Discover all containers:
#   /opt/cron/docker_stats.sh discovery_all
# Count running containers:
#   /opt/cron/docker_stats.sh count
# Count all containers:
#   /opt/cron/docker_stats.sh count_all
# Send stats to trapper items:
#   /opt/cron/docker_stats.sh stats "<stats>" "<containers>"
#   - OPTIONAL stats: space delimited list of stats, defaults to all supported stats (cpu disk netin netout memory status uptime)
#   - OPTIONAL containers: space delimited list of container names or ids, defaults to all containers
#
set -e

# Path to Zabbix agent script docker.sh
ZBX_DOCKER_SCRIPT=/etc/zabbix/scripts/docker.sh
# Path to temporary stats file
STATS_FILE=/tmp/docker_stats.txt

SCRIPT_ACTION=$1
shift

rm -f $STATS_FILE
if [ "$SCRIPT_ACTION" == "stats" ]; then
    stats=${1:-cpu disk netin netout memory status uptime}
    containers=$2
    if [ -z "$containers" ]; then
        containers=$($ZBX_DOCKER_SCRIPT discovery_all | jq -r '.[][]["{#CONTAINERNAME}"]')
    fi

    for c in $containers; do
        for s in $stats; do
            value=$($ZBX_DOCKER_SCRIPT $c $s)
            echo "- docker.containers[$c,$s] $value" >>$STATS_FILE
        done
    done
elif [ "$SCRIPT_ACTION" == "discovery" ]; then
    value=$($ZBX_DOCKER_SCRIPT discovery)
    echo "- docker.containers.discovery $value" >>$STATS_FILE
elif [ "$SCRIPT_ACTION" == "discovery_all" ]; then
    value=$($ZBX_DOCKER_SCRIPT discovery_all)
    echo "- docker.containers.discovery.all $value" >>$STATS_FILE
elif [ "$SCRIPT_ACTION" == "count" ]; then
    value=$($ZBX_DOCKER_SCRIPT count)
    echo "- docker.containers.count $value" >>$STATS_FILE
elif [ "$SCRIPT_ACTION" == "count_all" ]; then
    value=$($ZBX_DOCKER_SCRIPT count_all)
    echo "- docker.containers.count.all $value" >>$STATS_FILE
fi

# Send results if we got some
if [ -e $STATS_FILE ]; then 
    zabbix_sender -vv -c /etc/zabbix/zabbix_agentd.conf -i $STATS_FILE
    rm -f $STATS_FILE
fi