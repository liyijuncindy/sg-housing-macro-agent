# Submission validation — 2 October 2026

The submission completes the original task's report metadata and delivery requirements. Its sample is [english_submission_run](../examples/english_submission_run/report.md), with an [HTML presentation](../examples/english_submission_run/report.html) and a [concise engineering report](engineering-report.md). The reporting cutoff remains **1 October 2026**. No source refresh or new model execution was made for these changes.

## Required report fields and wording

New v2 executions and editorial presentations record `report_fields_version=2`. All five selected indicators now display their recorded update-frequency statements and complete sales, rental, possible economic-response-lag and limitations fields. Observation frequency, an inferred update cadence, a table-update date and an observation's publication date are separate concepts. Unverified release timing is labelled explicitly.

Seven selection reasons and twelve narrative fields have explicit editorial corrections. The sample displays twelve editorial labels and eight original-model narrative labels; original selections and the full original trace remain preserved. The changes clarify the retained vacancy denominator, household-stock versus gross-formation scope, resident-employed-household income coverage, and unverified timing. They do not change selected IDs or numerical conclusions.

Uncaptured, missing or empty candidate observations display **Not assessed** in the enhanced selection table. An assessed zero score remains zero. Older snapshots without the presentation marker retain their original byte-identical reports.

[Content audit](evidence/submission-content-audit.json) verified all required fields, labels, selected IDs, source manifests and **80 unchanged source artifacts**, including every original raw response and chart. The sample records zero model tokens, zero model calls and zero source calls for its editorial presentation.

## Tests, installation and workflow

- **260 automated tests passed**, including six new regressions for required fields, economic versus statistical lags, field-level authorship, missing metadata/fallbacks, unassessed versus genuine zero scores, and historical presentation compatibility. [Full test log](evidence/submission-tests.txt).
- A wheel was built and installed without dependencies into a new isolated virtual environment. Neither the model SDK nor Matplotlib was installed there. **All eleven saved reports replayed exactly**, with no model or source request. [Installed-package record](evidence/submission-installed-package.json).
- The ordinary v2 CLI was exercised in rules mode using the verified original source snapshot. It recomputed candidate checks, changes and research, generated charts and a complete English report, and recorded the new presentation marker. This was a saved-source workflow, not a fresh retrieval or model run. [Workflow record](evidence/submission-workflow-check.json).
- Static HTML validation confirmed eight valid embedded SVG charts, five complete metadata/narrative sections and valid relative links. Automated browser navigation to the local file was disallowed by the browser's file-URL policy; no browser-rendering verification is claimed. [HTML record](evidence/submission-html-check.json).

The independent numerical audit of the underlying live capture remains in [the v2 validation record](report-v2-validation.md). No prediction-training or optimal-predictor claim is required for the original task. Historical release availability, automatic revision differences and exhaustive semantic verification remain disclosed limitations.

## Final archive

The delivery archive is named **Yijun Li Engineering Task.zip**. Packaging uses a clean local clone, retains `.git` and meaningful commit history, sets only the public repository URL as its remote, and excludes local `.env`, virtual environments, caches, credential configuration, hooks and reflogs. Configured keys are checked against both delivery files and Git objects without printing them.

The ZIP's exact commit, checksum, Git integrity, file identity, extracted-install/replay/workflow checks and secret-exclusion results are recorded in **Yijun Li Engineering Task.package.json**, written alongside the archive. This external receipt avoids a self-referential archive checksum and is separate from the source-run manifest. The README supplies fresh setup, full execution, exact report regeneration and test instructions.
