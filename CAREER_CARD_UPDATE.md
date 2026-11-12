# Source-only career descriptions and editable study search area — 12 November 2026

- Removed FIT_CONTEXT and its authored personal-fit phrases. The explanation builder now returns the stored O*NET occupation-description sentences in source order, with no synthesized fit explanation, interest-theme heading, or score tags. Compatibility API fields remain present but generated explanation strings are empty.
- Renamed Why This May Suit You to What this career involves. The section explains the career's work rather than claiming that source text establishes personal suitability. It links to the occupation-specific O*NET profile.
- The renderer ignores old cached fit-explanation strings and unsupported legacy fit_reasons. When structured evidence is missing, it can display the response's stored career description.
- Added a compact Study search area / Change control beside the results introduction. The city/province prompt is prefilled with the current choice. Updated choices also refresh program-name hrefs so opening links in a new tab uses the current area.
- Fixed first-use location searches replacing the assessment page. A tab is reserved during the click, then navigated after location resolution. Cancellation closes the empty tab. If popups are blocked, the area is saved and the user can select the program again; the assessment page stays open.

Verification: 44 Python tests and Node rendering/search checks pass. All 923 catalog descriptions match the bundled raw O*NET occupation descriptions. Checks cover source-only content, suppression of cached fit phrases, saved-area changes, nearby URLs, successful first-use search, cancellation, and blocked-popup recovery. Browser/device appearance is not visually verified in this environment.

Limits: O*NET career descriptions do not establish individual suitability or Philippine entry requirements. Automatic lookup resolves a province, not a city or nearest campus. College links are Google searches; TESDA links submit the mapped qualification and location to TESDA's registered-program directory. Neither the app's search link nor the model verifies current campus offerings or calculates campus distance. See docs/location_and_career_content.md for next improvements.

Restart the server and refresh after applying the update.

---

Earlier history follows; latest source-content and search-area descriptions above supersede earlier fit templates and search behavior.

# Shared home typography and clickable study names — 12 November 2026

- The specified home-screen paragraph uses 1rem text, regular 400 weight, and a 1.625 line height. Those values are now shared CSS variables used by that paragraph and card body text, links, field labels, salary details, and controls. Career and section headings retain their hierarchy.
- College program and TESDA qualification names are now the actual nearby-search links. An inline arrow follows the name, and the separate Find schools/Find training action row is removed.
- Every alternative in a program dropdown has its own linked name and search destination. Searches use the saved location, or the existing optional location/manual-city flow when the user activates a name without a saved location.
- Source/reference information remains available through the small line icon and its hover/focus/tap help. The plain program dropdown chevrons remain separate controls.
- Used the supplied image as a reference for clear typography and uncluttered link treatment; no employer data, logos, job descriptions, or structure were copied into the app.

Verification: JavaScript syntax and Node card-rendering checks pass. Added checks verify linked names, arrows, removal of duplicate search controls, program-specific college/TESDA destinations using a saved location, and the actual nearby-search handler. Tooltip, salary, escaping, pagination toggle, and primary-action checks remain passing. Live browser visual verification remains unavailable in this environment.

Restart the server and refresh after applying the update.

---

Earlier update history follows; the latest descriptions above supersede previous typography sizes and separate study-action labels.

# Smaller program controls and source help — 12 November 2026

- Reduced the visible size of Find schools/training controls and removed their filled backgrounds and borders. Source controls now use a small document line icon instead of the boxed information-circle design.
- Added source help that opens on pointer hover or keyboard focus. A tap/click keeps it open; another tap/click, an outside interaction, or Escape closes it. The help explains the reference and offers an explicit Open reference link, so touching an unfamiliar icon does not immediately navigate away.
- Source help is positioned within the viewport. Native popovers place it above card clipping; older browsers use a fixed-position fallback. Open help closes on scrolling, resizing, pagination, and assessment reset.
- Removed the circular backgrounds from both college and TESDA dropdowns. The darker chevron remains visible, rotates on expansion, and retains a keyboard focus outline. Touch controls retain invisible padding.
- Modestly reduced program and detail text, title size, and vertical spacing while retaining the established card design.

Verification: JavaScript syntax and Node rendering checks pass. Behavioral checks cover hover/focus preview, first activation pinning, second activation dismissal, native close synchronization, viewport placement, and the fallback. These are logic checks, not live-device visual verification. The existing limitation on preview access remains.

Restart the server and refresh to load the updated asset versions.

---

Earlier update history follows; latest descriptions above supersede earlier control sizes and source-link interactions.

# Small card refinements and remote-search repair — 12 November 2026

