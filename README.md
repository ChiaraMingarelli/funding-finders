# Funding Finders

Searchable lists of grants, fellowships, jobs and student programs for Yale Physics, Applied Physics and Astronomy, and for the NANOGrav collaboration. All pages read from one shared catalog of about 1010 programs, each taken from the funder's or employer's own page or from an academic job board such as Academic Jobs Online.

## Pages (`docs/`)

Live on GitHub Pages: https://chiaramingarelli.github.io/funding-finders/

| File | Audience |
|---|---|
| `physics.html` | Yale Physics, all research areas and career stages |
| `applied-physics.html` | Yale Applied Physics (quantum information, photonics, quantum materials, materials science, devices, energy, physical biology) |
| `astronomy.html` | Yale Astronomy (cosmology, exoplanets, extragalactic, galactic, high-energy, stellar, ISM, instrumentation) |
| `nanograv.html` | NANOGrav students, postdocs and faculty job seekers |

Each page is a single self-contained HTML file with its data embedded. They are built from the catalog, so don't edit them by hand: change `catalog/` or `templates/` instead (see below).

Features on every page:

- Filters by career stage, deadline window and, for postdocs, position type (prize fellowship, group postdoc or other). The three Yale pages also filter by research area, status and type; the NANOGrav page also filters by region and by fit with pulsar-timing and gravitational-wave work. "Next 6 weeks" falls back to "all" when nothing is due.
- A **New** tag on programs added in the last 7 days. Filter with "New this week" or type `new` in the search box.
- Tick boxes to export only the programs you care about, as a calendar file (`.ics`, with reminders 6 and 4 weeks before each deadline) or a CSV.
- Per-program **Google Calendar**, **Outlook** and **Apple Calendar** links. The Apple Calendar link downloads a one-program `.ics` file with reminders 6 and 4 weeks before the deadline. The Google Calendar and Outlook links can't carry custom reminders, so set those alerts yourself.

## Catalog (`catalog/`)

This folder is the source of truth. `catalog/programs/<id>.json` holds one program per file, `catalog/meta/status.json` the Physics page's "What's new" lines, `catalog/meta/notes.json` its tips for each career stage, and `catalog/meta/ap_notes.json` and `catalog/meta/astro_notes.json` the "What changed" panels of the Applied Physics and Astronomy pages. `data/programs.json` is the whole catalog as one list, rebuilt automatically.

Each program has these fields:

| Field | Meaning |
|---|---|
| `id` | Stable slug |
| `n`, `f`, `c` | Program name, funder, type |
| `s` | Status: `open`, `rolling` or `watch`. A listing whose deadline has passed is removed, or kept as `watch` with no deadline if the program recurs and its next call is not posted yet |
| `d`, `dt` | Next deadline (ISO date or null) and a free-text deadline note |
| `a`, `e`, `u` | Award, eligibility and notes, official link |
| `fields` | Research areas (`all` = open to every field) |
| `asub` | Astronomy sub-areas |
| `stages` | `ug`, `gr`, `pd`, `fj` (faculty jobs), `tt` (tenure-track), `ten` (tenured) |
| `aud` | Which pages show the row: `yale` (Physics), `ng`, `ap`, `ast` (no `aud` = Physics only). `radar` marks rows for a separate page the maintainer keeps by hand; it does not affect these pages |
| `pt` | Postdoc type: `prize`, `group` or `other` |
| `src` | Source key used to avoid duplicate rows |
| `nofo` | Related grants.gov funding notices |
| `ng` | Replacement text for some fields on the NANOGrav page |
| `yale` | Yale internal or limited-submission step `{d, t, u}` |
| `us`, `nom`, `region`, `nfit` | US-only flag, nomination needed, region, fit for pulsar-timing work |
| `unv` | What could not be confirmed on the funder's page |
| `added`, `checked` | Date the row entered the catalog, date it was last checked |

## Engine (`engine/`)

- `export_ap.py`, `export_astro.py` and `export_ng.py` build each page's embedded data from a folder of catalog rows (`<id>.json`).
- `astro_classify.py` assigns Astronomy sub-areas and decides which rows the Astronomy page shows.
- `export_mod.js` is the tick-box export and calendar-link code inlined in every page.
- `build.py` checks the catalog and builds every page from it and from `templates/`. It writes `docs/` (this site), `sites/<repo>/` (the files each single-page repository copies in), `data/programs.json`, and a `version.json` on every site naming the catalog commit it was built from. Run `python3 engine/build.py --check` to test a change without writing anything.

## How it updates

1. The catalog is rechecked every Monday and new postings are added on the other days of the week. The tips are kept current daily.
2. Whenever `catalog/`, `templates/` or `engine/` changes on `main`, the **Build pages** workflow runs `engine/build.py`, commits the result and publishes `docs/`. It also runs once a day.
3. Catalog updates from the scheduled Claude Code runs in step 1 are pushed to `claude/catalog-*` branches and merged into `main` by the **Accept catalog updates** workflow if they only change catalog data files, delete at most 60 programs, keep every existing `added` date, merge cleanly and pass the build check. Anything else is left on its branch for review.
4. Each single-page repository ([Physics](https://github.com/ChiaraMingarelli/yale-physics-funding-finder), [Applied Physics](https://github.com/ChiaraMingarelli/yale-applied-physics-funding-finder), [Astronomy](https://github.com/ChiaraMingarelli/yale-astronomy-funding-finder), [NANOGrav](https://github.com/ChiaraMingarelli/nanohertz-opportunities)) copies its files from `sites/` and publishes them, and republishes if its live site ever differs from the repository. After each build, the "Build pages" workflow starts these copies right away, so the single-page sites usually update within a few minutes; the hourly schedule is a backup.

Deadlines move. Check the funder's page before you commit to a date.

## License

The code (the scripts in the pages and in `engine/`) is released under the [MIT License](LICENSE). The catalog (`data/programs.json`), the data embedded in the pages and the page text are released under [CC BY 4.0](LICENSE-DATA), so you can reuse them with credit to Chiara Mingarelli. Program details come from each program's official posting; check there before relying on a date.
