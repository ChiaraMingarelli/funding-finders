#!/usr/bin/env python3
"""Build every funding-finder page from the catalog in this repository.

Inputs (the source of truth):
  catalog/programs/<id>.json   one program per file
  catalog/meta/status.json     lastChecked date and the "What's new" strings (Physics page)
  catalog/meta/notes.json      Physics page tips by career stage, plus its "What changed" list
  templates/<page>.html        page layouts; {{snapshot}} marks the data, {{link:<page>}} the cross-links
  engine/export_ap.py, export_astro.py, export_ng.py   choose and shape each page's rows

Outputs:
  docs/<page>.html             the combined site (cross-links stay inside docs/)
  sites/<repo>/...             what each single-page repo copies in (see sites/<repo>/MANIFEST)
  data/programs.json           the whole catalog as one list

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
ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")
SHRINK_LIMIT = 0.7  # refuse a catalog with fewer than 70% of the rows of the last build


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def dump(obj):
    return json.dumps(obj, ensure_ascii=False, indent=1) + "\n"


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
        if not isinstance(x.get("n"), str) or not x["n"].strip():
            problems.append(f"{where}: missing name (n)")
        if x.get("s") not in STATUS:
            problems.append(f"{where}: status (s) must be one of {sorted(STATUS)}")
        if not isinstance(x.get("stages"), list) or not x["stages"]:
            problems.append(f"{where}: stages must be a non-empty list")
        if x.get("d") is not None and not (isinstance(x["d"], str) and ISO.match(x["d"])):
            problems.append(f"{where}: deadline (d) must be YYYY-MM-DD or null")
        for k in ("added", "checked"):
            if k in x and not (isinstance(x[k], str) and ISO.match(x[k])):
                problems.append(f"{where}: {k} must be YYYY-MM-DD")
        extra = set(x) - FIELDS
        if extra:
            problems.append(f"{where}: unknown fields {sorted(extra)}")
        x["id"] = pid
        rows.append(dict(sorted(x.items())))
    for name in ("status", "notes"):
        p = os.path.join(ROOT, "catalog", "meta", f"{name}.json")
        try:
            if not isinstance(load(p), dict):
                problems.append(f"catalog/meta/{name}.json: must hold one JSON object")
        except (OSError, ValueError) as e:
            problems.append(f"catalog/meta/{name}.json: {e}")
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
    """The data block for one page, made the same way the routines make it."""
    meta = lambda name: load(os.path.join(ROOT, "catalog", "meta", f"{name}.json"))
    if key == "physics":
        return {"programs": [r for r in rows if "aud" not in r or "yale" in r["aud"]],
                "status": meta("status"), "notes": meta("notes")}
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "out.json")
        src = os.path.join(ROOT, "catalog", "programs")
        args = [src, out] if key == "ng" else [src, os.path.join(ROOT, "catalog", "meta", "status.json"), out]
        subprocess.run([sys.executable, os.path.join(ROOT, "engine", script), *args],
                       check=True, capture_output=True, text=True)
        snap = load(out)
    for k in ("skipped_for_yale_mentions",) if key == "ng" else ("updated",):
        snap.pop(k, None)
    return snap


def render(template, snap, link):
    text = json.dumps(snap, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    out = template.replace("{{snapshot}}", text, 1)
    out = re.sub(r"\{\{link:(\w+)\}\}", lambda m: link(m.group(1)), out)
    if "{{" in out.split("<!-- SNAPSHOT:START -->")[0]:
        raise ValueError("unreplaced placeholder in template")
    return out


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
        put(os.path.join(site, "index.html"),
              render(template, snap, lambda k: PAGES_URL.format(repo=PAGES[k][1])))
        put(os.path.join(site, "data", "programs.json"), dump(progs))
        files = ["index.html", "data/programs.json"]
        for f in SITE_ENGINE[key]:
            put(os.path.join(site, "engine", f), open(os.path.join(ROOT, "engine", f), encoding="utf-8").read())
            files.append(f"engine/{f}")
        put(os.path.join(site, "MANIFEST"), "\n".join(files) + "\n")
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
            shutil.copytree(os.path.join(ROOT, "data"), os.path.join(tmp, "data"), dirs_exist_ok=True)
            build(tmp)
        print("check passed")
    else:
        build(ROOT)


if __name__ == "__main__":
    main()
