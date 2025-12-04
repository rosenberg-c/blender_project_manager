
#!/bin/sh

ROOT="$1"
DRY="$2"

if [ -z "$ROOT" ]; then
    echo "Usage: $0 <path> [--dry]"
    exit 1
fi

if [ "$DRY" = "--dry" ]; then
    echo "Dry run: listing .blend1 files under $ROOT"
    find "$ROOT" -type f -name "*.blend1" -print
else
    echo "Deleting .blend1 files under $ROOT"
    find "$ROOT" -type f -name "*.blend1" -print -exec rm -f {} \;
fi
