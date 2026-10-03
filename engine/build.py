#!/usr/bin/env python3
"""Build every funding-finder page from the catalog in this repository.

Inputs (the source of truth):
  catalog/programs/<id>.json      one program per file
  catalog/meta/status.json        lastChecked date and the "What's new" strings (Physics page)
  catalog/meta/notes.json         Physics page tips by career stage, plus its "What changed" list
  catalog/meta/ap_notes.json      Applied Physics "What changed" panel
  catalog/meta/astro_notes.json   Astronomy "What changed" panel
  templates/<page>.html           page layouts; {{snapshot}} marks the data, {{link:<page>}} the cross-links
  engine/export_ap.py, export_astro.py, export_ng.py   choose and shape each page's rows

Outputs:
  docs/<page>.html                the combined site (cross-links stay inside docs/)
  docs/version.json               the catalog commit the pages were built from
  sites/<repo>/...                what each single-page repo copies in (see sites/<repo>/MANIFEST)
  data/programs.json              the whole catalog as one list

Usage: python3 engine/build.py [--check]
--check validates the catalog and builds in a temporary folder without writing anything.
"""
import datetime, glob, json, os, re, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = {  # key: (template/doc name, single-page repo, export script)
    "physics": ("physics.html", "yale-physics-funding-finder", None),
    "ap": ("applied-physics.html", "yale-applied-physics-funding-finder", "export_ap.py"),
    "astro": ("astronomy.html", "yale-astronomy-funding-finder", "export_astro.py"),
    "ng": ("nanograv.html", "nanohertz-opportunities", "export_ng.py"),
}
SITE_ENGINE = {  # engine files each single-page repo carries, for readers of that repo
    "physics": ["export_mod.js"],
    "ap": ["export_mod.js", "export_ap.py"],
    "astro": ["export_mod.js", "export_astro.py", "astro_classify.py"],
    "ng": ["export_mod.js", "export_ng.py"],
}
PAGES_URL = "https://chiaramingarelli.github.io/{repo}/"
FIELDS = {"id", "n", "f", "c", "s", "d", "dt", "a", "e", "u", "fields", "stages", "pt", "src", "unv",
          "nofo", "yale", "us", "nom", "checked", "added", "aud", "asub", "region", "nfit", "ng"}
STATUS = {"open", "rolling", "watch", "closed"}
AUD = {"yale", "ng", "radar", "ap", "ast"}
STAGES = {"ug", "gr", "pd", "fj", "tt", "ten"}
META = ("status", "notes", "ap_notes", "astro_notes")
ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")
SHRINK_LIMIT = 0.7  # refuse a catalog with fewer than 70% of the rows of the last build


def load(path):
    def no_nan(c):
        raise ValueError(f"{c} is not valid JSON")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh, parse_constant=no_nan)


def dump(obj):
    return json.dumps(obj, ensure_ascii=False, indent=1) + "\n"


def is_date(v):
    try:
        return isinstance(v, str) and bool(ISO.match(v)) and bool(datetime.date.fromisoformat(v))
    except ValueError:
        return False


def str_list(v, allowed=None):
    return isinstance(v, list) and all(isinstance(x, str) and (allowed is None or x in allowed) for x in v)


def check_row(x, where):
    p = []
    if not isinstance(x.get("n"), str) or not x["n"].strip():
        p.append("missing name (n)")
    if x.get("s") not in STATUS:
        p.append(f"status (s) must be one of {sorted(STATUS)}")
    if not str_list(x.get("stages"), STAGES) or not x["stages"]:
        p.append(f"stages must be a non-empty list of {sorted(STAGES)}")
    if "aud" in x and not str_list(x["aud"], AUD):
        p.append(f"aud must be a list of {sorted(AUD)} (leave it out for Yale-only rows)")
    for k in ("fields", "asub"):
        if k in x and not str_list(x[k]):
            p.append(f"{k} must be a list of strings")
    if x.get("d") is not None and not is_date(x["d"]):
        p.append("deadline (d) must be a real YYYY-MM-DD date or null")
    for k in ("added", "checked"):
        if k in x and not is_date(x[k]):
            p.append(f"{k} must be a real YYYY-MM-DD date")
    for k in ("ng", "yale"):
        if k in x and not isinstance(x[k], dict):
            p.append(f"{k} must be an object")
    if isinstance(x.get("yale"), dict) and x["yale"].get("d") is not None and not is_date(x["yale"]["d"]):
        p.append("yale.d must be a real YYYY-MM-DD date or null")
    for k in ("us", "nom"):
        if k in x and not isinstance(x[k], bool):
            p.append(f"{k} must be true or false")
    extra = set(x) - FIELDS
    if extra:
        p.append(f"unknown fields {sorted(extra)}")
    return [f"{where}: {m}" for m in p]


