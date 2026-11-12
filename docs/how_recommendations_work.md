# How ALS-Gabay selects career suggestions

This document describes the code delivered in this package. The implementation is an interest-based nearest-neighbor recommender with explicit ranking rules. It is not a classifier trained on ALS learners' eventual career outcomes, and its scores are not probabilities of success or measured accuracy.

## Inputs and matching

1. The learner answers 12 local interest questions, scored from 1 to 5. There are two questions for each RIASEC interest: Realistic, Investigative, Artistic, Social, Enterprising, Conventional. Each pair is averaged. Source: app/services/assessment.py and data/reference/assessment_questions.json.
2. The six averages are normalized to 0–1 using `(rating - 1) / 4`. Each career's six stored O*NET interests, originally on a 1–7 scale, are normalized using `(rating - 1) / 6`.
3. scikit-learn NearestNeighbors compares the learner's six-dimensional vector with every career in the database, using Euclidean distance. Lower distance means a closer interest profile. The candidate list is not cut off before contextual ranking.
4. Interest proximity is `100 × max(0, 1 - distance / sqrt(6))`. The largest possible distance between these two six-dimensional normalized vectors is `sqrt(6)`. This is a similarity calculation, not a validated percentage of career suitability.

Implementation: app/recommendation/engine.py, _prepare_catalog and recommend_career.

## Contextual ranking

The default ranking value is:

`0.8 × interest proximity + goal adjustment + skill adjustment - preparation penalty + feedback adjustment`

| Component | Delivered behavior |
| --- | --- |
| Interests | Uses all six interests, not just the highest one or two. |
| Selected skills | +4 per supported phrase match, capped at +12. Exact evidence-bearing phrases and simple plural forms are matched in the career title or duties. Generic words such as assistant, data, support, and worker alone no longer trigger skill credit. This remains a limited phrase matcher, not a verified ability assessment. |
| College goal | +5 for Job Zone 3–5 careers. No penalty based on the learner's present education, because this is exploration of future study. |
| Vocational goal | Only careers with a mapped TESDA qualification enter this goal's results. +6 for those in Job Zones 1–3. Zone 4–5 careers include a preparation note explaining that a related qualification may build supporting skills without qualifying someone for the full profession. |
| Immediate workforce goal | +5 for Job Zones 1–2. Preparation adjustments remain; the result is still guidance, not a job-eligibility determination. |
| Remote-work goal | +12 for careers marked remote-capable; -25 for careers marked on-site in the existing catalog. These flags are curated and have not been independently validated for current Philippine employers. |
| Preparation | Outside the college goal, a career beyond the configured preparation zones receives -15. Elementary: zones 1–2; Junior High: 1–3; Senior High: 1–4; Exploring: 1–5. A higher education choice no longer penalizes zone 1 careers. Job Zones are broad O*NET preparation groups, not Philippine admissions or licensing rules. |
| Community feedback | Existing same-goal/top-two-interest-group feedback adds `1.5 × net_score_boost`, limited to -10 through +10. It is an explicit heuristic and does not retrain the nearest-neighbor model. Feedback is excluded in offline weight evaluation. |
| Salary | No effect on ranking. Salary is a secondary reference below TESDA. |

The system sorts by the full ranking value, then by interest proximity and occupation code to make ties deterministic, and returns up to 30 careers. For vocational exploration, fewer may be returned if the database has fewer than 30 mapped careers. The API preserves the internal display score for compatibility, capped at 98.5; it is not a calibrated probability and is not displayed as an accuracy claim on the cards.

The API's `ranking_factors` object records interest, skills, matched skill names, goal, preparation, and feedback components for inspection. Program and salary metadata are joined by the selected career's occupation code. Neither source-link availability nor salary changes the rank.

## What changed in this update

- Removed broad-word skill matches that could connect unrelated careers to caregiving, coding, hardware, or selling.
- Allowed simple plural career titles to match their corresponding specific role phrases.
- Removed the current-education penalty for future college exploration.
- Required an actual mapped TESDA qualification for the vocational goal.
- Kept low-preparation careers available without penalty to senior-high learners.

These are testable ranking corrections, not proof of a measured increase in real-world relevance. The existing nearest-neighbor method and numeric ranking weights are retained.

## What would establish accuracy

No reviewed ALS learner/expert relevance dataset was supplied with this request. A higher accuracy rate cannot be confirmed. The 12-question local instrument has not been established as equivalent to O*NET's published 30- or 60-question Interest Profiler instruments.

Have ALS learners and guidance counselors review candidate careers against representative profiles. Keep development participants separate from held-out test participants, compare Precision@5 and nDCG@5, and report reviewer disagreement and group coverage. Use the existing evaluate_weights.py workflow in docs/recommendation_validation.md. The example profiles are demonstration data, not validation evidence. Regression tests check implementation behavior; they do not measure career satisfaction, employment outcomes, or psychometric validity.

## Primary technical references

- scikit-learn NearestNeighbors: https://scikit-learn.org/stable/modules/generated/sklearn.neighbors.NearestNeighbors.html — describes unsupervised neighbor search.
- O*NET Interest Profiler: https://www.onetcenter.org/IP.html — describes the six occupational interests and the published instrument formats. This does not validate the local 12-question adaptation.


## Education question in plain language

The system does consider the selected education level, but it does not search a verified Philippine education requirement for each job. It uses broad preparation zones as a ranking preference. Elementary selection favors zones 1–2; junior high favors 1–3; senior high favors 1–4. Careers outside those groups receive a penalty rather than being strictly excluded. These zone groups are app heuristics, not school-grade equivalencies or guarantees of employer acceptance.

For college exploration, the current-education penalty is intentionally absent: the career is something to prepare for through future study. That does not establish present admission eligibility. For TESDA, a suggestion must have mapped related training, but the program may have its own entry requirements. For work or remote work, each employer's listing still needs to supply its actual education, skills, and experience requirements.

A primary card button now opens the next step for the selected plan: college search, TESDA training-center search, Jobstreet job search, or OnlineJobs.ph remote search. These actions navigate to searches; they do not submit applications.


## Career content in this older-UI merge

The original **Why This May Suit You** function is retained unchanged. It combines
fixed activity phrases, the occupation's stored O*NET description, interest
scores, selected matching skills, and preparation guidance. It is deterministic,
not generated by a language model. The API also retains source-evidence fields
for compatibility; the old cards render `fit_reasons`.

Location is requested in a dialog when the existing college/TESDA search button
is clicked. Location affects external searches only, not career ranking.
