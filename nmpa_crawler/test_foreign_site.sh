#!/bin/bash

# Test foreign website connectivity script
# Usage: ./test_foreign_site.sh [URL]

# Default URL if none provided
DEFAULT_URL="https://www.youtube.com"

# Use provided URL or default
URL=${1:-$DEFAULT_URL}

echo "Testing connectivity to: $URL"
echo "================================"

# Test with curl and show timing information
curl -w "\n\nConnection Statistics:\n----------------------\nTime total: %{time_total}s\nTime connect: %{time_connect}s\nTime DNS: %{time_namelookup}s\nHTTP code: %{http_code}\n" \
    -o /dev/null -s -L "$URL"

echo "================================"
echo "Test completed."