import sys
import os
import re

from web.backend.main import app
from fastapi.routing import APIRoute

code_endpoints = []
for route in app.routes:
    if isinstance(route, APIRoute):
        code_endpoints.append(f"{list(route.methods)[0]} {route.path}")

code_endpoints.sort()

with open('docs/api.md', 'r', encoding='utf-8') as f:
    docs_content = f.read()

docs_endpoints = []
# Match patterns like: **`GET` /api/analytics-tools** or `GET /api/health`
for match in re.finditer(r'`(GET|POST|PUT|DELETE|PATCH)`\s+(/api/[^\s*]+)', docs_content):
    docs_endpoints.append(f"{match.group(1)} {match.group(2)}")

docs_endpoints = sorted(list(set(docs_endpoints)))

code_set = set(code_endpoints)
docs_set = set(docs_endpoints)

print("--- Endpoints v kódu a dokumentaci ---")
for ep in sorted(code_set & docs_set):
    print(ep)
    
print("\n--- Endpoints jen v kódu ---")
for ep in sorted(code_set - docs_set):
    print(ep)
    
print("\n--- Endpoints jen v dokumentaci ---")
for ep in sorted(docs_set - code_set):
    print(ep)
