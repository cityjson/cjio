#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
LOG_PATH="$SCRIPT_DIR/upgrade.txt"
ORIGINAL_FILES_PATH="$SCRIPT_DIR/old/"

mkdir -p "$ORIGINAL_FILES_PATH"

for filepath in $(find $directory -type f -name "*.json")
do

  file="$(basename -- "$filepath")"
  name="${file%%.*}"
  echo $file
  
  # rename original files and move to dedicated folder
  basepath="${filepath%/*}/"
  oldfilepath="$ORIGINAL_FILES_PATH$name"_old.json
  mv "$filepath" "$oldfilepath"
  
  # save upgraded files with names of original files
  cjio "$oldfilepath" upgrade save "$filepath" >> $LOG_PATH

  echo -e "\n ========== \n" >> $LOG_PATH
  
done
