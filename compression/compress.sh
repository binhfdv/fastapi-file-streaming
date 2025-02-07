#!/bin/bash

INPUT_DIR="./data/input"
OUTPUT_DIR="./data/compressed"

# Create output directory if it doesn't exist
mkdir -p "$INPUT_DIR"
mkdir -p "$OUTPUT_DIR"

while true; do
    echo "Running compression.."
    # Loop through all .ply files and compress them
    for file in "$INPUT_DIR"/*.ply; do
        if [ -f "$file" ]; then
            output_file="$OUTPUT_DIR/$(basename "$file" .ply).drc"
            echo "Compressing $file to $output_file..."
            draco_encoder -i "$file" -o "$output_file" -cl 10
            rm -rf "$file"
        fi
    done
done