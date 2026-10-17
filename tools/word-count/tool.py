import json

d = json.load(open("input.json"))
print(json.dumps({"words": len(d["text"].split())}))
