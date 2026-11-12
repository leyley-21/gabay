# Assessment and icon fixes

- Education options keep their ALS labels while sending the values accepted by the server. Previously, all three ALS choices were rejected as invalid and shown as connection failures.
- Validation, session, rate-limit, server, timeout and network errors now have separate messages.
- Answers and the submission ID are preserved for retries; repeated clicks do not start duplicate in-flight submissions.
- Navigation between assessment steps is blocked during submission.
- Logo and icon containers scale with viewport width, maintain square proportions and resist flex shrinking. Modal content can scroll on short screens.

## Verification

- `python -m unittest discover -s tests`: 37 tests passed, including submission of all four frontend education values.
- `node tests/assessment_state.cjs`: passed submission, offline, timeout, duplicate-click, retry-token and HTTP error checks.
- JavaScript syntax checks passed.
- `tests/browser_regression.cjs` provides browser checks for seven viewport widths and network scenarios. These were not completed here because the environment blocks Chromium startup; visual responsiveness remains unverified.

## Using this update

Extract this project, install dependencies using `python -m pip install -r requirements.txt`, and start it using your usual command (for example, `python serve.py`). Reload your browser after restarting the server.

This archive contains the application, original database and data files. The bundled Windows virtual environment and generated Python caches are omitted; create or reuse a local virtual environment and install requirements there.


# Career card update

- Estimated salary is visible in the card summary. Historical data, industry averages and related-role estimates retain visible labels so they are not presented as current exact pay. Missing salary data stays unavailable.
- Source links, mapping notes and other salary evidence are inside a closed Salary details dropdown.
- One college or training option appears directly. Multiple options use a closed dropdown showing the first option and a count; opening it reveals all options with compact Search controls.
- Remote setup details are collapsed.
- Suitability notes use the occupation's own task descriptions, selecting up to two passages with supported connections to the learner's interests and selected skills. Connection tags require task evidence and qualifying scores; there is no repeated “aligns with” sentence or rotating generic praise.
- Low-interest conflicts and on-site conflicts remain visible within Career Details.

Validation: 38 Python tests passed; `node tests/career_cards.cjs` and `node tests/assessment_state.cjs` passed. JavaScript syntax checks passed. Browser visual checks remain unverified due to the Chromium startup restriction described above.
