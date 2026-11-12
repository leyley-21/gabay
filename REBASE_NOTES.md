# Older UI merge

Base: uploaded als_gabay (2).zip. Merged from the previous delivered ZIP.

Preserved byte-for-byte: the original three CSS files and the complete card
markup between the details toggle and bottom search button, including Why This
May Suit You. Preserved the AST of build_fit_reasons, so its original authored
phrases, O*NET excerpt and personalized guidance remain unchanged.

Merged: previous images and logo assets, ALS education labels, Tagalog question
descriptions, selection scrolling, reduced-motion handling, request/session
protection, submission retry handling, ranking improvements and sourced Philippine
study/salary data. Existing learner attempt and feedback rows are unchanged.

College/TESDA lists remain plain text. Their existing bottom buttons first ask
for a program and city/province, then open TESDA's directory or Google web search.
The dialog explains that course availability must be confirmed. This does not
claim to identify the verified nearest institution offering the exact course.

Salary cards show stored Jobstreet advertised monthly references only. These
reflect the snapshot and role mapping, not a live listing, individualized wage,
or verified current offer. Related occupation proxies are labeled; careers
without a Jobstreet reference remain explicitly unavailable.

Validation: 44 backend tests; assessment-state regression; legacy-card/search
regression; byte/AST checks for preserved styles, named card section and fit
logic; existing learner-history comparison. Browser visual appearance was not
verified in this environment. Prior-release validation documents describe their
own release and are not evidence of a browser check for this merge.

Run: python manage.py initialize-database, then python serve.py.
Checks: python -m unittest discover -s tests -p "test_*.py";
node tests/assessment_state.cjs; node tests/legacy_cards.cjs.

## Requested follow-up

- Removed icon container backgrounds while keeping the existing layout.
- College searches use Google search with the selected program and city/province.
- Salary display contains the numeric range/pay period and Jobstreet reference;
  related-role/source context remains in the link tooltip and API metadata.
- Remote buttons use Jobstreet's remote-plus-career search path.
- Browser scroll restoration is disabled; reload clears old home-section anchors
  and returns to the hero. In-page section links still work when clicked.
- Assessment inputs, selected skills, step and retry identity save locally on
  changes. On reload, a modal offers Continue or Retake. Restore does not submit
  automatically. Retake and successful completion clear the previous draft.
  Invalid drafts are ignored; unavailable storage leaves the form usable and
  displays a message. Progress remains limited to this browser/device.

Validation for this follow-up: 44 backend tests and three dependency-free Node
regressions (assessment_state, legacy_cards, progress_state) passed. A real
Chromium test was prepared (refresh_progress.cjs), but browser launch was blocked
by the environment; it has not passed here. No browser visual check is claimed.

## Career-card PDF download

Added a Download PDF action alongside Retake Assessment in the results header.
It exports all saved recommendations, including collapsed details, from the
current anonymous session. The export route verifies session and CSRF token,
limits repeated requests and does not modify learner history or feedback.

PDFs are generated in memory using ReportLab with embedded DejaVu fonts; font
license text is included. They retain the plain study lists, compact salary and
Jobstreet reference, original fit-reason content and O*NET source links. No
source sentence or recommendation ranking was changed by the export feature.

Validation: 49 backend tests and four Node regressions passed. The 30-career PDF
was rendered and first/middle/last pages visually inspected. Long-text regression
confirms content continues without truncation. The UI browser check remains
unavailable in this environment; the PDF rendering itself was verified.
