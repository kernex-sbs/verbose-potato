#!/bin/bash
# Canary String, DO NOT REMOVE:

grep -c '" 404 ' /app/access.log > /app/not_found_count.txt
