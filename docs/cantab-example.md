# Source-verified CANTAB example

This is a descriptive empirical example, developed at the investigator's
request on 6 October 2026. It does not estimate a causal surgical effect,
fit a cognitive predictor, assess reliable change, or test analog cognition.

## Source and verification

The [OSF behavioral release](https://osf.io/5kfw3/) is the supplementary
resource for the exploratory behavioral study. It differs from the selected
MRI cohort in [Aerts et al., 2022](https://doi.org/10.1038/s41597-022-01806-4).
Join imaging and behavior by verified source IDs, never row order. Preserve
the original GLI/MEN/CON groups and historical diagnostic labels.

`src/glioma_ai/references/cantab_osf.json` pins Data.csv revision 2, Legend.csv
revision 1 and the authors' non-imputed regression code revision 1 with download
URLs and SHA-256 hashes. The CSV is UTF-8; the source legend is Windows-1252.
The authors' code establishes day/month/two-digit-year date parsing.
The dates refer to assessments; the surgery date is not supplied here.
Latency units are milliseconds, RVP A prime is unitless sensitivity, SOC counts
problems solved in minimum moves, and SSP is a maximum spatial-span count.
RTI uses the release's five-choice measure, without guessing mean versus median.

An explicit local configuration links the investigator's prepared session table
to one glioma row. Five measures can be checked at both visits: MOT mean latency,
RTI five-choice, RVP sensitivity, SOC minimum-move problems and SSP span.
The other local measures are not verified by this narrower release.
Exact agreement and agreement at released decimal precision are separate
outcomes. Extra local decimal places do not establish extra source precision.
The figure uses source values, never higher-precision local substitutions.

The completed audit is recorded in ignored `outputs/cantab/`. One attention
score agrees only at the released precision. At that precision the paired
attention scores are equal, so the figure does not claim a small improvement.
The actual case interval and cohort counts are generated from the source.
Neither the local session table nor the source-case identifier is committed.

## Reproduce locally

```sh
make cantab-fetch
```

This explicitly downloads only the pinned public tables and analysis code into
ignored `data/cantab/osf/`. It acquires no MRI, weights or trial-level data.
Keep the source license and cite the OSF release and associated studies.
Create ignored `local/cantab-case.json` using this schema, replacing both values:

```json
{
  "source_case_id": "EXPLICIT_SOURCE_ID",
  "sessions_path": "/absolute/path/to/prepared_sessions.tsv"
}
```

```sh
make cantab
make notebooks
make paper
make talk
```

`make cantab` verifies hashes and case agreement before writing four paired
plots, numbers and provenance. A mismatched, missing, duplicated or ambiguous
case fails. Raw tables, the local session table, source IDs, exact dates and
generated artifacts stay local. The released values of the verified case appear
in the tracked paper and in the authorized executed copy of notebook 10, which
cites the CC BY 4.0 release; source ZIPs exclude `notebooks/executed/`. Exported figure/record labels
omit patient IDs, exact calendar dates and demographics.

Notebook 10 always exercises a clearly synthetic precision control. With the
explicitly acquired local release it additionally reports empirical availability;
with the local case configuration it builds the verified case figure. Without
those inputs it gives an acquisition/configuration notice and does not replace
the case with synthetic data. No notebook automatically fetches patient data.

Clean source builds omit the empirical image and show a preparation notice.
The illustrated local talk and paper contain the real example. The private
source ZIP excludes acquired data and case configuration. A Colab user may
explicitly acquire the public release with the CLI; case data/configuration
must be supplied deliberately. Hosted Colab has not been exercised.

## What the example establishes

Paired scores describe performance across surgery, recovery and intervening
treatment. Test repetition, seizures, medication, fatigue, mood and assessment
conditions can also contribute. Normative impairment and reliable change require
compatible norms/retest calibration that are not provided by this release.
Repeated caregivers offer an exploratory comparison, with shared distress and
a small sample; they do not isolate a surgical effect or supply validated norms.
Percent changes in milliseconds, sensitivity and span are not pooled.

The BTC MRI includes T1, diffusion and resting-state BOLD. The published
high-precision SegResNet pipeline requires T1/T1c/T2/FLAIR. Its methods and
quality-control principles provide a bridge, but its four-input model cannot
run directly on BTC T1 alone. No contrast is synthesized or substituted here.
Reviewed supplied masks, anatomy and connectomics need separate validation.
There are no LFP, traveling-wave, astrocyte or microtubule observations in this
example. CANTAB supplies behavioral endpoints for future mechanistic studies.

The [prediction protocol](cognition-prediction-study.md) distinguishes a larger
linked study from this single-case illustration. The existing research-assistance
benefit pilot remains a separate evaluation with different endpoints.
