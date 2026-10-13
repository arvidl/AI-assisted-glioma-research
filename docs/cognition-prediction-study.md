# Proposed AI study of imaging and cognitive outcome

Version 0.1, 6 October 2026. This is a design for investigator and clinical
review, not an approved protocol, registered study or completed evaluation.
No empirical predictor has been fitted in this repository.

## Question and estimand

Do preoperative network and mechanistic-dynamics features improve prediction
of follow-up spatial working-memory performance beyond baseline cognition,
clinical information and reviewed tumor anatomy?

The candidate primary endpoint is the released CANTAB SSP span at a
prespecified follow-up window, with baseline SSP included as a predictor.
Raw change is a secondary descriptive endpoint. SSP is bounded and discrete;
evaluate errors in span units and inspect boundary behavior. No synthetic
threshold defines cognitive impairment or clinically important change.
RTI five-choice, RVP sensitivity and SOC planning are secondary endpoints
with their own units and directions. These choices require investigator and
neuropsychological review before freezing the analysis.

Target future observed performance under the recorded care pathway. Prediction
does not identify the causal effect of resection, treatment, or tumor growth.
An actual surgical date and follow-up window must be collected. The source
behavioral release provides assessment dates rather than the surgical date.
Its scheduled six-month follow-up is not assumed to equal every actual interval.

## Existing resource and feasibility

The pinned OSF release and notebook 10 provide the behavioral availability
audit. The behavioral cohort is larger than the MRI recruitment cohort.
Complete paired glioma scores are a small subset. Imaging overlap, modality
availability and QC can reduce eligibility further. Do not pool meningioma
with glioma to enlarge a nominal glioma sample. Do not reinterpret historical
grades as modern molecular diagnoses or assume education/treatment fields exist.

Use the present resource for the empirical illustration, linkage development
and sensitivity planning. Its small glioma sample does not support claims of
predictive performance, flexible feature selection or a trained deep network.
A larger linked glioma cohort is required for the predictive comparison.
Before enrollment or analysis, use plausible noise, endpoint distributions and
feature correlations in simulations to choose sample size, model complexity
and desired precision. Record that decision prospectively; no universal sample
threshold or effect size is assumed here.

## Comparisons

| Model | Information available before the outcome | Purpose |
| --- | --- | --- |
| Persistence | Baseline SSP only, unchanged at follow-up | Simple reference prediction |
| Clinical baseline | Baseline SSP and a frozen small set of preoperative clinical variables | Account for starting performance and available clinical context |
| Anatomy | Baseline information plus a prespecified burden/location feature | Establish the value of anatomical information |
| Network/dynamics | Anatomy plus a few prespecified baseline SC/FC summaries or independently fitted dynamics parameters | Evaluate added information from the functioning network |
| Physiological extension | Add appropriately acquired baseline EEG/MEG/ECoG features in a separate cohort | Explore dynamic information when recordings actually exist |

Age, education, subtype, baseline seizures and medication are candidate clinical
variables, subject to measured availability and a justified feature budget.
Actual postoperative treatments, measured resection cavities and follow-up
connectivity are unavailable at the preoperative prediction time and are
excluded from predictors. Known treatment plans may enter only if documented
before prediction. Predictions conditional on a proposed surgical plan require
explicit plan geometry and a separate validation, not the observed cavity.

A distinct retrospective analysis may relate changes in burden/connectivity
to cognitive changes and treatment. Label it association and keep it separate
from preoperative forecasting. Neither analysis reconstructs tumor growth from
a tumor-to-cavity comparison. Growth questions require serial imaging and
cognition with suitable pretreatment/follow-up timing.

## AI contribution and mechanistic modeling

The trained predictive component would be a compact regularized supervised
model, initially ridge regression with a prespecified penalty grid. Compare
the same model family across feature sets, along with the persistence baseline.
This isolates added information from a change in modeling flexibility.
Select a bounded/ordinal alternative only prospectively, with its own checks.
Do not add a large nonlinear learner because the workstation can run one.

