# Funding Finders

Searchable lists of grants, fellowships, jobs and student programs for Yale Physics, Applied Physics and Astronomy, and for the NANOGrav collaboration. All pages read from one shared catalog of about 910 programs, each taken from the funder's own page.

## Pages (`docs/`)

Live on GitHub Pages: https://chiaramingarelli.github.io/funding-finders/

| File | Audience |
|---|---|
| `physics.html` | Yale Physics, all research areas and career stages |
| `applied-physics.html` | Yale Applied Physics (quantum information, photonics, quantum materials, materials science, devices, energy, physical biology) |
| `astronomy.html` | Yale Astronomy (cosmology, exoplanets, extragalactic, galactic, high-energy, stellar, ISM, instrumentation) |
| `nanograv.html` | NANOGrav students, postdocs and faculty job seekers |

Each page is a single self-contained HTML file with its data embedded, so the `docs/` folder can be served as-is with GitHub Pages (Settings → Pages → Deploy from branch → `/docs`).

Features on every page:

- Filters by research area, career stage, status, type and deadline window. "Next 6 weeks" falls back to "all" when nothing is due.
- A **New** tag on programs added in the last 7 days. Filter with "New this week" or type `new` in the search box.
- Tick boxes to export only the programs you care about, as a calendar file (`.ics`, with reminders 6 and 4 weeks before each deadline) or a CSV.
- Per-program **Google Calendar** and **Outlook** links. These can't carry custom reminders, so set the 6- and 4-week alerts yourself.

The live versions also run inside Claude, where they read the catalog live and offer "email me when the call opens" sign-ups. Those features need Claude and are switched off in these static copies.

## Catalog (`data/programs.json`)

One object per program:

| Field | Meaning |
|---|---|
| `id` | Stable slug |
| `n`, `f`, `c` | Program name, funder, type |
| `s` | Status: `open`, `rolling`, `watch`, `closed` |
| `d`, `dt` | Next deadline (ISO date or null) and a free-text deadline note |
| `a`, `e`, `u` | Award, eligibility and notes, official link |
| `fields` | Research areas (`all` = open to every field) |
| `asub` | Astronomy sub-areas |
| `stages` | `ug`, `gr`, `pd`, `fj` (faculty jobs), `tt` (tenure-track), `ten` (tenured) |
| `aud` | Which pages show the row: `yale`, `ng`, `ap`, `ast` (no `aud` = Physics only) |
| `yale` | Yale internal or limited-submission step `{d, t, u}` |
| `us`, `nom`, `region`, `nfit` | US-only flag, nomination needed, region, fit for pulsar-timing work |
| `unv` | What could not be confirmed on the funder's page |
| `added`, `checked` | Date the row entered the catalog, date it was last checked |

## Engine (`engine/`)

- `export_ap.py`, `export_astro.py` and `export_ng.py` build each page's embedded data from a folder of catalog rows (`<id>.json`).
- `astro_classify.py` assigns Astronomy sub-areas and decides which rows the Astronomy page shows.
- `export_mod.js` is the tick-box export and calendar-link code inlined in every page; `alerts_mod.js` and `alerts_dlg.html` are the alert sign-up code used by the live pages.

The catalog is rechecked every Monday, new postings are added on the other days of the week, and the tips are kept current daily. This repository is rebuilt from the catalog and pushed automatically every day at about 1 pm Eastern.

Deadlines move. Check the funder's page before you commit to a date.

## License

The code (the scripts in the pages and in `engine/`) is released under the [MIT License](LICENSE). The catalog (`data/programs.json`), the data embedded in the pages and the page text are released under [CC BY 4.0](LICENSE-DATA), so you can reuse them with credit to Chiara Mingarelli. Program details come from each funder's own page; check there before relying on a date.
