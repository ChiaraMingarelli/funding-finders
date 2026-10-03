#!/usr/bin/env python3
"""Build the Applied Physics Funding Finder's embedded data from a dump of the shared catalog.

Usage: python3 export_ap.py <programs_dump_dir> <meta_status.json> <out.json>
  programs_dump_dir: folder of <doc_id>.json files (ArtifactData list with out_dir).
  meta_status.json: the catalog's meta/status document (its lastChecked is reused).
Rules:
  - include rows whose `aud` list contains "ap" and whose stages include tt, ten, pd, gr or ug
  - keep the Yale internal step (`yale`) because Applied Physics is a Yale department
  - drop internal fields (aud, ng, editedBy)
  - AP_NOTES below holds the page's "What changed" panel; edit it here, never in the page
"""
import json, glob, os, sys, datetime

STAGES = {"tt", "ten", "pd", "gr", "ug"}
DROP = {"aud", "ng", "editedBy", "agency"}

AP_NOTES = {"changes": [
    {"b": "NSF Engineering consolidated its core programs",
     "t": "ECCS (NSF 26-514), CMMI (26-515) and CBET (26-518) now accept proposals anytime, alongside the MPS materials solicitation (26-521)."},
    {"b": "One-proposal limit in DMR",
     "t": "Under NSF 26-521, from Oct 1 each year a person can be PI or co-PI on only one proposal per fiscal year across all eight materials programs."},
    {"b": "DOE Office of Science FY2027 open call",
     "t": "BES materials and chemical-sciences programs and ASCR quantum topics take white papers or pre-applications through the FY2027 call (DE-FOA-0003665); several are due Nov 22 to Nov 30, 2026."},
    {"b": "CHIPS and DARPA",
     "t": "NIST's CHIPS R&D Office paused white-paper intake on Sep 15, 2026 and expects to reopen in November. DARPA's Microsystems Technology Office is now the Multi X Office (MXO), with a new office-wide solicitation."},
    {"b": "Archived or paused NSF programs",
     "t": "FuSe2, ExpandQISE and QuSeC-TAQS are archived; MRSEC, DMREF, ERC and NRT are between competitions. MRI is waiting for a new solicitation."},
    {"b": "NIH",
     "t": "NIH now accepts at most 6 applications per PI per calendar year, and institutes no longer use paylines."},
    {"b": "Budget requests",
     "t": "The President's FY2027 request cuts NSF by 55% and the DOE Office of Science by 13%. Appropriations are still pending."},
]}

def main(src, status_path, out):
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
              "changes": ["New: Applied Physics edition covering quantum information, photonics and quantum materials"]}
    data = {"programs": rows, "status": status, "notes": AP_NOTES,
            "updated": datetime.date.today().isoformat()}
    json.dump(data, open(out, "w"), ensure_ascii=False, separators=(",", ":"))
    print(f"{len(rows)} Applied Physics rows exported")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
