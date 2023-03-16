"""
Iterate recursively through the iiif/manifest folder and open each manifest.json file
Iterate the canvases in the manifest sequence
For each canvas, look for the images array
For each image in the images array, if the "on" property does not \
match the "@id" of the canvas change the "on" to match the "@id"
Print on screen the original "on" and the new "on" values
"""
import json
import os
import tqdm
from pathlib import Path
from typing import List, Optional, Tuple


def get_manifests(path: Path) -> List[Path]:
    """
    Return a list of manifest.json files in the path
    """
    return list(path.glob("**/manifest.json"))


def get_canvases(manifest: Path):
    """
    Return a list of canvases
    """
    with open(manifest, "r") as f:
        manifest_json = json.load(f)
    return [canvas for canvas in manifest_json["sequences"][0]["canvases"]], manifest_json


def update_canvas_on(canvas):
    for image in canvas["images"]:
        if image["on"] != canvas["@id"]:
            image["on"] = canvas["@id"]
    return canvas


if __name__ == "__main__":
    manifests = get_manifests(path=Path("./iiif/manifest/"))
    for manifest_path in tqdm.tqdm(manifests):
        canvases, manifest = get_canvases(manifest_path)
        manifest["sequences"][0]["canvases"] = [update_canvas_on(canvas) for canvas in canvases]
        with open(str(manifest_path), "w") as new_f:
            json.dump(manifest, new_f, indent=2, ensure_ascii=False)


