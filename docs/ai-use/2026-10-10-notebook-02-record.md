# Notebook 02 contribution record and controls caption

- Date: 10 October 2026.
- Tool: Cursor agent; exact backend snapshot and settings not captured.
- Request: give notebook 02 a contribution cell in the format of notebook 01, with reasons for the design decisions, a paper-style caption for the controls figure, and a comparison of D and ρ with the literature checked before it is added.
- Inputs: project source and the regenerated synthetic run record; the full text of Wang et al. 2009 (Cancer Res 69:9133) retrieved by web search.
- Contribution: five-field contribution record with a clinical question, design decisions with reasons and a table comparing D, ρ, v* and ℓ with Wang et al. 2009; panel letters, a contour legend and fixed colours in the controls figure; a Figure 1 caption; removal of three empty cells.
- Investigator choices: the request set the format and the literature check. The stated reasons for the pre-existing coefficients, initial state, time window and thresholds are assistant-written explanations of an earlier design, awaiting review; the choice of Wang et al. 2009 as the comparison source and the reading of its D values as mm²/yr are assistant choices recorded with their justification in the notebook.
- Verification: recorded in `docs/validation.md`.
- Evidence status: synthetic numerical experiments; published coefficients are quoted for scale only and nothing is fitted.
- Decision: pending investigator review.

This is a retrospective development summary, not a captured verbatim dialogue.

## Addendum: motivation section

- Request: open the notebook with serial boundary observation (manual or automated, with error; growth, migration and splitting into disjoint regions) and the question of forecasting by analogy with weather prediction, including PDE-based and AI weather models (GenCast, Aurora, WeatherNext 3) and the aggressive-tumor-as-cyclone analogy with its limit for diffuse tumors.
- Investigator choices: the framing, the analogy and the named weather models.
- Contribution: wording of the section; verification of the weather-model claims and the addition of Yankeelov et al. 2015 as the oncology precedent; the data-density contrast, the air-quality-plume comparison and the placement of the notebook as a first step are assistant additions awaiting review.
- Evidence status: literature context and explicitly labelled speculation; no forecast, model fit or new result.
- Follow-up: the investigator drafted a point on treatment as an intervention with no counterpart in weather forecasting; the assistant revised it (treatment-conditional forecasts, confounding of treatment and observed course, pseudoprogression with a RANO 2.0 citation), and the investigator asked for the revision to be applied.

## Addendum: reference update

- Request: check whether RANO has a version newer than 2.0; add recent tumour-microtube papers on detection and function, recent cancer-neuroscience and cytoelectric-coupling papers on glioma growth; explain each model symbol with references, including Murray.
- Contribution: literature search and selection, citation checks, the added notebook text and its wording of each finding.
- Investigator choices: the four topics. The selection of papers and their one-line summaries are assistant choices awaiting review; the search was targeted, not systematic.
- Evidence status: literature context; mechanistic results are mainly experimental and patient findings associations, as the notebook states.

## Follow-up: paper and talk

- Request: carry the notebook references into the paper and the talk's backup slides, then push.
- Contribution: bibliography entries from Crossref records, paper sentences, backup-slide source lists and notes, regenerated exports.
- Verification: Crossref showed that Swanson et al. 2004 concerns a therapeutic window, so the notebook's description of it was corrected. Builds and checks are recorded in `docs/validation.md`.
- Evidence status: unchanged; literature context, with experimental results, patient associations and hypotheses labelled as such.
