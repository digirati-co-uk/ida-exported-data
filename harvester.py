import requests
import json
from prezi_upgrader import Upgrader
import os
from pathlib import Path
import base64
from urllib.parse import unquote, urlparse, parse_qs
import glob
from elucidate import oa_from_id

upgrader = Upgrader(flags={"default_lang": "en"})


def fetch(
    at_id,
    path_base="/Volumes/MMcG_SSD/Github/ida-exported-data",
    rewrite_id=True,
    upgrade=True,
):
    r = requests.get(at_id, headers={"accept": "application/json"})
    iiif = None
    iiif_resource = None
    if r.status_code == requests.codes.ok:
        iiif_resource = r.json()
    if iiif_resource:
        if upgrade:
            if (
                iiif_resource.get("@context")
                == "http://iiif.io/api/presentation/2/context.json"
            ):
                iiif = upgrader.process_resource(iiif_resource, top=True)
                iiif["@context"] = "http://iiif.io/api/presentation/3/context.json"
            elif (
                iiif_resource.get("@context")
                == "http://iiif.io/api/presentation/3/context.json"
            ):
                iiif = iiif_resource
        else:
            iiif = iiif_resource
    if iiif and upgrade:
        if iiif["id"].startswith("https://manifests.dlcs-ida.org/"):
            _type = iiif["type"].lower()
            new_id = (
                iiif["id"].replace(
                    "https://manifests.dlcs-ida.org/",
                    f"https://digirati-co-uk.github.io/ida-exported-data/iiif/iiif3/{_type}/",
                )
                + f"{_type}.json"
            )
            iiif["id"] = new_id
            filepath = os.path.join(path_base, "/".join(new_id.split("/")[4:]))
            _dir = os.path.dirname(filepath)
            Path(_dir).mkdir(parents=True, exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(iiif, f, indent=2, ensure_ascii=False)
        elif iiif["id"].startswith("https://presley.dlcs-ida.org/"):
            _type = iiif["type"].lower()
            new_id = (
                (
                    iiif["id"].replace(
                        "https://presley.dlcs-ida.org/",
                        f"https://digirati-co-uk.github.io/ida-exported-data/iiif/iiif3/{_type}/",
                    )
                    + f"{_type}.json"
                )
                .replace("manifestmanifest", "manifest")
                .replace("/iiif/iiif3/manifest/iiif/", "/iiif/iiif3/manifest/")
            )
            iiif["id"] = new_id
            print(new_id)
            print(new_id.split("/"))
            filepath = os.path.join(
                path_base, "iiif/iiif3/manifest/", "/".join(new_id.split("/")[7:])
            )
            print(filepath)
            _dir = os.path.dirname(filepath)
            Path(_dir).mkdir(parents=True, exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(iiif, f, indent=2, ensure_ascii=False)
    elif iiif and not upgrade:
        if iiif["@id"].startswith("https://manifests.dlcs-ida.org/"):
            _type = iiif["@type"].lower().replace("sc:", "")
            new_id = (
                iiif["@id"].replace(
                    "https://manifests.dlcs-ida.org/",
                    f"https://digirati-co-uk.github.io/ida-exported-data/iiif/{_type}/",
                )
                + f"{_type}.json"
            )
            iiif["@id"] = new_id
            filepath = os.path.join(path_base, "/".join(new_id.split("/")[4:]))
            print(filepath)
            _dir = os.path.dirname(filepath)
            Path(_dir).mkdir(parents=True, exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(iiif, f, indent=2, ensure_ascii=False)
        elif iiif["@id"].startswith("https://presley.dlcs-ida.org/"):
            _type = iiif["@type"].lower().replace("sc:", "")
            new_id = (
                (
                    iiif["@id"].replace(
                        "https://presley.dlcs-ida.org/",
                        f"https://digirati-co-uk.github.io/ida-exported-data/iiif/{_type}/",
                    )
                    + f"{_type}.json"
                )
                .replace("manifestmanifest", "manifest")
                .replace("/iiif/manifest/iiif/", "/iiif/manifest/")
            )
            iiif["@id"] = new_id
            print(new_id.split("/"))
            filepath = os.path.join(
                path_base, "iiif/manifest/idatest01", "/".join(new_id.split("/")[7:])
            )
            print(filepath)
            _dir = os.path.dirname(filepath)
            Path(_dir).mkdir(parents=True, exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(iiif, f, indent=2, ensure_ascii=False)


def fetch_annos(c, manifest_id, iiif3=False, path_base="/Volumes/MMcG_SSD/Github/ida-exported-data"):
    if not iiif3:
        anno_list = c.get("otherContent")
        if anno_list:
            for anno in anno_list:
                if anno["@id"].startswith(
                    "https://transcriptions.dlcs-ida.org/annotations/"
                ):
                    r = requests.get(anno["@id"])
                    if r.status_code == requests.codes.ok:
                        j = r.json()
                    else:
                        j = None
                        print(f"{r.status_code}: {r.url}")
                    if j:
                        partial_base = str(anno["@id"].replace(
                                "https://transcriptions.dlcs-ida.org/annotations/", ""
                            ))
                        qs = parse_qs(unquote(partial_base.split("/")[-1]))
                        if (image := qs.get("image", [])[0]) is not None:
                            image_uuid = image.split("/")[-1]
                            anno_id = f"https://digirati-co-uk.github.io/ida-exported-data/iiif/annotations/{manifest_id}" \
                                      f"/ocr_{image_uuid}/annotations.json"
                            filepath = os.path.join(
                                path_base,
                                f"iiif/annotations/{manifest_id}",
                                f"ocr_{image_uuid}/annotations.json"
                            )
                            _dir = os.path.dirname(filepath)
                            Path(_dir).mkdir(parents=True, exist_ok=True)
                            j["@id"] = anno_id
                            anno["@id"] = anno_id
                            with open(filepath, "w", encoding="utf-8") as f:
                                print(filepath)
                                json.dump(j, f, indent=2, ensure_ascii=False)
                        else:
                            print("Erk")
                elif anno["@id"].startswith(
                        "https://annotations.dlcs-ida.org/annotationlist/"
                ):
                    filepath = os.path.join(
                        path_base,
                        f"iiif/annotations/{manifest_id}",
                        anno["@id"].replace(
                            "https://annotations.dlcs-ida.org/annotationlist/", ""
                        ),
                        "annotations.json"
                    )
                    _dir = os.path.dirname(filepath)
                    Path(_dir).mkdir(parents=True, exist_ok=True)
                    anno_url_base = str(anno["@id"].replace(
                        "https://annotations.dlcs-ida.org/annotationlist/", ""
                    )) + "annotations.json"
                    anno_id = f"https://digirati-co-uk.github.io/ida-exported-data/iiif/annotations/{manifest_id}/" \
                              f"{anno_url_base}"
                    oa_content = oa_from_id(identifier=anno["@id"].split("/")[-2], request_uri=anno_id)
                    anno["@id"] = anno_id
                    print(f"OA: {filepath} : {anno_id}")
                    with open(filepath, "w", encoding="utf-8") as f:
                        json.dump(oa_content, f, indent=2, ensure_ascii=False)
        return c


def harvest_annotations(manifest_filepath, iiif3=False):
    with open(manifest_filepath, "r") as f:
        manifest = json.load(f)
    if not iiif3:
        manifest_id = manifest["@id"]
        canvases = manifest["sequences"][0]["canvases"]
        new_canvases = [fetch_annos(canvas, manifest_id="".join(manifest_id.split("/")[-2:-1]), iiif3=iiif3) for canvas
                        in canvases]
        manifest["sequences"][0]["canvases"] = new_canvases
        with open(manifest_filepath, "w") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
    else:
        pass
        # manifest_id = manifest["id"]
        # canvases = [c for c in manifest["items"] if c.get("type").lower() == "canvas"]


def fetch_all_annos():
    manifests = glob.glob("/Volumes/MMcG_SSD/Github/ida-exported-data/iiif/manifest/idatest01/*/manifest.json")
    for manifest_f in manifests:
        print(manifest_f)
        harvest_annotations(manifest_f, False)


def fetch_all_manifests(collections=("./iiif/collection/rollcollection.json", "./iiif/collection/top.json")):
    for collpath in collections:
        with open(collpath, "r") as coll_file:
            coll = json.load(coll_file)
            for manifest in coll["members"]:
                manifest_id = manifest["@id"]
                print(manifest_id)
                fetch(at_id=manifest_id, upgrade=False)


# fetch_all_manifests(collections=("./iiif/collection/top.json",))
fetch_all_annos()
