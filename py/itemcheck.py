import glob
import json
import os

from collections import OrderedDict

root_dir = os.path.join(".", "")

ids = {"rooms":{}}

itemsDB = {}
with(open(os.path.join(".","items.json"))) as json_file:
    data = json.load(json_file)
    for cat,items in data.items():
        if isinstance(items,dict):
            for item,iData in items.items():
                if "data" in iData:
                    itemsDB[item] = iData["data"]
# print(itemsDB)

for filename in glob.iglob(root_dir + "**/regions.json", recursive=True):
    if "schema" not in filename and "caves" not in filename:
        with(open(filename)) as json_file:
            data = json.load(json_file)
            region = filename.replace(os.path.join(".","regions",""),"")
            region = region.replace(".json","")
            if "rooms" in data:
                for room in data["rooms"]:
                    if room["id"] not in [67]: # Capacity Upgrade
                        if "Shop" not in room["name"]:
                            if "nodes" in room:
                                for node in room["nodes"]:
                                    if node["nodeType"] == "item":
                                        record = False
                                        nodeItemCode = False
                                        nodeAddress = False
                                        if "nodeItem" not in node:
                                            record = True
                                        elif node["nodeItem"] == "Item Name":
                                            record = True
                                        if "nodeItemCode" not in node:
                                            record = True
                                            nodeItemCode = True
                                        elif node["nodeItemCode"] == "Item Code":
                                            record = True
                                            nodeItemCode = True
                                        if "nodeAddress" not in node:
                                            record = True
                                            nodeAddress = True
                                        elif node["nodeAddress"] == "":
                                            record = True
                                            nodeAddress = True
                                        if record:
                                            if str(room["id"]) not in ids["rooms"]:
                                                ids["rooms"][str(room["id"])] = {}
                                            if "node" not in ids["rooms"][str(room["id"])]:
                                                ids["rooms"][str(room["id"])] = {"node":[]}
                                            nData = {}
                                            nData["id"] = str(node["id"])
                                            if "name" in node:
                                                nData["name"] = room["name"] + ':' + node["name"]
                                            if nodeItemCode:
                                                if node["nodeItem"] in itemsDB:
                                                    nData["nodeItemCode"] = itemsDB[node["nodeItem"]]
                                                else:
                                                    nData["nodeItem"] = "Missing"
                                            if nodeAddress:
                                                nData["nodeAddress"] = "Missing"
                                            ids["rooms"][str(room["id"])]["node"].append(nData)
ids2 = OrderedDict(sorted(ids["rooms"].items()))
print(json.dumps(ids2,indent=2))
