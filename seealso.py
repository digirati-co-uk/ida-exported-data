import json
from urllib.parse import quote, unquote
import os
import requests
from collections import defaultdict

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


def extract_metadata(canvas):
    """ """
    annotation_content = defaultdict(list)
    annotation_lists = None
    if canvas.get("otherContent"):
        annotation_lists = [
            o
            for o in canvas["otherContent"]
            if o["label"] == "Named Entity Extraction Annotations"
        ]
    if annotation_lists:
        for anno_list in annotation_lists:
            r = requests.get(anno_list["@id"])
            if r.status_code == requests.codes.ok:
                _annos = r.json()
                for resource in _annos["resources"]:
                    if (annos := resource.get("resource")) is not None:
                        entity_type = None
                        entity_value = None
                        for a in annos:

                            if a.get("@type") == "oa:Tag":
                                if a["chars"].split(":")[0] == "entity":
                                    entity_type = a["chars"].split(":")[1].lower()
                                else:
                                    entity_value = a["chars"]
                        if entity_type and entity_value:
                            annotation_content[entity_type].append(entity_value)
    if annotation_content:
        return annotation_content


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


def simplify_metadata(metadata_dict, filter_keys=("series", "roll", "school", "tribe")):
    metadata_list = [
        {"label": k.title(), "value": list(set([_v.title() for _v in v]))}
        for k, v in metadata_dict.items()
        if k in filter_keys
    ]
    for d in metadata_list:
        if len(d["value"]) == 1:
            d["value"] = d["value"][0]
    return metadata_list


def parse_manifest(manifest, text_meta_dir):
    manifest_metadata = defaultdict(list)
    for i, c in enumerate(manifest["sequences"][0]["canvases"]):
        c = parse_canvas(c, text_meta_dir=text_meta_dir)
        if not c.get("label"):
            c["label"] = f"{i}"
        anno_content = extract_metadata(c)
        if anno_content:
            for k, v in anno_content.items():
                manifest_metadata[k] += v
    manifest["metadata"] = simplify_metadata(manifest_metadata)
    return manifest


if __name__ == "__main__":
    m = requests.get(
        "https://digirati-co-uk.github.io/ida-exported-data/iiif/manifest/idatest01/"
        "_roll_M-1011_066_cvs-503-524/manifest.json"
    )
    if m.status_code == requests.codes.ok:
        _manifest = parse_manifest(
            m.json(),
            "/Volumes/MMcG_SSD/Github/ida-exported-data/backups/ida-starsky-text-meta",
        )
        with open(
            "/Volumes/MMcG_SSD/Github/ida-exported-data/iiif/manifest/ocr/"
            "_roll_M-1011_066_cvs-503-524/manifest.json",
            "w",
        ) as f:
            json.dump(_manifest, f, indent=2)
