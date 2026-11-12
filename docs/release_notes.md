# Direct-search and sourced salary update

- Removed the education modal and stored school/campus directory.
- Direct TESDA links use the suggested qualification and remembered location.
- Direct college links search for the suggested degree near the selected area.
- Exported all 659 official TESDA TR/CS list records, including status labels.
- Expanded the active TESDA catalog to 597 distinct titles.
- Replaced generic salaries with exact or related PH source-role references.
- Preserved assessment/feedback history and recommendation weights.
- See `program_search.md` and `salary_sources.md` for setup and source coverage.

# Release changes

- Removed career saving UI, JavaScript, HTTP routes, and fresh-database table creation.
- Added top scrolling for step changes, results, pagination and retakes, plus a floating top button.
- Expanded the interests step from six to 12 questions; equal averaging of two items per RIASEC trait.
- Corrected profile scale comparison by normalizing questionnaire and O*NET rating ranges.
- Added career-specific explanations from occupation profiles/descriptions and user inputs.
- Added three editable reference CSVs, each with 923 occupation mappings and provenance/status fields.
- Separated occupation evidence, CSV import, scoring, ranking, explanations and feedback services.
- Added professional entry points: `manage.py`, `serve.py`, `wsgi.py`, `development_server.py`.
- Renamed browser scripts by responsibility and moved ML code under `app/recommendation/`.
- Added Waitress, health checking, container configuration, environment examples and deployment docs.
- Preserved existing quiz attempts, feedback and archived legacy events. No cloud publishing performed.

## Renamed commands

| Previous command/file | Current command/file |
| --- | --- |
| `python init_db.py` | `python manage.py initialize-database` |
| `python update_summary.py` | `python manage.py refresh-feedback-summary` |
| `python run.py` | `python serve.py` (production) |
| `python -m ml_engine.view_stats` | `python manage.py show-statistics` |
| `ml_engine/predictor.py` | `app/recommendation/engine.py` |
| `app/static/js/app.js` | `app/static/js/assessment.js` |
| `app/static/js/results.js` | `app/static/js/career-results.js` |

Keep an earlier release folder as a backup instead of copying these files over it.
