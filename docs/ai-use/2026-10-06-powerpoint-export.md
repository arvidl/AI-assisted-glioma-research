# Editable PowerPoint export

- Date: 6 October 2026.
- Tool: Codex desktop assistant and bundled JavaScript Artifact Tool;
  exact backend snapshot/settings were not captured.
- Request: Make a PPTX version of the Beamer talk. The investigator selected
  editable text and tables with scientific figures retained as images.
- Inputs: Existing `talk/slides.tex`, illustrated local `talk/slides.pdf`,
  `talk/speaker-notes.md`, generated source macros and checked figure assets.
- Contribution: Reconstructed the 23-slide sequence in editable PowerPoint
  objects, retained the native results table and hyperlinks, copied the
  scientific panels, preserved equation appearance as images, and transferred
  the speaking guide, timing, backup notes and source links.
- Choices: Preserved the existing 16:9 white/teal design and scientific wording;
  used Arial for editable text. No clinical interpretation or study scope was
  added. Published, synthetic, retrospective, empirical and proposed evidence
  labels remain distinct.
- Verification: Package/layout/font/native-bullet checks and exact-file import
  passed. All 23 final slides were individually inspected after rendering.
  OOXML checks verified source title order, notes, source links, table values,
  embedded image bytes, uncropped images and aspect ratios. The source TeX,
  PDF and speaking guide were not changed. Details are in `docs/validation.md`;
  manifests and receipts are local in ignored `outputs/powerpoint/`.
- Limit: The computer-use tool reported missing permission, so native Microsoft
  PowerPoint rendering and editing were not exercised. No claim of clinical
  validation, measured AI benefit or human scientific approval is made.
- Decision: Local editable snapshot. Later changes to Beamer or PowerPoint
  need deliberate synchronization and another review.

This is a retrospective record of the conversion, not a saved verbatim dialogue.
