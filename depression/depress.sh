#!/bin/bash

INPUT_DIR="./data/compressed"
OUTPUT_DIR="./data/depressed"

# Create necessary directories
mkdir -p "$INPUT_DIR"
mkdir -p "$OUTPUT_DIR"

while true; do
    echo "Running depression.."

    echo "---Checking for zip files..."
    # Process all zip files in the input directory
    for zipfile in "$INPUT_DIR"/*.zip; do
        if [ -f "$zipfile" ]; then
            echo "Extracting $zipfile..."
            unzip "$zipfile" -d "$OUTPUT_DIR"
            rm -f "$zipfile"
        fi
    done

    echo "---Checking for drc files..."
    # Process all drc files in the output directory
    for drc_file in "$OUTPUT_DIR"/*.drc; do
        if [ -f "$drc_file" ]; then
            ply_file="$OUTPUT_DIR/$(basename "$drc_file" .drc).ply"
            echo "Decoding $drc_file to $ply_file..."
            draco_decoder -i "$drc_file" -o "$ply_file"
            rm -f "$drc_file"
        fi
    done
done
