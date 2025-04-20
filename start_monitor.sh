#!/bin/bash

# Default interval (1 hour)
INTERVAL=3600

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --interval)
            INTERVAL="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Create necessary directories if they don't exist
mkdir -p templates webpage_archives

# Start the monitor script in the background
python3 monitor.py --interval $INTERVAL &

# Start the web interface in the background
python3 web_interface.py &

# Print instructions
echo "Monitor and web interface started!"
echo "Monitor is checking every $INTERVAL seconds"
echo "Web interface is running at http://localhost:5199"
echo "Press Ctrl+C to stop both processes"
echo "To check status, visit http://localhost:5199 in your browser"

# Keep the script running
wait 