- Removed A closer look from the expanded section.
- Replaced the three repeated study actions with one Find schools/Find training button and one accessible information icon linking to the original program/qualification source. The search button uses the existing remembered-location or optional location-selection flow. There is no separate Near me action.
- Previously, Find schools/training used a saved location when present, and Near me used that location or prompted for one. Those actions could therefore produce the same destination. Their behavior is now consolidated.
- Salary remains below TESDA. Its label, amount, optional related/historical qualifier, and dropdown arrow now have dedicated space instead of competing across a narrow line. Source details remain collapsed by default.
- Made small spacing, alignment, and button-font adjustments within the existing visual design.
- Main buttons are Find jobs, Find remote jobs, Find colleges, and Find training, without website names.
- Fixed the remote search query field: the clicked card's full career title is sent as jobkeyword, replacing keyword. The destination remains the job-search results route, with full-time/part-time/gig options enabled rather than a fixed job detail link.

Verification: Node card-rendering checks pass, including four different career-title queries, correct jobkeyword encoding, retained location searches, program dropdowns, simplified labels, removed eyebrow, escaped text, salary structure, and action buttons. JavaScript syntax checks pass. The official indexed OnlineJobs.ph search confirms jobkeyword usage: https://www.onlinejobs.ph/jobseekers/jobsearch?gig=on&isFromJobsearchForm=1&jobkeyword=developer&partTime=on . The exact combined search URL could not be retrieved by the lookup tool, so no live result count or complete result relevance is claimed. The existing environment limitation on browser visual verification remains.

Restart the server and refresh after applying the update. The recommendation model, career data, and salary figures were not modified in this refinement.

---

Earlier update history follows; the latest descriptions above supersede older link, label, and salary-layout descriptions.

# Career guide visual refresh — 12 November 2026

- Redesigned the career card and expanded details with a muted forest-green palette, warm gold accents, a stronger title hierarchy, and clearer spacing.
- Added an Explore this career control with a highlighted background and directional arrow. The open section uses a continuous numbered reading layout rather than nested information cards.
- Each fit explanation separates The work (the stored career duty) from Why it may fit (the existing conditional explanation). Theme headings, a subtle connecting line, and section icons make the longer content easier to scan.
- Work arrangement, the preparation note where applicable, the career-profile link, and feedback now have distinct visual hierarchy and consistent spacing.
- Retained readable main text, first-program links below their names, collapsed alternatives, salary below TESDA, and the four primary action buttons.
- Added a short opening transition with a reduced-motion alternative. No new libraries or image downloads are required.

Verification: existing Node rendering, escaping, disclosure, program-link, salary-placement, and four-action checks pass. The existing 44 Python tests pass. The preview browser could not access the local server; its policy also blocked the generated local review file. Desktop/mobile appearance has therefore not been visually verified in a browser in this environment.

Restart the server and refresh the page after applying the files so that the automatic asset versions pick up the new JavaScript and CSS. Keep any existing database with newer learner history, as described below.

---

Earlier update history follows; latest styling descriptions above supersede earlier styling notes.

# Readability and primary action buttons — 12 November 2026

- Card content now uses 16px-equivalent text, 15px-equivalent links and secondary labels, and 20px-equivalent titles at the default 16px browser root size. Relative rem units follow the browser's root text size.
- Primary action buttons and program arrows have larger targets. Long explanations, salary source details, and additional programs remain collapsed by default. Links remain under each program name, and salary remains below TESDA without a large bold amount.
- Restored the main action button for all four plans: Find Jobs on Jobstreet; Find Remote Jobs on OnlineJobs.ph; Find Colleges; Find TESDA Training Centers. The Jobstreet button now uses the current ph.jobstreet.com role-search URL format. The college and TESDA actions retain the existing nearby-study flow.
- Ranking behavior is unchanged in this readability update. Education affects broad preparation preferences outside the college goal; it is not a verified employer minimum-education filter. A higher-preparation job may still appear, and a recommendation is not proof of eligibility. College recommendations represent future study, so current education does not reduce their ranking.
- See docs/how_recommendations_work.md for the scoring steps, source files, limits, and the explanation of goal, interests, skills, preparation, and feedback.

Validation: 44 Python tests passed. Node rendering checks passed, including all four primary action destinations and the retained program-link/dropdown behavior. Live desktop/mobile appearance has not been visually verified in this environment. The existing OnlineJobs.ph destination was retained; its live page could not be retrieved by the web lookup tool.

---

Earlier update history follows; latest descriptions above supersede earlier typography and button-removal notes.

# Compact guidance cards and ranking corrections — 12 November 2026

## Latest changes

- The first college and TESDA program now has its links on a separate line below its name. An arrow alongside the name opens or closes additional programs. Every alternative has its own links underneath.
- Reduced card spacing and type size. Kept work-arrangement text and fit explanations inside More about this career; removed the duplicate bottom education-search button. Full information remains available on expansion instead of forcing a long default card.
- Moved salary below TESDA. The amount uses small, regular text in a collapsed source-details row; related-role and historical qualifiers remain visible. Salary never affects ranking.
- Corrected broad-word skill matches, added plural role matching, removed current-education penalties for future college exploration, required mapped TESDA options for vocational suggestions, and included zone 1 among preparation options for senior-high learners.
- Added auditable ranking components to the API and a detailed plain-language explanation at docs/how_recommendations_work.md. Numeric ranking weights were retained. No measured accuracy gain is claimed without reviewed learner/counselor data.

