#!/usr/bin/env python3
import sys
import re

with open(sys.argv[1], 'r') as f:
    content = f.read()

# Fix unsafe realm_access access (variable name may change between builds)
pattern = r'([a-zA-Z_$][a-zA-Z0-9_$]*)\.principal\.claims\.realm_access\.roles\.includes\("app-admin"\)'
replacement = r'\1.principal.claims?.realm_access?.roles?.includes("app-admin")??false'
new_content, count = re.subn(pattern, replacement, content)
if count > 0:
    content = new_content
    print(f"Patched {count} realm_access access(es)")
else:
    print("WARNING: pattern not found")
    idx = content.find('realm_access')
    if idx >= 0:
        print(f"  Found 'realm_access' at byte {idx}: {content[max(0,idx-30):idx+80]}")
    else:
        print("  No 'realm_access' found in file at all")

with open(sys.argv[1], 'w') as f:
    f.write(content)
print("Done")
