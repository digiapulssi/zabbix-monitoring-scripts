#!/bin/bash
# Version: 1.0
set -e

# Find netcat command or die
NC_CMD=$(command -v netcat || command -v nc || exit 1)
# Path of docker socket
DOCKER_SOCKET=/var/run/docker.sock
# Statistics directory (parent directory must exist and be writable for user running script)
STATS_DIR=/tmp/zabbix-docker-stats

# Chech if docker socket is writable with the current user
if [ -w "$DOCKER_SOCKET" ]; then
  NC="$NC_CMD"
else
  # Current user does not belong to docker group, use sudo (requires that sudo rights given correctly in the system)
  NC="sudo $NC_CMD"
fi

# Create statistics directory if it does not exist
if [ ! -e "$STATS_DIR" ]; then
  mkdir -p $STATS_DIR
fi

# Executes GET command to docker socket
# Parameters: 1 - docker command
docker_get() {
  RESPONSE=$(printf "GET $1 HTTP/1.0\r\n\r\n" | $NC -U $DOCKER_SOCKET | tail -n 1)
}

# Executes command in docker container
# Parameters: 1 - Container name
#             2 - Command and arguments in quoted comma separated list (e.g. "ls", "-l")
docker_exec() {
  # Create command execution
  local BODY="{\"AttachStdout\": true, \"Cmd\": [$2]}"
  local CREATE_RESPONSE
  CREATE_RESPONSE=$(printf "POST /containers/$1/exec HTTP/1.0\r\nContent-Type: application/json\r\nContent-Length: ${#BODY}\r\n\r\n${BODY}" | $NC -U $DOCKER_SOCKET | tail -n 1)
  local RUN_ID=$(echo $CREATE_RESPONSE | jq ".Id // empty " | sed -e 's/"//g')

  # Start execution
  if [ "$RUN_ID" != "" ]; then
    # tr at end is used to suppress warning on bash >=4.4
    RESPONSE=$(printf "POST /exec/$RUN_ID/start HTTP/1.0\r\nContent-Type: application/json\r\nContent-Length: 2\r\n\r\n{}" | $NC -U $DOCKER_SOCKET | tr -d '\0')
  else
    RESPONSE=""
  fi
}

# Obtains last line from execution of cat file on docker container
# Parameters:: 1 - Container name
#              2 - File in container
cat_single_value() {
  local CMD="\"cat\", \"$2\""
  docker_exec $1 "$CMD"
  local VALUE=$(echo "$RESPONSE" | tail -n 1 | tr -cd "[:print:]")
  echo $VALUE
}

# Updates timestamp of statistic and returns the time elapsed since last update
# in nanoseconds
# Parameters: 1 - Container name
#             2 - Statistic name
update_stat_time() {
  local UTIME_FILE="$STATS_DIR/$1/$2.utime"
  local NEW_VALUE=$(date +%s%N)

  if [ ! -e "$UTIME_FILE" ]; then
    printf "0" >$UTIME_FILE
  fi
  local OLD_VALUE=$(cat $UTIME_FILE)

  printf "$NEW_VALUE" >$UTIME_FILE
  TIMEDIFF=$((NEW_VALUE-OLD_VALUE))
  printf $TIMEDIFF
}

# Updates statistic value and prints the old value
# Parameters: 1 - Container name
#             2 - Statistic name
#             3 - New monitored value
update_stat() {
  local STAT_FILE="$STATS_DIR/$1/$2"
  local NEW_VALUE=$3
  if [ ! -e "$STATS_DIR/$1" ]; then
    mkdir -p "$STATS_DIR/$1"
  fi

  if [ ! -e "$STAT_FILE" ]; then
    printf "0" >$STAT_FILE
  fi

  cat $STAT_FILE
  printf "$NEW_VALUE" >$STAT_FILE
}

# Statistic: Number of running docker containers
# Parameters: 1 - all or running; defaults to running
count() {
  if [ "$1" = "all" ]; then
    docker_get "/containers/json?all=true"
  else
    docker_get "/containers/json"
  fi
  echo $RESPONSE | jq "length"
}

count_all() {
  count all
}

