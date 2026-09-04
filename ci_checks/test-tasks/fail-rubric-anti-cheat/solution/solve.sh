#!/bin/bash
# Canary String, DO NOT REMOVE:

echo -n "benchmark" | sha256sum | awk '{print $1}' > /app/hash.txt
echo "Done!"
