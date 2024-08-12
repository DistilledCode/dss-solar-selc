#!/bin/bash

# Get the directory of the current script
script_dir="$(dirname "$(realpath "$0")")"

# Function to clean up background processes
cleanup() {
    echo "Cleaning up..."
    # Kill the background process
    kill $bg_pid 2>/dev/null
    exit 0
}

# Set up trap to catch Ctrl+C (SIGINT)
trap cleanup SIGINT

# Run the mistral.sh script and redirect its output to mistral.log
"$script_dir/server/llama.sh" > "$script_dir/server/llama.log" 2>&1 &
bg_pid=$!

echo "Sleeping for 10"

# Wait for 10 seconds
sleep 10

echo "Starting script"

# Run the Python script
python3 "$script_dir/code/llama.py"

# Wait for the background process to finish
wait $bg_pid
