# Public working repository and the paper restructured around notebooks 01–12

- Date: 15 October 2026.
- Tool: Cursor agent (reported as Claude Opus 5.5); exact backend snapshot and settings not captured.
- Request: after notebook 12 ran well in Colab, the investigator proposed that the public
  repository skip the talk and slides and keep the paper in LaTeX, with tables, figures and a
  bibliography aligned with the project and notebooks 01–12, and asked for help with the transition
  from the private development repository.
- Investigator decisions (answers to the assistant's questions):
  - The public repository is the working repository from now on. The private repository is
    archived (talk, slides and held-back scripts), with no further snapshots.
  - The paper has one section or subsection per notebook 01–12, each with a figure or table and an
    evidence label, in thematic order from image to cognition: measuring and locating a tumour
    (01, 09); one patient's serial scans (03); growth and its environment (02, 05, 06); physiology
    at the interface (07, 08); networks and cognition (11, 12, 10); auditing AI-assisted
    research (04).
  - The title stays "AI-assisted glioma research: a perspective with reproducible examples in
    imaging and clinical evidence".
  - `paper/references.bib` holds only cited works, each checked against its registry.
  - A built `paper/main.pdf` is tracked as a curated export and rebuilt only with `make paper`.
- Contribution:
  - Infrastructure (commit `136893c` on `codex/paper-public`): `paper/` source imported from the
    private repository; `glioma_ai.paper_assets` and the `glioma-ai paper-assets` command, which
    build every paper figure and number macro from the package and skip, rather than substitute,
    figures whose licensed inputs are not fetched; `make paper-assets` and `make paper`; a public
    `AGENTS.md` and Cursor rule without the talk; `docs/paper-plan.md`; README and CONTRIBUTING
    without the talk; a `paper` job in the public workflow; `scripts/public_snapshot.py` removed.
  - New generated macros: the notebook 01 cohort recomputation (`cohort_numbers.tex`), the BTC
    CANTAB counts (`btc_numbers.tex`) and the notebook 03 two-level revision and fit
    (`lumiere_revision_numbers.tex`, with the figure `lumiere_two_level.pdf`). No number about a
    result is typed by hand in `main.tex`.
  - `paper/main.tex` rewritten in the agreed structure: abstract, introduction with a notebook map
    (Table 1) and five evidence labels, one contribution block per notebook, new sections for
    notebooks 03, 10, 11 and 12 and the notebook 01 cohort, a table of checks for notebook 04, and
    revised discussion, conclusion, declarations and reproduction appendix. Text from the earlier
    draft was reused and shortened where it still matched the notebooks. The talk and the private
    repository URL were removed.
  - `paper/references.bib`: three uncited entries removed (Zhao 2021, Kefeli 2024, Zarodniuk 2026)
    and 21 added (Calabrese 2022, Swanson 2008, Herbet 2024, Douw 2026, Salvalaggio 2025,
    Hannisdal 2026, Catani 2005, Honey 2009, Smith 2015, Aerts 2018, Tykocki 2026, Robbins 1994,
    Jacobson 1991, Chelune 1993, McSweeny 1993, Riley 2025, Collins 2024 and four OpenNeuro dataset
    versions), 65 entries in all. New entries were generated from the registry metadata; author
    order of the OSF release now follows its DataCite record.
- Verification: recorded in `docs/validation.md`. Each sentence describing a notebook was written
  from the notebook's own text and the generated macros; no interpretation was added that the
  notebooks do not state. The Hannisdal et al. sentence follows the notebook 02 summary of the
  paper, not the full text.
- Not done: investigator, clinical and citation-context review of the rewritten paper; review of
  the sub-PAT16 upstream QC (0 of 37 items); the archive note in the private repository.

This is a retrospective development summary, not a captured verbatim dialogue.
