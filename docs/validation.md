# Checks for this release

- Fourteen integration/regression checks passed on temporary databases.
- Complete browser walkthrough passed with the original uploaded layout: all
  12 interest questions, skills, See Result, details, feedback, pagination, retake,
  Back to previous step/home and scroll-to-top controls.
- Back and Retake Assessment were visible with explicitly checked dark text,
  solid borders and white backgrounds. Screenshots were visually reviewed.
- Viewport checks passed at 320, 360, 390, 430, 768, 1024 and 1440 CSS pixels
  without horizontal page overflow. No JavaScript page errors occurred.
- Cached catalog/index is reused across quiz-history writes. Committed reference
  edits invalidate it. New feedback changes scores on the next request without
  refitting the career catalog.
- Independent Euclidean-distance calculations agree with the proximity scores.
- A controlled case confirms a relevant remote-work career outside the old first
  150 neighbors can now enter the final results after contextual reranking.
- The original homepage HTML element structure and green palette were retained.
- The complete SQLite file was compared byte-for-byte with the uploaded ZIP and
  preserved: 28 current feedback logs, 19 summary groups, seven quiz attempts,
  923 occupations, three reference tables with 923 rows each, and 369 legacy events.
- Backend timing measurements and limitations are in performance_update.md.

Tests ran on Linux/Python 3.12 with Chromium viewport emulation. Windows packaging
uses ordinary ZIP deflate and portable source files. No physical-device or formal
recommendation-accuracy validation is claimed.


## Direct searches and PH salary update — 2026-10-31

- All 34 automated tests pass. These cover the retained assessment/ranking/session
  behavior plus direct-search markup, retired reference-table migration, complete
  TESDA snapshot, local province lookup, salary provenance, missing-value handling,
  source-value round trips, median/amount validation and atomic import rollback.
- Desktop and 390px mobile Chrome flows completed without JavaScript errors or
  horizontal overflow. Confirmed remembered location after reload, clearing it,
  permission-denied manual fallback, direct college program/location query, and
  exact TESDA course/location filters.
- A separate fresh-browser flow confirmed the first TESDA button click obtains
  province via geolocation and navigates directly without an education modal.
  External destinations were intercepted for testing rather than depending on
  third-party page uptime or enrolling/submitting anything to a provider.
- The database passed SQLite integrity_check. Retired school/campus tables are
  absent. No retired hard-coded school name/link remains in any database field
  or database bytes after compaction.
- Original quiz_attempts, raw_feedback_logs and legacy_feedback_archive rows were
  compared with the uploaded database and preserved exactly.
- Salary coverage: 411 current Jobstreet PH role matches, 116 historical PSA
  occupation-group matches, 396 explicitly unavailable. Related-role mappings
  remain advisory; this is not a measured recommendation-accuracy result.

## Career-card refinement — 2026-11-01

- All 36 automated tests pass. Added full career/catalog mapping coverage and
  specialist regression checks, plus evidence-sensitive explanation checks.
- Chrome verified no location bar or location lookup on page load/results render
  or program expansion. Each alternative uses its own program. Saved area is
  reused after reload; cancelling the native location prompt does not navigate.
- Both denied-permission/manual-entry and real browser-geolocation flows reach
  direct TESDA results with the correct course and Cavite location filters.
- Related salary values remain in collapsed comparisons; exact advertised pay
  and unavailable-reference search states render separately.
- Desktop and mobile screenshots were reviewed. No page errors or horizontal
  overflow at 320, 360, 390, 430, 768 and 1440 CSS pixels.
- College snapshot: 1,395 labels/variants (676 official-list/registry and 719
  classification examples); 1,896 exploratory associations across 923 careers.
  Catalog size and test coverage do not establish national completeness or
  validated career/qualification accuracy.
- Current assessment-history, raw-feedback and legacy-feedback rows were compared
  with the original uploaded database and preserved. SQLite integrity_check passes.

External destinations were intercepted during browser tests. Live provider
availability, search-result ordering, campus admissions and enrollment were not
validated or submitted. ML weights and assessment questions are unchanged.
