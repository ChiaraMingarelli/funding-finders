#!/usr/bin/env python3
"""Build the Astronomy Funding Finder's embedded data from a dump of the shared catalog.

Usage: python3 export_astro.py <programs_dump_dir> <meta_status.json> <out.json>
Rules:
  - include rows whose `aud` list contains "ast" and whose stages include tt, ten, pd, gr or ug
  - `asub` holds the Yale Astronomy research areas a row belongs to
    (cos, exo, xgal, galac, he, star, ism, inst); rows without asub show under every area
  - keep the Yale internal step (`yale`); drop internal fields (aud, ng, editedBy)
  - ASTRO_NOTES below holds the page's "What changed" panel; edit it here, never in the page
"""
import json, glob, os, sys, datetime

STAGES = {"tt", "ten", "pd", "gr", "ug"}
DROP = {"aud", "ng", "editedBy", "agency"}
ASTRO_NOTES = {"changes": [
    {"b": "NSF consolidated its astronomy programs",
     "t": "AAG is now Astro-Core under NSF 26-522 (posted Aug 17, 2026). Proposals are accepted anytime, with a program target date in mid-November; FY2027 is flagged as especially competitive."},
    {"b": "NASA ROSES-26 still unreleased",
     "t": "ATP, ADAP, FINESST and the guest-investigator programs are waiting on it. LISA Preparatory Science was not solicited in ROSES-24 or ROSES-25."},
    {"b": "Archived or paused NSF programs",
     "t": "WoU-MMA, MPS-Ascend and Mid-scale RI-2 are archived. MRI is waiting for a new solicitation."},
    {"b": "Observing time",
     "t": "Chandra Cycle 29 and the NRAO/GBO calls are tracked under Instrumentation & observing; Yale's own Keck and Palomar time goes through the Yale Time Allocation Committee."},
    {"b": "Budget requests",
     "t": "The President's FY2027 request cuts NSF by 55% and NASA Astrophysics research and analysis from $113.7M to $46.6M. Appropriations are still pending."},
]}

def main(src, status_path, out):
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
    json.dump({"programs": rows, "status": status, "notes": ASTRO_NOTES, "updated": datetime.date.today().isoformat()},
              open(out, "w"), ensure_ascii=False, separators=(",", ":"))
    print(f"{len(rows)} Astronomy rows exported")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
