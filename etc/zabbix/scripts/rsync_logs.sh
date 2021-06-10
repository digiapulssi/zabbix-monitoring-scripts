#!/bin/bash

# Transfer files to destination server via rsync

set -e

SOURCEFILE="$1"
DESTINATIONPATH="$2"
DESTINATIONSERVER="$3"
RSYNCVARS="$4"

# Check that rsync variables file exists and create one if not
if [ ! -f "$RSYNCVARS" ]; then
  touch "$RSYNCVARS"
  cat > "$RSYNCVARS" << EOL
  INODE=0  
  DELETE=0
  PREVSIZE=0
EOL
fi

source "$RSYNCVARS"

# Check the inode of logfile
NEWINODE=$(ls -i "$SOURCEFILE" | awk '{print $1}')

# Check the size of logfile
LOGFILESIZE=$(wc -c "$SOURCEFILE" | awk '{print $1}')

# If log has rotated, delete destination file
if [ $DELETE -eq "1" ]; then
  ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null rsync@$DESTINATIONSERVER "rm $DESTINATIONPATH"
  DELETE=0
fi

# Check has the log rotated. Option 1: Original log has moved and new file has been created. Option 2: The file has same inode although it has been rotated.
if [ $NEWINODE -eq $INODE ] || [ $INODE -eq "0" ]; then
  if [ $LOGFILESIZE -lt $PREVSIZE ]; then
    ROTATED=1
  else
    ROTATED=0
  fi
else
  ROTATED="1"
fi

# If rotated, find the old file and transfer remaining rows
if [ $ROTATED -eq "1" ]; then
  OLDLOGFILEPATH=$(dirname "$SOURCEFILE")
    OLDLOGFILEPATH=$(find "$OLDLOGFILEPATH" -inum "$INODE" 2>/dev/null || true)
    if [ ! -z "$OLDLOGFILEPATH" ]; then
      rsync -za --append --chmod=o+r -e "ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null" "$OLDLOGFILEPATH" rsync@$DESTINATIONSERVER:"$DESTINATIONPATH"
    fi
  DELETE=1
else
  rsync -za --append --chmod=o+r -e "ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null" "$SOURCEFILE" rsync@$DESTINATIONSERVER:"$DESTINATIONPATH"
fi

# Set variables in helper file
cat > "$RSYNCVARS" << EOL
INODE=${NEWINODE}
DELETE=${DELETE}
PREVSIZE=${LOGFILESIZE}
EOL
