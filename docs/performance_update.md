# Calculation and runtime update

## What changed

- Reuse a fitted scikit-learn NearestNeighbors index while actual database catalog
  contents remain unchanged. Cache up to four catalog snapshots in memory.
- Match selected-skill keywords once per skill and catalog version, using compiled
  whole-word expressions. Prepare skills only when users select them.
- Calculate education/goal/skill/feedback adjustments with NumPy arrays.
- Consider all 923 occupations before final reranking. The old first-150 cutoff
  could exclude a stronger match for the user's goal or skills.
- Sort using full-precision scores before formatting display numbers, with stable
  tie-breaking by interest proximity and occupation code.
- Generate detailed explanations only for the final 30 results.
- Deduplicate selected skills so a repeated skill cannot inflate its score.
- Read community feedback fresh on each request. New votes do not require refitting
  the career index; changes to imported catalog/reference rows invalidate it.
- Render result cards with one DOM update, rather than repeatedly reparsing cards.
- Use a local system font instead of waiting for a third-party font stylesheet.

## Local benchmark

Measured against the engine from the user's uploaded ZIP, using its 923-occupation
SQLite database in read-only mode. One profile with two selected skills; three
warmups and 30 measured calls per engine, in the same Python process.

| Backend calculation | Median | 95th percentile |
| --- | --- | --- |
| Uploaded version | 17.861 ms | 19.735 ms |
| Updated, warm cache | 6.648 ms | 7.155 ms |

Updated first/cold call: 20.466 ms, after Python imports.
Warm median speedup: 2.69×.

These measurements cover the recommendation function, not Python startup, a full
HTTP request, browser rendering, internet latency, or every possible profile. They
were measured on Linux/Python 3.12 and are not promises for another device.

## Calculation limits

The model remains nearest-neighbor similarity matching with fixed adjustments.
The two questionnaire items per RIASEC category are still equally averaged. The
normalization and goal/education/skill/feedback weights are retained. Final rankings
can differ because all occupations are now eligible for contextual reranking and
sorting no longer loses precision before selection.

The update fixes selection/calculation behavior and reduces repeated computation.
It does not establish improved predictive accuracy, validate the questionnaire, or
turn the model into supervised/self-training ML. Scores remain guidance scores,
not probabilities of career success. Reference salary/program estimates retain
their existing status.

Primary implementation references:
https://scikit-learn.org/stable/modules/generated/sklearn.neighbors.NearestNeighbors.html
https://scikit-learn.org/stable/modules/neighbors.html
