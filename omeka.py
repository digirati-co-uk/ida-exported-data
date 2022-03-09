import requests
import json

def fetch_paginated_results(query_string, endpoint="items", resource_type="item", omeka="https://omeka.dlcs-ida.org/api"):
    item_list = []
    initial_request = f"{omeka}/{endpoint}?search={query_string}&resource-type={resource_type}"
    r = requests.get(initial_request, headers={"Accept": "application/json"})
    if r.status_code == requests.codes.ok:
        links = r.links
        item_list += [x["dcterms:identifier"][0]["@value"] for x in r.json() if x.get("dcterms:identifier")]
        while links.get("next"):
            print(len(item_list))
            print(links["next"]["url"])
            n = requests.get(links["next"]["url"])
            if n.status_code == requests.codes.ok:
                links = n.links
                item_list += [x["dcterms:identifier"][0]["@value"] for x in n.json() if x.get("dcterms:identifier")]
    return item_list


def update_top(top_file="./iiif/collection/top.json", item_file="./iiif/collection/items.json"):
    top = json.load(open(top_file, "r"))
    items = json.load(open(item_file, "r"))
    top_ids = [x["@id"] for x in top["members"]]
    new_top_ids = [x for x in items if x not in top_ids]
    for i in new_top_ids:
        print(i)
        r = requests.get(i)
        if r.status_code == requests.codes.ok:
            j = r.json()
            d = {"@id": i, "@type": "sc:Manifest"}
            if j.get("label"):
                d["label"] = j["label"]
            elif j.get("metadata"):
                titles = [x["value"] for x in j["metadata"] if x["label"] == "Title"]
                if titles:
                    print(titles)
                    d["label"] = titles[0]
            top["members"].append(d)
    with open("./iiif/collection/newtop.json", "w") as f:
        json.dump(top, f, indent=2, ensure_ascii=False)



update_top()
# with open("./iiif/collection/items.json", "w") as f:
#     items = fetch_paginated_results(query_string="sc:manifest")
#     json.dump(items, f)
