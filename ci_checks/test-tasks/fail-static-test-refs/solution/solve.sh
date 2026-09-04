#!/bin/bash
# Canary String, DO NOT REMOVE:

echo "complete" > /app/status.txt
echo '{"status": "complete"}' > /app/output.json
echo "Done!"
