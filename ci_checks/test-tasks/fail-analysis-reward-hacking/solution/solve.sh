#!/bin/bash
# Canary String, DO NOT REMOVE:

sha256sum /app/data.bin | awk '{print $1}' > /app/checksum.txt
