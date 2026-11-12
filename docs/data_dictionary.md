# Data dictionary

The application reads career mappings and salary references from SQLite. Editable
CSV sources are in `data/reference/`. After edits run:

```sh
python manage.py import-reference-data
```

The three canonical imports are validated and committed atomically. Each file has
one row per `onet_code`, stored as text. `occupation_title` is an editor aid, not
the join key. Do not replace an O*NET code with a course or qualification ID.

## Shared fields

| Field | Meaning |
| --- | --- |
| onet_code | Occupation key, e.g. 15-1252.00. |
| occupation_title | Human-readable title for editing. |
| country | PH for these references. |
| data_status | curated, verified, unavailable; legacy_estimate is accepted only for older imports. |
| source_url | HTTPS evidence URL; mandatory for verified/sourced salary records. |
| reviewed_on | ISO review date, YYYY-MM-DD. |

Verification metadata records the source review. It does not automatically establish
admission eligibility, job licensing, salary equivalence or model accuracy.

## Degree and training mappings

- `college_programs.csv`: `programs` contains exact degree names separated by ` | `.
- `tesda_programs.csv`: `qualifications` contains exact qualification names separated
  by ` | `. No guessed training duration or availability is appended.
- Blank mappings remain explicitly unmapped. College buttons can search related
  courses from the career title; TESDA buttons require a named qualification.
- `program_catalog.csv`: CSV validation/source catalog of official-list names and
  aliases. It is not stored as a program/campus SQL directory. When present during
  import, every nonblank mapping must refer to a name of the correct kind.
- `tesda_official_programs.csv`: complete 659-record source-list snapshot, with
  list type, listed/superseded status, individual document URL and review date.

These occupational-family degree/training suggestions require local expert review.
The full official TESDA snapshot and its 597-name active/unmarked catalog are
explained in `program_search.md`.

## Salary references

| Field | Meaning |
| --- | --- |
| min_amount / max_amount | Published P25/P75 for advertised-pay distributions, or minimum/maximum of industry-specific survey averages. See measure. Blank when unsupported. |
| median_amount | Published median for Jobstreet distributions, blank for PSA industry means. |
| currency / period | PHP / month for sourced records. |
| experience_level | mixed; no unsupported entry-level claim. |
| source_occupation | Actual PH role/group being used for comparison. |
| source_name | Publisher, e.g. Jobstreet PH or PSA Occupational Wages Survey. |
| reference_year | 2026 snapshot year for current publisher pages; 2022 survey year for PSA occupational data. |
| measure | advertised_p25_p75, industry_average_span, survey_average, unavailable; legacy_estimate only for compatibility. |
| match_type | exact normalized title, related-role proxy, or unavailable. |
| mapping_note | Scope, source period and matching limitations. |
| source_count | Number of source distributions/industry observations, not a Jobstreet job-ad sample count. |

Positive finite amounts and median ordering are validated. Unsupported records
must not contain fabricated zeros or default wages. The importer formats the
measure/year into `salary_display`; no amount is embedded in UI JavaScript.
Source links and role labels are shown on result cards.

`salary_crosswalk.csv` exposes each assignment and its rule. Raw extracted facts,
source metadata, current coverage counts and the PSA source tables are in
`data/source/ph_salary/`. See `salary_sources.md` for provenance and the distinction
between advertised distributions and older industry-average spans.

## O*NET and database compatibility

`occupation_catalog.csv` stores the occupation code, title, description, job zone,
remote-work metadata and six 1–7 numeric RIASEC dimensions. It contains no pay or
program fallbacks. `data/source/onet/` retains the user-supplied raw source files;
the rebuild command uses OI numeric ratings. Ranking weights are unchanged.

The original `college_programs`, `tesda_programs` and `salary_ranges` SQL tables
remain authoritative. The legacy occupation display columns `college_majors`,
`tech_voc`, `salary` are synchronized during imports so DB viewers do not see old
contradictory values. The recommendation engine still reads the canonical tables.

The retired school/campus, campus-offering, program-registry and discovery-cache
SQL tables are removed on schema initialization. Assessment history, raw feedback
and archived feedback are preserved. Existing historical response snapshots remain
historical records, not current salary sources.

## Expanded college evidence

`college_program_catalog.csv` mirrors college rows in `program_catalog.csv`:
1,395 program labels/variants, not 1,395 verified current degrees. `source_status`
is `official_listed` (676) or `classification_listed` (719). National PSCED
classification examples do not demonstrate current campus availability.
`college_program_evidence.csv` retains 4,709 source observations;
`college_pathway_audit.csv` records 1,896 exploratory associations across all 923
careers, including the selected rule, source status and study/eligibility caveat.
The actual `college_programs.csv` rows remain one per occupation with pipe-separated
names, imported into the existing SQL mapping table. Broad family associations
are exploratory study options, not independently validated qualification routes.
See `program_search.md` for scope, sources and rebuild instructions.