def check_catalog():
    """Return (rows, problems). Problems stop the build; nothing is guessed or repaired."""
    rows, problems = [], []
    for fp in sorted(glob.glob(os.path.join(ROOT, "catalog", "programs", "*.json"))):
        pid = os.path.basename(fp)[:-5]
        where = f"catalog/programs/{pid}.json"
        if not SLUG.match(pid):
            problems.append(f"{where}: file name must be a lowercase slug")
        try:
            x = load(fp)
        except ValueError as e:
            problems.append(f"{where}: not valid JSON ({e})")
            continue
        if not isinstance(x, dict):
            problems.append(f"{where}: must hold one JSON object")
            continue
        if x.get("id", pid) != pid:
            problems.append(f"{where}: id {x.get('id')!r} does not match the file name")
        problems += check_row(x, where)
        x["id"] = pid
        rows.append(dict(sorted(x.items())))
    for name in META:
        where = f"catalog/meta/{name}.json"
        try:
            m = load(os.path.join(ROOT, "catalog", "meta", f"{name}.json"))
        except (OSError, ValueError) as e:
            problems.append(f"{where}: {e}")
            continue
        if not isinstance(m, dict):
            problems.append(f"{where}: must hold one JSON object")
        elif name in ("ap_notes", "astro_notes", "notes") and "changes" in m and not (
                isinstance(m["changes"], list) and all(isinstance(c, dict) and isinstance(c.get("b"), str)
                                                       and isinstance(c.get("t"), str) for c in m["changes"])):
            problems.append(f"{where}: changes must be a list of {{\"b\": text, \"t\": text}}")
    if not rows:
        problems.append("catalog/programs is empty")
    prev = os.path.join(ROOT, "data", "programs.json")
    if os.path.exists(prev) and os.environ.get("ALLOW_SHRINK") != "1":
        before = len(load(prev))
        if before and len(rows) < SHRINK_LIMIT * before:
            problems.append(f"catalog shrank from {before} to {len(rows)} rows; "
                            "set ALLOW_SHRINK=1 if that is intended")
    return rows, problems


def snapshot(key, script, rows):
    """The data block for one page, made the same way the routines used to make it."""
    meta = lambda name: load(os.path.join(ROOT, "catalog", "meta", f"{name}.json"))
    if key == "physics":
        return {"programs": [r for r in rows if "aud" not in r or "yale" in r["aud"]],
                "status": meta("status"), "notes": meta("notes")}
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "out.json")
        src = os.path.join(ROOT, "catalog", "programs")
        args = [src, out] if key == "ng" else [src, os.path.join(ROOT, "catalog", "meta", "status.json"), out]
        res = subprocess.run([sys.executable, os.path.join(ROOT, "engine", script), *args],
                             capture_output=True, text=True)
        if res.returncode:
            print(f"{script} failed:\n{res.stdout}{res.stderr}")
            sys.exit(1)
        snap = load(out)
    if key == "ng" and snap.get("skipped_for_yale_mentions"):
        print("ng: left out for mentioning Yale (add an ng override):", ", ".join(snap["skipped_for_yale_mentions"]))
    for k in ("skipped_for_yale_mentions",) if key == "ng" else ("updated",):
        snap.pop(k, None)
    return snap


def render(template, snap, link):
    if template.count("{{snapshot}}") != 1:
        raise ValueError("template must contain exactly one {{snapshot}}")
    out = re.sub(r"\{\{link:(\w+)\}\}", lambda m: link(m.group(1)), template)
    if "{{" in out.replace("{{snapshot}}", ""):
        raise ValueError("unreplaced placeholder in template")
    # Escape <, > and & so no catalog text can end the <script> block early.
    text = json.dumps(snap, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    text = text.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return out.replace("{{snapshot}}", text, 1)


def source_commit():
    res = subprocess.run(["git", "-C", ROOT, "log", "-1", "--format=%H", "--", "catalog", "templates", "engine"],
                         capture_output=True, text=True)
    return res.stdout.strip() or "unknown"


def write(path, text, changed, root):
    old = open(path, encoding="utf-8").read() if os.path.exists(path) else None
    if old != text:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        changed.append(os.path.relpath(path, root))


def build(out_root):
    rows, problems = check_catalog()
    if problems:
        print("Catalog problems:\n  " + "\n  ".join(problems))
        sys.exit(1)
    changed, counts = [], {}
    put = lambda path, text: write(path, text, changed, out_root)
    version = dump({"source": source_commit()})
    for key, (doc, repo, script) in PAGES.items():
        snap = snapshot(key, script, rows)
        progs = snap["programs"]
        if not progs or len({p["id"] for p in progs}) != len(progs):
            print(f"{key}: no rows or duplicate ids")
            sys.exit(1)
        counts[key] = len(progs)
        template = open(os.path.join(ROOT, "templates", doc), encoding="utf-8").read()
        put(os.path.join(out_root, "docs", doc), render(template, snap, lambda k: PAGES[k][0]))
        site = os.path.join(out_root, "sites", repo)
        put(os.path.join(site, "index.html"), render(template, snap, lambda k: PAGES_URL.format(repo=PAGES[k][1])))
        put(os.path.join(site, "data", "programs.json"), dump(progs))
        put(os.path.join(site, "version.json"), version)
        files = ["index.html", "data/programs.json", "version.json"]
        for f in SITE_ENGINE[key]:
            put(os.path.join(site, "engine", f), open(os.path.join(ROOT, "engine", f), encoding="utf-8").read())
            files.append(f"engine/{f}")
        put(os.path.join(site, "MANIFEST"), "\n".join(files) + "\n")
    put(os.path.join(out_root, "docs", "version.json"), version)
    put(os.path.join(out_root, "data", "programs.json"), dump(rows))
    readme = os.path.join(ROOT, "README.md")
    if os.path.exists(readme):
        txt = open(readme, encoding="utf-8").read()
        put(os.path.join(out_root, "README.md"),
            re.sub(r"catalog of about \d+ programs", f"catalog of about {round(len(rows), -1)} programs", txt))
    print(f"catalog: {len(rows)} programs; " + ", ".join(f"{k} {n}" for k, n in counts.items()))
    print("changed:", *changed, sep="\n  ") if changed else print("no changes")


def main():
    if "--check" in sys.argv[1:]:
        with tempfile.TemporaryDirectory() as tmp:
            build(tmp)
        print("check passed")
    else:
        build(ROOT)


if __name__ == "__main__":
    main()
