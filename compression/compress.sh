#!/bin/bash

INPUT_DIR="./data/input"
OUTPUT_DIR="./data/compressed"
PYTHON_SCRIPT="./store_to_redis.py"

mkdir -p "$INPUT_DIR"
mkdir -p "$OUTPUT_DIR"

while true; do
    echo "Running compression..."

    # Loop through all .ply files and compress them
    for file in "$INPUT_DIR"/*.ply; do
        if [ -f "$file" ]; then
            output_file="$OUTPUT_DIR/$(basename "$file" .ply).drc"
            echo "Compressing $file to $output_file..."
            
            # Compress using Draco encoder
            draco_encoder -i "$file" -o "$output_file" -cl 10
            
            if [ -f "$output_file" ]; then
                echo "Storing $output_file in Redis..."
                
                # Store the compressed file in Redis
                python3 "$PYTHON_SCRIPT" "$output_file"
                
                # Remove original and compressed files after storing in Redis
                rm -rf "$file"
                rm -rf "$output_file"
            else
                echo "Compression failed for $file"
            fi
        fi
    done

    # sleep 10
done
