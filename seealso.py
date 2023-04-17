import json
from urllib.parse import quote, unquote
import os
import requests
from collections import defaultdict
import glob
from lxml import html
import re
from pathlib import Path
import random


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
            return url, filepath
    return None, None


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
                        if isinstance(annos, list):
                            for a in annos:
                                try:
                                    if a.get("@type") == "oa:Tag":
                                        if a["chars"].split(":")[0] == "entity":
                                            entity_type = (
                                                a["chars"].split(":")[1].lower()
                                            )
                                        else:
                                            entity_value = a["chars"]
                                except AttributeError:
                                    pass
                            if entity_type and entity_value:
                                annotation_content[entity_type].append(entity_value)
    if annotation_content:
        return annotation_content


def parse_canvas(canvas, text_meta_dir):
    see_alsos = []
    hocr_url = None
    hocr_path = None
    resource = canvas["images"][0]["resource"]["service"]["@id"]
    if resource:
        try:
            hocr_url, hocr_path = find_url(resource, text_meta_dir)
        except TypeError:
            print(resource)
        if hocr_path:
            doc = html.parse(hocr_path)
            lines = [
                re.sub(r"\s+", "\x20", line.text_content()).strip()
                for line in doc.xpath("//*[@class='ocr_line']")
            ]
            plain_path = os.path.join(
                "/Users/matt.mcgrattan/code/ida-exported-data/backups",
                hocr_path.replace(text_meta_dir, "plaintext") + ".txt",
            )
            if lines and plain_path:
                see_alsos.append(
                    {
                        "@id": hocr_url.replace(
                            "/ida-starsky-text-meta/", "/plaintext/"
                        )
                        + ".txt",
                        "format": "text/plain",
                    }
                )
            with open(plain_path, "w", encoding="utf-8") as pf:
                pf.writelines(lines)
        if hocr_url:
            see_alsos.append(
                {
                    "@id": hocr_url,
                    "format": "text/vnd.hocr+html",
                    "profile": "http://kba.github.io/hocr-spec/",
                }
            )
        if see_alsos:
            canvas["seeAlso"] = see_alsos
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


def parse_manifest(manifest, text_meta_dir, base_dir=os.getcwd(), num=1):
    manifest_metadata = defaultdict(list)
    for i, c in enumerate(manifest["sequences"][0]["canvases"]):
        c = parse_canvas(c, text_meta_dir=text_meta_dir)
        if not c.get("label"):
            c["label"] = f"{i}"
        anno_content = extract_metadata(c)
        if anno_content:
            for k, v in anno_content.items():
                manifest_metadata[k] += v
    if new_metadata := simplify_metadata(manifest_metadata):
        manifest["metadata"] = new_metadata
    if manifest.get("service"):
        del manifest["service"]
    manifest["@id"] = manifest["@id"].replace("idatest01", f"ocr{num}")
    filepath = manifest["@id"].replace(
        "https://digirati-co-uk.github.io/ida-exported-data", base_dir
    )
    return manifest, filepath


def iterate_dir(manifest_dir, limit=40, dry_run=True, rnd=True, num=1):
    files = glob.glob(manifest_dir + "/**/manifest.json", recursive=True)
    if rnd:
        file_choices = random.choices(files, k=limit)
    else:
        file_choices = files[0:limit]
    for file in file_choices:
        manifest = json.load(open(file))
        _manifest, filepath = parse_manifest(
            manifest=manifest,
            text_meta_dir="/Users/matt.mcgrattan/code/ida-exported-data/"
            "backups/ida-starsky-text-meta",
            num=num
        )
        if not dry_run and _manifest.get("metadata"):
            manifest_dir = os.path.dirname(filepath)
            Path(manifest_dir).mkdir(parents=True, exist_ok=True)
            with open(filepath, "w") as manf:
                json.dump(_manifest, manf, ensure_ascii=False, indent=2)
                print(_manifest["@id"])
        else:
            print("No manifest metadata")
    return files


def make_collection(num=1):
    manifests = glob.glob(
        f"/Users/matt.mcgrattan/code/ida-exported-data/iiif/manifest/ocr{num}/**/manifest.json"
    )
    collection = {
        "@id": f"https://digirati-co-uk.github.io/ida-exported-data/iiif/collection/qa{num}.json",
        "@context": "http://iiif.io/api/presentation/2/context.json",
        "label": f"Madoc QA Collection {num}",
        "@type": "sc:Collection",
        "members": [],
    }
    for manifest in manifests:
        with open(manifest, "r") as f:
            m = json.load(f)
            if m.get("label"):
                collection["members"].append(
                    {"@id": m["@id"], "label": m["label"], "@type": "sc:Manifest"}
                )
    with open(
        f"/Users/matt.mcgrattan/code/ida-exported-data/iiif/collection/qa{num}.json",
        "w",
    ) as c:
        json.dump(collection, c, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    for n in range(6, 10):
        f = iterate_dir(
            "/Users/matt.mcgrattan/code/ida-exported-data/iiif/manifest/idatest01",
            limit=40,
            dry_run=False,
            num=n
        )
        make_collection(num=n)
    # m = requests.get(
    #     "https://digirati-co-uk.github.io/ida-exported-data/iiif/manifest/idatest01/"
    #     "_roll_M-1011_066_cvs-503-524/manifest.json"
    # )
    # if m.status_code == requests.codes.ok:
    #     _manifest, _base = parse_manifest(
    #         m.json(),
    #         "/Volumes/MMcG_SSD/Github/ida-exported-data/backups/ida-starsky-text-meta",
    #     )
    #     print(_base)
    #     with open(
    #         "/Volumes/MMcG_SSD/Github/ida-exported-data/iiif/manifest/ocr/"
    #         "_roll_M-1011_066_cvs-503-524/manifest.json",
    #         "w",
    #     ) as f:
    #         json.dump(_manifest, f, indent=2)
