#!/bin/bash

# Exit on error
set -e

# Function to wait for Spark master
wait_for_spark() {
    echo "Waiting for Spark master..."
    until nc -z spark 7077; do
        echo "Spark master is unavailable - sleeping"
        sleep 2
    done
    echo "Spark master is up"
}

# Wait for Spark to be ready
wait_for_spark

# Start ComfyUI
echo "Starting ComfyUI..."
python main.py --port 8181 --listen 0.0.0.0 --extra-model-paths-config /comfyui/extra_model_paths.yaml
