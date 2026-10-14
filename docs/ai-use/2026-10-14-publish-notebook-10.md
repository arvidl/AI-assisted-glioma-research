# Publishing notebook 10

- Date: 14 October 2026.
- Tool: Cursor agent; exact backend snapshot and settings not captured.
- Request: the investigator found notebook 10 "as good as it gets for now" and asked to commit and push it for testing in Colab.
- Investigator decisions (answers to the assistant's questions): a Colab-only cell that downloads the pinned OpenNeuro participant tables and the sub-PAT16 session table with `fetch_btc` (SHA-256 checked) and does nothing outside Colab; the OSF release is not fetched in Colab, so the OSF cross-check and the paper's case figure show their notices there.
- Contribution: an "Open in Colab" badge and Colab note under the title, the Colab setup cell of notebook 09 before the first code cell, and the Colab-only note and fetch cell before the data cell. No other cell changed. `scripts/public_snapshot.py` now publishes 00–10 and no longer reports `attachment:` links as file links; the public README and notebook map list 10.
- Verification: recorded in `docs/validation.md`.
- Decision: the investigator asked for the publication; the push to public `main` is made with the investigator's approval; hosted Colab runs are the investigator's.

This is a retrospective development summary, not a captured verbatim dialogue.
