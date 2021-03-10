import glob
import json
import os

root_dir = os.path.join(".", "")

regions = {}
ids = []
notids = []

for filename in glob.iglob(root_dir + "**/*.json", recursive=True):
    if "schema" not in filename and "caves" not in filename:
        with(open(filename)) as json_file:
            data = json.load(json_file)
            region = filename.replace(os.path.join(".","regions",""),"")
            region = region.replace(".json","")
            if "rooms" in data:
                for room in data["rooms"]:
                    if "id" in room:
                        ids.append(room["id"])
            regions[region] = data
ids.sort()
for i in range(1,ids[len(ids) - 1]):
    if i not in ids:
        notids.append(i)
print(notids)
