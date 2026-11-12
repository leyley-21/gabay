# Philippine salary references

The old generic salary assignments are replaced by sourced Philippine role
references. All 923 occupation rows remain present. **527** have a matched
reference: **411** use current Jobstreet PH role distributions and **116** use
PSA occupational wage observations. **396** have no defensible match and display
an unavailable message instead of a made-up wage. Exact normalized title matches
number **72**; **455** are explicitly labelled related-role proxies.

## Sources and what the numbers mean

### Jobstreet PH: 204 source roles, checked 2026-10-31

Source pages follow `https://ph.jobstreet.com/career-advice/role/<role>/salary`.
Each record retains the actual role name, source URL, retrieval date and original
page SHA-256. Values come from the page's public JSON-LD
`Occupation.estimatedSalary`, only where currency is PHP and duration is P1M.

- `min_amount` is the published 25th percentile.
- `max_amount` is the published 75th percentile.
- `median_amount` is the published median.
- The app labels the range **middle 50% of advertised pay**.

These are full-time salary-disclosed job-ad distributions, not minimum and maximum
salaries for all Filipino workers. Experience is mixed. Some advertised pay includes
benefits and some does not. The data is national, not adjusted to the learner's
city/province. A current page snapshot is not a guarantee that its underlying
observations all come from October 2026. No job-ad count or statistical confidence
is invented; `source_count=1` identifies one published distribution, not one job ad.

### Philippine Statistics Authority: August 2022 occupational data

Source: https://psada.psa.gov.ph/catalog/315/related-materials
Download: https://psada.psa.gov.ph/catalog/315/download/2379

Table 1 provides published monthly average wages for occupation/industry cells in
formal establishments employing 20 or more workers. The bundled extraction retains
513 numeric industry/occupation observations across 192 distinct PSOC codes. Those
codes are not equivalent to the number of occupations described in PSA's survey.
The source PDF is included with the extracted facts and page references.

For a matched PSOC group with several numeric industry observations, the displayed
range is the **minimum and maximum of industry-specific average wages**. It is not
the pay distribution of individual workers and is never labelled as entry-level
pay or a current salary offer. One industry observation is displayed as one survey
average. Figures remain nominal August 2022 pesos: no inflation adjustment or
conversion to current regional wages is assumed.

The newer 2024 PSA industry/benchmark workbook is retained as context. Its industry
averages are not assigned indiscriminately to all occupations. Newer occupation-
specific facts may be added when they can be sourced with the same precision.

PSA attribution: Philippine Statistics Authority, 2022 Occupational Wages Survey,
Statistical Tables, Table 1. Adapted extraction and occupational crosswalk.
PSA website data are CC BY 4.0 unless otherwise stated.

## How salaries are assigned

1. Prefer a current PH source role with the same normalized occupation title.
2. Use an explicit occupational-family rule for a defensible related PH role,
   labelled **Related PH role** in the result card.
3. When the named current source role has no available distribution, use a
   specifically matched PSA occupation group if one exists.
4. Otherwise keep amounts blank and show **No matched Philippine salary reference
   yet**. Never substitute zero, a national average, or the previous generic band.

`data/reference/salary_crosswalk.csv` exposes every target occupation, selected
source identifier, source role, mapping rule, match type and limitations. Related
mappings are advisory and need local expert review; a similar role is not proof
of equivalent duties, qualifications, seniority or pay. No arbitrary fuzzy score
is presented as accuracy. Manually reviewed overrides can be made in the CSVs.

Salary figures appear in a small disclosure summary below the TESDA section, with a visible qualifier for a related-role proxy or historical source. The salary dropdown contains the source occupation, median when published, measure, year, last check date, source link, and limitations. A historical span is a range of industry averages, never an entry-level band. Missing references show unavailable plus a current PH salary-search link. Location is used for education searches; it does not silently change national salary figures. These reference figures do not change ML ranking weights.

## Files

- `data/reference/salary_ranges.csv`: one row per O*NET occupation, amounts and
  explicit source/basis/matching metadata. Unsupported amounts are blank.
- `data/reference/salary_crosswalk.csv`: human-readable audit of each assignment.
- `data/source/ph_salary/jobstreet_ph_snapshot.json`: extracted distribution facts
  from 204 publisher pages, not copied page descriptions.
- `data/source/ph_salary/psa_ows2022_observations.json`: raw occupation/industry
  observations with source PDF page numbers.
- `data/source/ph_salary/psa_ows2022_tables.pdf`: official published tables.
- `data/source/ph_salary/psa_ows2024_context.xlsx`: newer broad industry and
  benchmark context, not a replacement for missing occupation-specific wages.
- `data/source/ph_salary/sources.json`: methodology, URLs and integrity hashes.
- `data/source/ph_salary/coverage.json`: exact coverage counts for this release.

`tools/rebuild_salary_references.py` reproduces salary mappings from the bundled
facts. It replaces mapping CSVs, so preserve any custom overrides first. It does
not fetch pages during normal app use or pretend to update salaries automatically.

After editing reference CSVs, run `python manage.py import-reference-data`.
Imports validate positive finite amounts, median ordering, PHP/month basis for
sourced records, publisher/role/year/URL metadata and missing-data rules. The
three canonical reference tables update atomically. Historical occupation display
columns are synchronized to avoid contradictory old wages in database viewers.

Coverage and proxy mappings have not been independently validated as a complete
national salary study. The exact crosswalk makes later expert corrections possible.