# Docker container discovery
# Parameters: 1 - all or running; defaults to running
discovery() {
  if [ "$1" = "all" ]; then
    docker_get "/containers/json?all=true"
  else
    docker_get "/containers/json"
  fi
  LEN=$(echo $RESPONSE | jq "length")
  for I in $(seq 0 $((LEN-1)))
  do
      NAME=$(echo "$RESPONSE"|jq --raw-output ".[$I].Names[0]"|sed -e 's/^\///')
      ID=$(echo "$RESPONSE"|jq --raw-output ".[$I].Id")
      IMAGENAME=$(echo "$RESPONSE"|jq --raw-output ".[$I].Image"|sed -e 's/:.*//')
      IMAGETAG=$(echo "$RESPONSE"|jq --raw-output ".[$I].Image"|sed -e 's/.*://')

      DATA="$DATA,"'{"{#CONTAINERNAME}":"'$NAME'","{#CONTAINERID}":"'$ID'","{#IMAGENAME}":"'$IMAGENAME'","{#IMAGETAG}":"'$IMAGETAG'"'

      # Compatibility with www.monitoringartist.com Docker template
      DATA="$DATA,"'"{#HCONTAINERID}":"'$ID'"}'

  done
  echo '{"data":['${DATA#,}']}'
}

discovery_all() {
  discovery all
}

# Statistic: Container status
status() {
  docker_get "/containers/$1/json"
  STATUS=$(echo $RESPONSE | jq ".State.Status" 2>/dev/null | sed -e 's/\"//g')

  if [ "$STATUS" = "running" ]; then
    # Running
    echo "1"
  elif [ "$STATUS" = "created" ] || [ "$STATUS" = "paused" ] || [ "$STATUS" = "restarting" ]; then
    # Not started (purposefully)
    echo "2"
  elif [ "$STATUS" = "exited" ] && [ "$(echo $RESPONSE | jq '.State.ExitCode')" = "0" ]; then
    # Stopped purposefully with ok exit code => status is "not started"
    echo "2"
  elif [ "$STATUS" = "exited" ] && [ "$(echo $RESPONSE | jq '.State.ExitCode')" = "137" ]; then
    # Stopped purposefully with sigkill (exit code 137) => status is "not started"
    echo "2"
  else
    # Exited with error (accidentally) or no such container exists
    echo "0"
  fi
}

# Container up and runnig? 1 (yes) or 0 (no)
up() {
  docker_get "/containers/$1/json"
  STATUS=$(echo $RESPONSE | jq ".State.Status" 2>/dev/null | sed -e 's/\"//g')

  # Running
  if [ "$STATUS" = "running" ]; then
    echo "1"
  else
    echo "0"
  fi
}

# Statistic: Container uptime
uptime() {
  docker_get "/containers/$1/json"
  # if running
  if [ "$(echo $RESPONSE | jq '.State.Running')" = "true" ]; then
    local STARTED=$(echo $RESPONSE | jq ".State.StartedAt" | sed -e 's/\"//g')
    local STARTED_S=$(date -d $STARTED +%s)
    local NOW_S=$(date +%s)
    UPTIME=$((NOW_S-STARTED_S))
    echo $UPTIME
  else
    # not running, uptime always zero (must output some number so that zabbix item won't get into error state)
    echo "0"
  fi
}

# Statistic: Container memory
memory() {
  NEW_VALUE=$(cat_single_value $1 "/sys/fs/cgroup/memory/memory.usage_in_bytes")
  if [ "$NEW_VALUE" = "" ]; then
    echo "0"
  else
    echo $NEW_VALUE
  fi
}

# Statistic: Container disk usage
disk() {
  docker_get "/containers/$1/json?size=1"
  echo $RESPONSE | jq ".SizeRootFs"
}

# Statistic: Container CPU usage
cpu() {
  NEW_VALUE=$(cat_single_value $1 "/sys/fs/cgroup/cpuacct/cpuacct.usage")
  if [ "$NEW_VALUE" = "" ]; then
    echo "0.0000"
  else
    OLD_VALUE=$(update_stat $1 "cpuacct.usage" "$NEW_VALUE")
    TIMEDIFF=$(update_stat_time $1 "cpuacct.usage")
    perl -e "print sprintf(\"%.4f\", (($NEW_VALUE-$OLD_VALUE)<0?0:($NEW_VALUE-$OLD_VALUE)/$TIMEDIFF*100))" # cpu percent
  fi
}

# Statistic: Container network traffic in
netin() {
  NEW_VALUE=$(cat_single_value $1 "/sys/devices/virtual/net/eth0/statistics/rx_bytes")
  if [ "$NEW_VALUE" = "" ]; then
    echo "0"
  else
    OLD_VALUE=$(update_stat $1 "rx_bytes" "$NEW_VALUE")
    TIMEDIFF=$(update_stat_time $1 "rx_bytes")
    perl -e "print int(($NEW_VALUE-$OLD_VALUE)<0?0:($NEW_VALUE-$OLD_VALUE)/$TIMEDIFF*1000000000)" # nanos to seconds
  fi
}

# Statistic: Container network traffic out
netout() {
  NEW_VALUE=$(cat_single_value $1 "/sys/devices/virtual/net/eth0/statistics/tx_bytes")
  if [ "$NEW_VALUE" = "" ]; then
    echo "0"
  else
    OLD_VALUE=$(update_stat $1 "tx_bytes" "$NEW_VALUE")
    TIMEDIFF=$(update_stat_time $1 "tx_bytes")
    perl -e "print int(($NEW_VALUE-$OLD_VALUE)<0?0:($NEW_VALUE-$OLD_VALUE)/$TIMEDIFF*1000000000)" # nanos to seconds
  fi
}

# Container image up and runnig? 1 (yes) or 0 (no)
image_up() {
  running_containerid $1
  if [ "$CONTAINER_ID" = "" ]; then
    echo 0
  else
    echo 1
  fi
}

# Statistic: Container image uptime
image_uptime() {
  running_containerid $1
  if [ "$CONTAINER_ID" = "" ]; then
    echo 0
  else
    uptime $CONTAINER_ID
  fi
}

# Statistic: Container image memory
image_memory() {
  running_containerid $1
  if [ "$CONTAINER_ID" = "" ]; then
    echo 0
  else
    memory $CONTAINER_ID
  fi
}

# Statistic: Container image disk usage
image_disk() {
  running_containerid $1
  if [ "$CONTAINER_ID" = "" ]; then
    echo 0
  else
    disk $CONTAINER_ID
  fi
}

# Statistic: Container image CPU usage
image_cpu() {
  running_containerid $1
  if [ "$CONTAINER_ID" = "" ]; then
    echo 0
  else
    cpu $CONTAINER_ID
  fi
}

# Statistic: Container image network traffic in
image_netin() {
  running_containerid $1
  if [ "$CONTAINER_ID" = "" ]; then
    echo 0
  else
    netin $CONTAINER_ID
  fi
}

# Statistic: Container image network traffic out
image_netout() {
  running_containerid $1
  if [ "$CONTAINER_ID" = "" ]; then
    echo 0
  else
    netout $CONTAINER_ID
  fi
}

# Returns all running container IDs for image, one per line
image_containerids() {
  containerids $1
  for i in $CONTAINER_IDS; do
    echo $i
  done
}

# Returns all existing container IDs for image, one per line
image_containerids_all() {
  containerids $1 all
  for i in $CONTAINER_IDS; do
    echo $i
  done
}

# Get sole running container ID for image into CONTAINER_ID
# - Exit with message if multiple running
# - Empty CONTAINER_ID if there are no running containers
running_containerid() {
  CONTAINER_ID=""
  containerids $1
  for i in $CONTAINER_IDS; do
    if [ "$CONTAINER_ID" = "" ]; then
      CONTAINER_ID=$i
    else
      echo "Multiple running containers for image"
      exit 1
    fi
  done
}

# Get container IDs for imagename into CONTAINER_IDS
containerids() {
  IMAGENAME=$1
  if [ "$2" = "all" ]; then
    docker_get "/containers/json?all=true"
  else
    docker_get "/containers/json"
  fi
  CONTAINER_IDS=$(echo $RESPONSE | jq '.[]|select(.Image|test("^'$IMAGENAME'(:.*)?$"))|.Id' | sed -e 's/\"//g')
}

if [ $# -eq 0 ]; then
  echo "No arguments"
  exit 1
elif [ $# -eq 1 ]; then
  $1
elif [ $# -eq 2 ]; then
  # Compatibility with www.monitoringartist.com docker template:
  # Remove leading slash from container id
  CONT_ID=$(echo "$1" | sed 's/^\///')

  # Execute statistic function with container argument
  $2 "$CONT_ID"
fi
