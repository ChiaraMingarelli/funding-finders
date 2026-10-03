#!/usr/bin/env python3
"""Build the Astronomy Funding Finder's embedded data from a dump of the shared catalog.

Usage: python3 export_astro.py <programs_dump_dir> <meta_status.json> <out.json>
Rules:
  - include rows whose `aud` list contains "ast" and whose stages include tt, ten, pd, gr or ug
  - `asub` holds the Yale Astronomy research areas a row belongs to
    (cos, exo, xgal, galac, he, star, ism, inst); rows without asub show under every area
  - keep the Yale internal step (`yale`); drop internal fields (aud, ng, editedBy)
  - the page's "What changed" panel is read from astro_notes.json next to meta_status.json (catalog/meta/)
"""
import json, glob, os, sys, datetime

STAGES = {"tt", "ten", "pd", "gr", "ug"}
DROP = {"aud", "ng", "editedBy", "agency"}

def main(src, status_path, out):
    # The "What changed" panel lives in the catalog as data: catalog/meta/astro_notes.json
    notes = json.load(open(os.path.join(os.path.dirname(status_path), "astro_notes.json"), encoding="utf-8"))
    rows = []
    for fp in sorted(glob.glob(os.path.join(src, "*.json"))):
        x = json.load(open(fp))
        x["id"] = os.path.basename(fp)[:-5]
        aud = x.get("aud")
        if not (isinstance(aud, list) and "ast" in aud):
            continue
        if not STAGES & set(x.get("stages", [])):
            continue
        r = {k: v for k, v in x.items() if k not in DROP}
        r["stages"] = [s for s in x.get("stages", []) if s in STAGES]
        rows.append(r)
    st = json.load(open(status_path)); st = st.get("data", st)
    status = {"lastChecked": st.get("lastChecked") or datetime.date.today().isoformat(),
              "changes": ["New: Astronomy edition, organized by the department's eight research areas"]}
    json.dump({"programs": rows, "status": status, "notes": notes, "updated": datetime.date.today().isoformat()},
              open(out, "w"), ensure_ascii=False, separators=(",", ":"))
    print(f"{len(rows)} Astronomy rows exported")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
