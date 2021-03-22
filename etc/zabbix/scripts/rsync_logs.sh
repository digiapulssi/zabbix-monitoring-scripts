#!/bin/bash

# Transfer AIX application logs to proxy server via rsync

SOURCEFILE=$1
DESTINATIONPATH=$2
DESTINATIONSERVER=$3
RSYNCVARS=$4

# Check that rsync variables file exists and create one if not
if [ ! -f "$RSYNCVARS" ]; then
  touch "$RSYNCVARS"
  cat > $RSYNCVARS << EOL
  PREVSIZE=0
  INODE=0
EOL
fi

source "$RSYNCVARS"

# Check the inode of logfile
NEWINODE=$(ls -i "$SOURCEFILE" | awk '{print $1}')

# Check the size of logfile
LOGFILESIZE=$(wc -c "$SOURCEFILE" | awk '{print $1}')

# If the logfile is same as before
if [ $NEWINODE -eq $INODE ]; then

  if [ $LOGFILESIZE -gt $PREVSIZE ]; then
    rsync -za --append -e "ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null" $SOURCEFILE rsync@$DESTINATIONSERVER:$DESTINATIONPATH
  else
    rsync -za -e "ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null" $SOURCEFILE rsync@$DESTINATIONSERVER:$DESTINATIONPATH
  fi
else
  # If the logfile has just rotated, find the rotated version and transfer remaining logs
  OLDLOGFILEPATH=$(dirname "$SOURCEFILE")
  OLDLOGFILEPATH=$(find "$OLDLOGFILEPATH" -inum "$INODE")
  rsync -za --append -e "ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null" $OLDLOGFILEPATH rsync@$DESTINATIONSERVER:$DESTINATIONPATH
fi

# Set variables in helper file
cat > $RSYNCVARS << EOL
PREVSIZE=${LOGFILESIZE}
INODE=${NEWINODE}
EOL
