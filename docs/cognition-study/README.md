# Blank study schemas

These header-only CSVs are proposed data-collection schemas. They contain no
participants, observations or results. Copy them to ignored local storage;
never commit completed rows or identifier crosswalks.

The local study identifier belongs only to the approved linkage process.
Do not place source patient identifiers or exact calendar dates in shared
results. Relative times use days and need an actual surgery date. A missing
value remains missing, never zero. Distinguish measured, derived, synthetic
and proposed evidence. Do not infer molecular subtype from historical grade.

For each feature, document its units, visit, availability at the prediction
time, coordinate space, label meaning, source hash and QC. `available_at_prediction`
must reflect recorded timing, not whether a value exists in the final dataset.
Features measured after prediction cannot enter a preoperative forecast.
Imaging transformations and model-derived parameters need their own provenance.

Review endpoint definitions, assessment windows, data access and the
[proposed analysis](../cognition-prediction-study.md) before filling these forms.
