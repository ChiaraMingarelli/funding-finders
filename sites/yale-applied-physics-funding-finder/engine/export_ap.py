#!/usr/bin/env python3
"""Build the Applied Physics Funding Finder's embedded data from a dump of the shared catalog.

Usage: python3 export_ap.py <programs_dump_dir> <meta_status.json> <out.json>
  programs_dump_dir: folder of <doc_id>.json files (ArtifactData list with out_dir).
  meta_status.json: the catalog's meta/status document (its lastChecked is reused).
Rules:
  - include rows whose `aud` list contains "ap" and whose stages include tt, ten, pd, gr or ug
  - keep the Yale internal step (`yale`) because Applied Physics is a Yale department
  - drop internal fields (aud, ng, editedBy)
  - the page's "What changed" panel is read from ap_notes.json next to meta_status.json (catalog/meta/)
"""
import json, glob, os, sys, datetime

STAGES = {"tt", "ten", "pd", "gr", "ug"}
DROP = {"aud", "ng", "editedBy", "agency"}

def main(src, status_path, out):
    # The "What changed" panel lives in the catalog as data: catalog/meta/ap_notes.json
    notes = json.load(open(os.path.join(os.path.dirname(status_path), "ap_notes.json"), encoding="utf-8"))
    rows = []
    for fp in sorted(glob.glob(os.path.join(src, "*.json"))):
        x = json.load(open(fp))
        x["id"] = os.path.basename(fp)[:-5]
        aud = x.get("aud")
        if not (isinstance(aud, list) and "ap" in aud):
            continue
        if not STAGES & set(x.get("stages", [])):
            continue
        r = {k: v for k, v in x.items() if k not in DROP}
        r["stages"] = [s for s in x.get("stages", []) if s in STAGES]
        rows.append(r)
    st = json.load(open(status_path))
    st = st.get("data", st)
    status = {"lastChecked": st.get("lastChecked") or datetime.date.today().isoformat(),
              "changes": []}
    data = {"programs": rows, "status": status, "notes": notes,
            "updated": datetime.date.today().isoformat()}
    json.dump(data, open(out, "w"), ensure_ascii=False, separators=(",", ":"))
    print(f"{len(rows)} Applied Physics rows exported")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
