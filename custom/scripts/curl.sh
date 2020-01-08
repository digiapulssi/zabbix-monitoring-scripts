#!/bin/bash
set -e

# Description:
#Silmple curl wiht one header

set -e
curl -s -H "$1" "$2"

