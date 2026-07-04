"""Merge all findings_*.json into findings.json."""
import os, json, glob
OUT = os.path.dirname(os.path.abspath(__file__))
merged = {}
for f in sorted(glob.glob(os.path.join(OUT, "findings_*.json"))):
    key = os.path.basename(f).replace("findings_", "").replace(".json", "")
    merged[key] = json.load(open(f))
with open(os.path.join(OUT, "findings.json"), "w") as f:
    json.dump(merged, f, indent=2)
print("merged keys:", list(merged.keys()))
