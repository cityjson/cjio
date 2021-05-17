#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
LOG_PATH="$SCRIPT_DIR/upgrade.txt"

for filepath in $(find $directory -type f -name "*.json")
do

  file="$(basename -- "$filepath")"
  name="${file%%.*}"
  echo $name
  
  cjio "$filepath" upgrade_version save "$filepath" >> $LOG_PATH

  echo -e "\n ========== \n" >> $LOG_PATH
  
done
