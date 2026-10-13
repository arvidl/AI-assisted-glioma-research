# Working together

This project connects a perspective, educational examples, and a conference
talk. Start with the manuscript plan. Use a small branch for a coherent change;
assistant-created branches use codex/. Open a pull request when ready for review.

Clinical reviewers assess relevance, terminology, and interpretation. Imaging
reviewers assess geometry, compartments, and source images. Numerical reviewers
assess discretization, stability, and expected values. Assign people and
authorship by agreement.

Run make check for Python, make notebooks for notebooks, and make paper for
manuscript or evidence changes. Record actual platforms in docs/validation.md.
Committed notebook sources have empty outputs and execution counts; make
notebooks writes executed copies to outputs/notebooks/. The authorized executed
copies in notebooks/executed/ are regenerated only with make executed-notebooks.

Retain the task, visible tool information, contribution, decision status, and
acceptance evidence for substantive assistance. A passing test does not invent
human review. Do not invent a past transcript or describe an unreviewed artifact
as approved.
