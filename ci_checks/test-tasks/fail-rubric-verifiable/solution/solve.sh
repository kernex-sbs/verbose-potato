#!/bin/bash
# Canary String, DO NOT REMOVE:

cat > /app/organize.py << 'EOF'
items = ["banana", "apple", "cherry"]
print(sorted(items))
EOF
echo "Done!"
