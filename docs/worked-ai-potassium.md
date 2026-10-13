# Worked AI-assisted example: astrocytic potassium clearance

**Evidence status:** Retrospective reconstruction from the saved development
summary, current source and executable checks. This is an actual development
contribution, not a verbatim interaction, an independently approved model or
an experiment measuring AI benefit. No historical prompt, rejection, timing
or model setting has been reconstructed as if it had been captured.

| Stage | What is documented | Inspectable evidence |
| --- | --- | --- |
| Investigator's question | The investigator requested a glioma–brain perspective addressing astrocytes, LFPs and cognition, with biological modeling examples. The narrow teaching question became: what changes when prescribed potassium release is held fixed and clearance changes? | Original revision summary: `docs/ai-use/2026-10-06-neuroglial-cognition.md` |
| AI contribution | Codex helped formulate and implement a one-compartment excess-potassium model, ideal Nernst calculation, controlled comparisons, notebook and shared figures. | `src/glioma_ai/neuroglial.py`, `src/glioma_ai/neuroglial_examples.py`, notebook 07 |
| Investigator choices | The topic and clinical audience came from the investigator. Fixed volume, release pulses, linear clearance, baseline K, intracellular K and temperature are prescribed implementation choices requiring scientific review. They are not recorded as investigator-approved physiological estimates. | Explicit assumptions and units in notebook 07 and the generated parameter record |
| Verification | Compare with the independent constant-input analytic solution; account for input, retained excess and both clearance contributions; check zero-clearance and decay limits; compare alternate clearance splits; check ideal Nernst sign and concentration-ratio limits. | `tests/test_neuroglial.py`; executable checks in notebooks 04 and 07; actual runs in `docs/validation.md` |
| Interpretation and uncertainty | Under these equations, reduced total clearance prolongs K excess. Equal total clearance produces the same trace despite different astrocytic attribution. The ideal equilibrium potential is a narrowly defined calculation. Physiological calibration, spatial buffering, explicit cells, membrane voltage, firing and cognition require additional evidence. | Model docstrings, notebook interpretation and paper example |

The balance is expressed per fixed extracellular reference volume:

`initial excess + cumulative release = current excess + astrocytic clearance + other clearance`

Every term has units of mM-equivalent in that reference volume. This is
concentration accounting with an implicit receiving reservoir, not a whole-tissue
mass measurement. Passing it supports implementation of the prescribed model.
It does not establish the biological attribution of an observed K trace.

Notebook 04 connects the record to an independent analytic and balance check;
notebook 07 contains the full experiment. The same package generates paper and
talk figures. Rebuilding uses ordinary CPU calculations without a language-model
call. Human scientific review remains pending; comparative productivity,
scientific quality and patient outcomes have not been measured.

The original machine-readable development record remains unchanged:
`docs/ai-records/2026-10-06-neuroglial-cognition.json`. The current presentation
revision has its own record, preserving the distinction between developing the
model and later explaining its AI contribution.
