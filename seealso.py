import json
from urllib.parse import quote, unquote
import os

foo = "https%3A%2F%2Fdlcs-ida.org%2Fiiif-img%2F2%2F1%2F3314189a-af97-4a95-91b5-a4ebed6972e4"

bar = unquote(foo)

def find_file(img_resource, search_dir):
    filename = quote(img_resource, safe='')
    filepath = os.path.join(search_dir, filename)
    print(filepath)
    if os.path.exists(filepath):
        return filepath


print(find_file(bar, "/Volumes/MMcG_SSD/Github/ida-exported-data/backups/ida-starsky-text-meta"))