## Current verification

The Python integration and data tests and the Node card-rendering checks pass. Checks cover unrelated skill matches, future college exploration, TESDA pathway availability, salary-independent ranking, program dropdown toggles, salary placement, link ordering, HTML escaping, security, and learner-history behavior. Live desktop/mobile browser appearance remains unverified because the available preview browser could not reach the local server in the preceding update.

## Applying the update

The included database retains the uploaded learner history and the revised study references. For a new folder, follow README.md and install requirements in your local virtual environment.

For an existing installation with newer history, back it up, copy app/, data/reference/, tools/, tests/, evaluate_weights.py, and docs/, then run `python manage.py import-reference-data` and restart the server. Keep your existing database and session configuration. Generated virtual environments and Python caches are excluded from this package.

---

The following records describe the earlier data and layout update. The latest changes above supersede its layout and ranking descriptions.

# Career cards update — 12 November 2026

## Changes

- One outer career card, with simple rows and separators instead of an inner bordered card.
- Salary amount stays visible; the dropdown explains the source role, measure, median where available, reference year, last check date, and limitations. Related-role estimates and historical PSA averages are labelled. Unsupported pay stays unavailable; no wages have been invented or inflated.
- The first college/TESDA option has visible school/training search links. More options expand below it. Program-source links lead to the included registry or qualification evidence. School searches are discovery links, not verified current campus offerings. Nearby searches retain the existing optional location flow.
- Removed both requested results-page notes.
- Expanded or corrected college mappings for 189 occupations and TESDA mappings for 174 occupations. All 923 careers retain a college study mapping; 292 have related TESDA training mappings. NC and Level designations are preserved exactly. A vocational qualification is not forced onto a career without a supported related mapping.
- Added programming/Web Development qualifications for software/web roles; replaced generic contact-center training for marketing roles with digital-marketing options; removed contact-center training assigned to chief executives. More trade progression options are available where listed in the included official TESDA catalog.
- Career-fit sections explain actual career duties and the kind of work someone may enjoy, with fuller conditional explanations. They display no exam results, scores, ratings, or inferred claims of ability. Different supported work themes are selected without repeating the same explanation within a card.
- Work arrangement appears once per card. Career-specific guidance replaces the old generic degree exemptions, internet-speed requirements, and identical headset descriptions. Remote availability remains conditional on employer and assignment; the existing catalog's remote-capability flags have not been independently revalidated.
- Recommendation ranking is unchanged. College programs, TESDA options, and salary references are joined to the selected occupation code; fit text uses that occupation's stored duties. Registry metadata supplies source links, not generated recommendations.

## Data scope and sources

New program additions use exact existing names marked official_listed in the included registry. Earlier mappings retained outside the revised rules can include national classification examples. The source status accompanies program options in the response. Occupational relevance is a curated association, not an official equivalency or licensing decision. Not every career reasonably has multiple college degrees or a TESDA substitute.

- CHED Region III program registry: https://region3.ched.gov.ph/resources/program-registry
- Other included degree evidence: https://chedcar.com/program-and-discipline-code/ and https://ro11.ched.gov.ph/programs-inventory/
- TESDA qualifications: https://www.tesda.gov.ph/download
- O*NET duty evidence: each result links to its occupation-specific career profile.
- Salary provenance: see data/reference/salary_ranges.csv and docs/salary_sources.md. The existing salary figures were retained; this update improves their presentation and interpretation, not their freshness. Source-role links remain available in each salary dropdown.
- Mapping audit: data/reference/career_pathway_audit.csv records program sources and editorial mapping rules. tools/refine_career_paths.py reproduces the revised mappings from bundled sources without inventing missing titles.

## Running this version

The included database has the updated reference tables and retains the uploaded learner history. Start using the existing README instructions. Generated virtual environments and Python caches are excluded from the package; install requirements in your local environment.

To apply to an existing installation with newer learner history, back it up, copy the updated app/, data/reference/, tools/, and tests/ files, then run:

```bash
python manage.py import-reference-data
```

Keep your existing database and session configuration. Restart the server after applying the update so its program metadata cache and static asset versions refresh.

## Earlier validation

39 Python integration/data tests pass, including all 923 career explanations, source membership, occupation-specific training corrections, salary integrity, ranking, history, and security behavior. The Node career-card checks pass, covering visible salary amounts, expandable options, actual search links, missing salary behavior, explanation rendering, and escaping.

The automated browser regression could not launch Chromium in this environment (socket permission error). The separate preview browser could not reach the local server, so desktop/mobile visual and live interaction checks remain unverified. These limitations do not affect the passing backend and rendered-markup checks.
