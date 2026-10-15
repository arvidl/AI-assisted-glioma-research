# Local data

Only guidance, the example manifest and one authorized derived folder are
tracked. Acquired datasets, identifying metadata, weights, and downloads remain
ignored. See ../docs/data.md. Default examples require none of these files.

`derived/sub-PAT16/` holds small CC0-derived connectivity matrices of one
Brain Tumor Connectomics patient with their provenance, tracked at the
investigator's request for notebook 12. They were derived with
`make pat16-connectome` in the archived private development repository, which
reads the investigator's local pipeline outputs; that step is not part of this
repository.