Imaging AI may contribute validated segmentation features where all required
inputs exist. The published T1/T1c/T2/FLAIR SegResNet does not run directly on
BTC T1/diffusion/BOLD. Supplied masks and reviewed T1 anatomy are viable research
inputs; they still require labeling, space, acquisition and quality checks.
SC/FC extraction and The Virtual Brain simulations are conventional analysis
and mechanistic modeling. Calibration must use baseline imaging only, never
cognitive outcomes or held-out follow-up data.

Generative research assistance can help implement the protocol, audit source
joins, verify units and timing, produce analysis code and check interpretation.
Retain contributions, investigator decisions and verification. No patient rows
are sent to an external assistant by this design. The already proposed
matched-task pilot evaluates assistance benefit separately; prediction accuracy
does not measure productivity, scientific quality or improved patient care.

## Leakage prevention and evaluation

1. Freeze endpoint, eligible population, follow-up window, features and model
   budget before examining outcome associations. Document exclusions and
   missingness separately for imaging and cognition.
2. Verify unique participant IDs and visits in a local linkage manifest. Keep
   all observations from a person in the same split. Preserve known caregiver
   relationships if controls enter a shared modeling exercise; controls are
   otherwise used only for exploratory retest comparisons.
3. Use subject-level outer validation. Perform scaling, imputation, outcome
   transformations, data-driven feature selection and penalty tuning inside
   the training folds, with nested inner validation where tuning is needed.
   Record fixed pretrained-model provenance and training overlap. Avoid site
   leakage with site-separated external validation when available.
4. Use identical eligible held-out participants to compare model sets. Report
   paired held-out absolute-error differences, MAE in span units, prediction
   plots and performance relative to persistence. Report failed fits, missing
   features and exclusions. Predefine how incomplete predictions are handled;
   do not drop inconvenient errors selectively.
5. Quantify uncertainty by resampling participants through the full analysis
   procedure. Cross-validation folds/repeats are not independent patients.
   Tiny-sample resampling does not create reliable confidence intervals.
   Report instability and dependence on influential cases, model choices,
   motion/HRF handling and missing-data assumptions.
6. Preserve a separate external or temporal validation set for the final model
   if the recruited sample permits it. Predictive validity is a prerequisite;
   clinical usefulness and patient benefit require a subsequent prospective
   evaluation of decisions and outcomes.

Prefer one reviewed primary endpoint and report secondary measures as
exploratory, with multiplicity addressed in any inferential analysis. Apply
reliable-change classification only with compatible test/retest calibration.
The small repeated caregiver group is not a ready-made normative database.

## Analog cognition and astrocytic hypotheses

A proposed mechanistic hypothesis is that network coordination and electrical
wave organization explain cognitive variation beyond anatomy. CANTAB measures
task performance; BOLD and fitted neural-mass parameters are not direct LFP or
electric-field observations. Testing distinctive analog-cognition predictions
needs appropriate recordings during a relevant task, with prespecified wave
features and comparisons against ordinary connectivity explanations.

Astrocytic potassium handling is a possible contributor to excitability, but
this dataset contains no astrocytic measurements. It cannot identify the
clearance rates in notebook 07. Cytoelectric/microtubule mechanisms require
their own cellular measurements and controlled perturbations. These are
hypotheses and experimental extensions, not inferred latent clinical labels.

## Data and review record

Use blank local copies of the schemas in `docs/cognition-study/`. Record
source hashes, visit timing, availability at prediction, acquisition/QC,
pipeline version, coordinate space and evidence status. The templates have
headers only. Store all completed rows and links in ignored local storage.
No enrollment, ethics approval, collaborator agreement, fitted model,
measured benefit or clinical deployment is claimed.

Primary context: [Aerts et al., 2019](https://biblio.ugent.be/publication/8625236),
[MRI resource](https://doi.org/10.1038/s41597-022-01806-4),
[virtual resection](https://doi.org/10.1016/j.neuroimage.2020.116738),
[analog cognition](https://doi.org/10.1523/JNEUROSCI.0711-26.2026).
The proposed comparison is our study design, not an outcome reported by these sources.
