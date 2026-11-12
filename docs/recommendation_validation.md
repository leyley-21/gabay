# Recommendation protection and weight evaluation

The website remains anonymous. No login, profile or saved-results screen was added.
The 12 questions still provide two answers per RIASEC category. Each pair is averaged;
all six scores drive interest matching. The top two traits identify feedback groups.
This implementation does not establish the questionnaire's measurement reliability.

## Protection and deployment

- The server issues a signed, HttpOnly, SameSite=Lax anonymous cookie. Client-supplied
  session IDs are ignored. Each write requires a CSRF token from the rendered page.
- Feedback must reference an assessment issued to that session and a career in that
  assessment's recommendations. Goal, education and RIASEC feedback grouping come
  from that assessment, not user-supplied profile fields.
- SQLite request budgets are shared across threads/processes using the same database.
  Defaults: session creation 120 per IP per 10 minutes; predictions 12 per session and
  60 per IP per minute; feedback 40 per session and 180 per IP per minute.
  Rejections return HTTP 429 and Retry-After. IPs are stored as keyed hashes.
- These controls reduce manipulation; they cannot prove one human per session or stop
  a distributed botnet. Shared school/mobile networks can hit the IP budget together.
  Adjust budgets in `app/services/security.py` using observed legitimate traffic.
- Forwarded IP headers are deliberately not trusted. Behind a reverse proxy, configure
  Werkzeug ProxyFix only for the exact trusted proxy hop count and prevent direct access
  to the backend, or apply per-client limits at the edge. Otherwise the backend limits
  may group visitors by the proxy's IP.
- Set a stable, private `GABAY_SECRET_KEY` and `GABAY_COOKIE_SECURE=1` on HTTPS hosting.
  Local HTTP development works without the Secure flag. If no key is supplied, the app
  creates `.session-secret` beside the database; keep it private and persistent, and
  share the same key across workers. Never commit or distribute a deployment's key.
- Schema migrations run at startup without deleting existing history. Back up the
  database before deployment. Existing unsigned browser IDs are no longer accepted;
  historical records remain stored but do not confer a new session identity.
- Anonymous HTML is `no-store` because it contains session-specific CSRF data.
  Images, CSS and JS retain versioned browser caching.

## Duplicate prevention and efficient feedback

The browser assigns one random submission ID per unchanged assessment submission.
Retry reuses that ID; retaking or changing the payload creates a new one. The backend
stores the result and history atomically. Concurrent retries return the same result,
without another history row. Reusing an ID for different answers returns HTTP 409.
IDs survive retry clicks within the open page, not browser refreshes or device changes.
A retry deliberately returns the original result even if feedback has since changed.
Stored responses are internal records, not a user-facing saved-results feature.

Feedback recalculates only the affected career, goal and RIASEC groups, including the
old group if a vote changes profiles. The full rebuild remains an administrative
repair/import operation. Repeated votes from the same anonymous session remain deduplicated.

## Ranking scores

The displayed `Ranking score: x/100` is the bounded score used to help order suggestions.
It combines interest proximity, goal and skill adjustments, education penalties, and
community feedback. It is not a probability, accuracy measurement, or prediction of
career success. The existing score cap and default ranking formula remain unchanged.

## Offline weight evaluation

No settings are trained, validated or deployed automatically. `evaluate_weights.py`
compares the current formula with interests-only, stronger-context and lighter-context
settings using actual reviewer judgments. It has no effect on live requests and opens
its database read-only. Community feedback is disabled equally for every setting to
avoid using evaluation votes as ranking evidence.

1. Copy `data/evaluation/profiles.example.json` into a research dataset. The supplied
   profiles are fictional format examples, not evaluation evidence. Replace them with
   consented, coded profiles. Do not include names. Assign participants to `development`
   or held-out `test`; one participant cannot appear in both.
2. Export a pool containing every career in the top five of any candidate setting:

   ```sh
   python evaluate_weights.py --profiles data/evaluation/profiles.example.json --export-pool /tmp/review_pool.json
   ```

3. Have reviewers assess the careers against each profile, preferably without seeing
   the setting or score. Add judgments to each profile's `ratings` object, keyed by
   occupation code: `0` irrelevant, `1` somewhat relevant, `2` relevant, `3` very relevant.
   Rate the whole exported pool. Keep learner judgments and expert judgments in
   separate datasets rather than silently combining them. No website login or dashboard
   is needed. After export, freeze the catalog and candidate settings for this evaluation.
4. Generate a comparison:

   ```sh
   python evaluate_weights.py --profiles /tmp/review_pool.json --output /tmp/weight_comparison.json
   ```

The report includes participant-profile counts, per-profile and average Precision@5
(ratings 2 or 3 count as relevant), and graded nDCG@5. The nDCG ideal is calculated
within the reviewed pool, not the whole catalog. Missing top-five judgments are
rejected rather than treated as negative. nDCG is undefined when every pool rating
is zero. Separate development/test results are mandatory.

Use development data to choose settings and inspect held-out results only after that
choice is fixed. The tool prints all settings for transparency; do not select weights
using the test results. Averages alone do not establish statistical superiority;
use enough representative learners, report uncertainty and reviewer disagreement,
and check outcomes across education/goal groups. Repeated profiles from one person
are not independent participants. Dataset and occupation-catalog hashes identify runs.
Local course/pay mappings and the questionnaire require their own review.

The script never changes production weights. Only change `DEFAULT_WEIGHTS` after
reviewing evidence, then rerun regression checks and monitor the deployed behavior.
