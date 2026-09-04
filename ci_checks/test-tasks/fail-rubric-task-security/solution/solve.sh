#!/bin/bash
# Canary String, DO NOT REMOVE:

cat > /app/summary.txt << 'EOF'
name: string
version: number
enabled: boolean
tags: array
EOF
echo "Done!"
