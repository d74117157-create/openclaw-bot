#!/usr/bin/env python3
import os
import sys
import json
from notion_client import Client

# Usage: update_notion.py '{"provider":"https://..."}'
API_KEY = os.getenv('NOTION_API_KEY')
DB_ID = os.getenv('NOTION_DB_ID')

if not API_KEY or not DB_ID:
    print('Set NOTION_API_KEY and NOTION_DB_ID')
    sys.exit(1)

client = Client(auth=API_KEY)

mapping = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
# mapping: name->url
for name, url in mapping.items():
    # naive search
    q = client.databases.query(database_id=DB_ID, filter={
        'property':'Name', 'title':{'equals': name}
    })
    results = q.get('results', [])
    if not results:
        print('No page for', name)
        continue
    page = results[0]
    client.pages.update(page_id=page['id'], properties={'base_url': {'url': url}})
    print('Updated', name, url)
