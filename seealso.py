import json
from urllib.parse import quote, unquote
import os
import requests


foo = "https%3A%2F%2Fdlcs-ida.org%2Fiiif-img%2F2%2F1%2F3314189a-af97-4a95-91b5-a4ebed6972e4"

bar = unquote(foo)


def find_url(img_resource, search_dir):
    filename = quote(img_resource, safe="")
    filepath = os.path.join(search_dir, filename)
    if os.path.exists(filepath):
        url = (
            f"https://digirati-co-uk.github.io/ida-exported-data/backups/"
            f"ida-starsky-text-meta/{quote(filename, safe='')}"
        )
        r = requests.get(url=url)
        if r.status_code == requests.codes.ok:
            return url
    else:
        print(f"{filepath} does not exist")
    return


def parse_canvas(canvas, text_meta_dir):
    resource = canvas["images"][0]["resource"]["service"]["@id"]
    hocr_url = find_url(resource, text_meta_dir)
    if hocr_url:
        canvas["seeAlso"] = {
            "@id": hocr_url,
            "format": "text/vnd.hocr+html",
            "profile": "http://kba.github.io/hocr-spec/",
        }
    return canvas


def parse_manifest(manifest, text_meta_dir):
    for c in manifest["sequences"][0]["canvases"]:
        c = parse_canvas(c, text_meta_dir=text_meta_dir)
    return manifest


m = requests.get("https://digirati-co-uk.github.io/ida-exported-data/iiif/manifest/idatest01/"
                 "_roll_M-1011_066_cvs-503-524/manifest.json")
if m.status_code == requests.codes.ok:
    _manifest = parse_manifest(m.json(),
                               "/Volumes/MMcG_SSD/Github/ida-exported-data/backups/ida-starsky-text-meta")
    with open("/Volumes/MMcG_SSD/Github/ida-exported-data/iiif/manifest/ocr/"
              "_roll_M-1011_066_cvs-503-524/manifest.json", "w") as f:
        json.dump(_manifest, f, indent=2)
