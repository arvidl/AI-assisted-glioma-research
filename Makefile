UV ?= uv
LATEXMK ?= latexmk
export PATH := /Library/TeX/texbin:$(PATH)

.PHONY: setup demo check notebooks executed-notebooks clear-notebooks paper paper-assets doctor published-figures published-figures-fetch cantab-fetch btc-fetch cantab lumiere-metadata lumiere-fetch lumiere-bundle lumiere-bundle-fetch hpgs-bundle hpgs-bundle-fetch

setup:
	$(UV) sync --locked --group notebooks

doctor:
	$(UV) run --locked glioma-ai doctor

demo:
	$(UV) run --locked glioma-ai demo --output outputs/demo

# Explicit local import; author figure inputs are not tracked in this repository.
published-figures:
	$(UV) run --locked glioma-ai published-figures --output paper/generated --checkout "$(HPGS_REPO)"

# Explicit acquisition of the same pinned, unmodified CC BY 4.0 figures from
# their GitHub release (published-figures-v1) into ignored paper/generated/.
published-figures-fetch:
	$(UV) run --locked glioma-ai published-figures-fetch --output paper/generated

# Explicit acquisition and a separate empirical workflow; defaults never fetch data.
cantab-fetch:
	$(UV) run --locked glioma-ai cantab-fetch --output data/cantab/osf

btc-fetch:
	$(UV) run --locked glioma-ai btc-fetch --output data/btc

cantab:
	$(UV) run --locked glioma-ai cantab --release-dir data/cantab/osf --case-config local/cantab-case.json --output outputs/cantab --paper-dir paper/generated

# Explicit local extraction of the tracked LUMIERE Patient-048 metadata from the
# released CSV tables (LUMIERE_DIR holds the four LUMIERE tables).
lumiere-metadata:
	$(UV) run --locked python scripts/extract_lumiere_metadata.py --lumiere-dir "$(LUMIERE_DIR)"

# Explicit acquisition: range-reads the 36 pinned Patient-048 files (about 38 MB)
# from the 32.6 GB LUMIERE Figshare archive into ignored data/lumiere/.
lumiere-fetch:
	$(UV) run --locked glioma-ai lumiere-fetch --output data/lumiere

# Explicit local build of the release ZIP of the prepared Patient-048 inputs
# (about 26 MB; LUMIERE_P048_ROOT is the investigator's prepared root).
lumiere-bundle:
	$(UV) run --locked python scripts/build_lumiere_bundle.py --prepared-root "$(LUMIERE_P048_ROOT)"

# Explicit acquisition of that ZIP from the pinned GitHub release into ignored
# data/lumiere_p048_prepared/ (set LUMIERE_BUNDLE_ARGS="--use-gh" if the repository is not public).
lumiere-bundle-fetch:
	$(UV) run --locked glioma-ai lumiere-bundle-fetch --output data $(LUMIERE_BUNDLE_ARGS)

# Explicit local build of the release ZIP of the UCSF-PDGM cohort inputs of
# notebook 01's Figure 3 (about 10 MB; HPGS_REPO is the companion checkout).
hpgs-bundle:
	$(UV) run --locked python scripts/build_hpgs_bundle.py --checkout "$(HPGS_REPO)"

# Explicit acquisition of that ZIP from the pinned GitHub release into ignored
# data/ucsf_pdgm_cohort50/ (set HPGS_BUNDLE_ARGS="--use-gh" if the release is not public).
hpgs-bundle-fetch:
	$(UV) run --locked glioma-ai hpgs-bundle-fetch --output data $(HPGS_BUNDLE_ARGS)

check:
	$(UV) run --locked ruff check .
	$(UV) run --locked ruff format --check .
	$(UV) run --locked pytest

notebooks:
	$(UV) run --locked --group notebooks python scripts/check_notebooks.py

# Investigator-authorized tracked executed copies of notebooks 01-12 in
# notebooks/executed/; needs the fetched inputs of 01, 03, 09 and 10 and the
# local CANTAB inputs of 10 and 12 (see docs/data.md).
executed-notebooks: notebooks
	$(UV) run --locked --group notebooks python scripts/export_executed_notebooks.py

clear-notebooks:
	$(UV) run --locked python scripts/clear_notebook_outputs.py

# Figures and number macros for the paper. Synthetic examples and the tracked
# sub-PAT16 matrices are always built; fetched inputs (make btc-fetch,
# hpgs-bundle-fetch, lumiere-bundle-fetch, published-figures-fetch) are used
# when present, and paper/generated/assets.json lists what was skipped.
paper-assets:
	$(UV) run --locked glioma-ai paper-assets --output outputs/paper --paper-dir paper/generated

paper: paper-assets
	cd paper && $(LATEXMK) -pdf -interaction=nonstopmode -halt-on-error main.tex
