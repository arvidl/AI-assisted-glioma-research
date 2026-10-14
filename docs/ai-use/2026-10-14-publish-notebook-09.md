# Publishing notebook 09

- Date: 14 October 2026.
- Tool: Cursor agent; exact backend snapshot and settings not captured.
- Request: the investigator was "for now, fine with notebook 09" and asked to commit and push it for testing in Colab. The assistant checked that its code imports only `glioma_ai` (`imaging_interactive`, `notebook_display`, `published`, `tumour_interface`), IPython and Matplotlib, reads no data apart from the published figures, has no links to the unpublished notebooks 10–12 (they are named in plain text), and that its relative links to `docs/` are in the public snapshot.
- Contribution: an "Open in Colab" badge and Colab note under the title, the Colab setup cell of notebooks 04–08 before the first code cell, and a Colab-only note and cell before the published-figures cell that fetch the three published figures from the release `published-figures-v1` with `glioma_ai.published.fetch_published_figures` (SHA-256 checked against `imaging_figures.json`), as notebook 01 does. No other cell changed. `scripts/public_snapshot.py` now publishes 00–09; the public README and notebook map list 09 and 10–12 as in review.
- Verification: recorded in `docs/validation.md`.
- Decision: the investigator asked for the publication; the push to public `main` is made with the investigator's approval; hosted Colab runs are the investigator's.

This is a retrospective development summary, not a captured verbatim dialogue.
