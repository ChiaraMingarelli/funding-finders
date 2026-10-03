#!/usr/bin/env python3
"""Build the NANOGrav page's embedded data from a dump of the shared catalog.

Usage: python3 export_ng.py <programs_dump_dir> <out.json>
  programs_dump_dir: folder of <doc_id>.json files (ArtifactData list with out_dir).
Rules:
  - include rows whose `aud` list contains "ng" and whose stages include ug, gr, pd or fj
  - apply the row's `ng` overrides (e.g. text rewritten without institution-specific notes);
    an override value of "" removes that field
  - drop internal fields (yale, aud, ng, editedBy, src, checked-by notes)
  - safety: any row that still mentions "Yale" is left out and reported
"""
import json, glob, os, re, sys, datetime

STAGES = {"ug", "gr", "pd", "fj"}
KEEP = ["id", "n", "f", "c", "s", "d", "dt", "a", "e", "u", "unv", "us", "nom", "pt",
        "region", "nfit", "checked", "nofo", "added"]

def main(src, out):
    rows, skipped = [], []
    for fp in sorted(glob.glob(os.path.join(src, "*.json"))):
        x = json.load(open(fp))
        x["id"] = os.path.basename(fp)[:-5]
        aud = x.get("aud")
        if not (isinstance(aud, list) and "ng" in aud):
            continue
        st = [s for s in x.get("stages", []) if s in STAGES]
        if not st:
            continue
        for k, v in (x.get("ng") or {}).items():
            if v == "":
                x.pop(k, None)
            else:
                x[k] = v
        r = {k: x[k] for k in KEEP if k in x and x[k] not in (None, "", [])}
        r["stages"] = st
        if "d" not in r:
            r["d"] = None
        if re.search(r"yale", json.dumps(r), re.I):
            skipped.append(x["id"])
            continue
        rows.append(r)
    data = {"programs": rows,
            "updated": datetime.date.today().isoformat(),
            "skipped_for_yale_mentions": skipped}
    json.dump(data, open(out, "w"), ensure_ascii=False, separators=(",", ":"))
    print(f"{len(rows)} rows exported; skipped (mention Yale): {skipped}")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
