#!/bin/bash

DIR="kubeseal"
PUB="pub.pem"

# Loop through all files in the specified directory matching the extension
for filepath in "$DIR"/*.yaml; do
    # Check if the glob found any files (prevents running on the literal '*.txt' string if no files are found)
    if [ -f "$filepath" ]; then
        echo "Found file path: $filepath"
        # Extract just the filename from the path
        filename=$(basename "$filepath")
        name="${filename%.*}"
         if [[ "$name" != *"-sealed"* ]]; then
          kubeseal --format=yaml --cert=pub.pem < $filename > $DIR/"${name}-sealed.yaml"
          git rm --cached "$DIR/$filename"
          git add $DIR/"${name}-sealed.yaml"
         fi
        # Add your processing commands here
    fi
done