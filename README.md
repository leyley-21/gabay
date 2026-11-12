# ALS-Gabay

## Older UI with merged improvements

This version uses the uploaded older UI. Its card CSS, **Why This May Suit You**
function and **Career Details & Next Steps** markup are preserved. New images,
logos, ALS education labels, Tagalog interest descriptions, radio-selection
scrolling and the prior backend improvements are included.

Programs and TESDA qualifications are plain text. The existing college/TESDA
button opens a program-and-location dialog on every click, including when a
previous search area is remembered. TESDA searches open its provider directory;
college searches open Google web search. These are searches, not verified nearest
campus/course matches. See [search behavior](docs/program_search.md).

Visible card salaries use stored Jobstreet PH advertised-pay references where
mapped. Related-role proxies are labeled. Missing Jobstreet matches show an
unavailable message; PSA figures and generic estimates are not substituted in
the card. These are dated references, not live offers or guaranteed earnings.
Salary cards show the amount and Jobstreet reference link; source methodology
remains in the linked reference metadata.

Unfinished assessment inputs and the current step are saved locally. Reloading
offers Continue Assessment or Retake Assessment. Successful completion clears
the draft. Remote searches use Jobstreet. Home-page reloads start at the hero.
See [merge and validation notes](REBASE_NOTES.md).

The expanded college catalog contains 1,395 sourced labels/variants, including
676 official-list/registry labels and 719 national classification examples. All
923 careers have exploratory study options. This is not an exhaustive live list
of accredited degrees or verified campus offerings; source status and mapping
rules are retained in the reference/audit CSVs.

The complete official-list snapshot includes 659 TESDA records, with 597 distinct
active/unmarked titles. Salary references now use 204 Jobstreet PH role snapshots
and published PSA occupational data; 527 careers have sourced exact or related
matches and 396 are explicitly unavailable. See [salary methodology](docs/salary_sources.md).

A Flask career guidance application with a 12-question RIASEC assessment, O*NET
occupation matching, career-specific fit explanations, and anonymous feedback.
Career saving has been removed from the interface and API.

## Download career cards as PDF

After completing the assessment, select **Download PDF** beside Retake Assessment.
The PDF includes all recommended careers across pagination, with program/training
lists, salary references, Career Details & Next Steps, and Why This May Suit You.
Source links remain clickable. Each career starts on a new A4 page; long details
continue onto the following page. The original website card design is unchanged.
The export uses the saved result and does not rerun matching or create a new
assessment. No external PDF service or browser extension is required.

Install the updated requirements before running this version (ReportLab is now
included). Optional backend test setup: `python -m pip install -r requirements-test.txt`.

## Install and run on Windows

Install **64-bit Python 3.12** and select **Add Python to PATH**. Python 3.11–3.13
is supported by the selected dependencies. Extract the ZIP, open **Command Prompt**,
and enter the folder containing this README. Do not run from inside the ZIP viewer.

```bat
cd als_gabay
py -3.12 -m venv .venv
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python manage.py initialize-database
python serve.py
```

If already inside `als_gabay`, skip `cd als_gabay`. If Python 3.12 is not installed,
use `py -m venv .venv` with another supported version.
Open **http://127.0.0.1:8080**. Keep the terminal open. Press **Ctrl+C** to stop.

For PowerShell, use `.\.venv\Scripts\Activate.ps1` for activation. If activation
is blocked, use Command Prompt or run `.\.venv\Scripts\python.exe` instead of
`python` without activating. No change to system execution policy is necessary.

## Install and run on macOS / Linux

```sh
cd als_gabay
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python manage.py initialize-database
python serve.py
```

On Debian/Ubuntu, install the OS package `python3-venv` first if venv is unavailable.
SQLite is included with Python. You do not need MySQL, XAMPP, Node.js, a model file,
or a separate database service. Package installation and external career links
need internet; CSS and homepage images are local. Google Fonts has system fallbacks.

## Start on later days

Activate the existing environment, then run:

```sh
python serve.py
```

You only need to reimport data after editing CSVs or upgrading this version's schema.
The normal server is **Waitress**, a production WSGI server that supports Windows
and Linux. `development_server.py` is a separate debug-only local entry point on
port 5000. Do not use that debug server for a live website.

## Management commands

Run all commands from the `als_gabay` folder with the virtual environment active.

| Command | Purpose |
| --- | --- |
| `python manage.py initialize-database` | Creates missing tables, seeds an empty occupation catalog, imports the three reference CSVs, and refreshes feedback summaries. Preserves assessment history and feedback. |
| `python manage.py import-reference-data` | Imports edited college, TESDA, and salary CSVs into the DB in one transaction. |
| `python manage.py import-onet-data` | Rebuilds the occupation catalog from the three raw O*NET CSVs. |
| `python manage.py refresh-feedback-summary` | Rebuilds community scores after manual feedback changes. Normal UI feedback updates them immediately. |
| `python manage.py show-statistics` | Prints database record counts. |
| `python -m unittest discover -s tests -v` | Runs integration tests against temporary databases. |

There is no required model-training command. The nearest-neighbor index is prepared from the current database and reused while
the imported career/reference data stays unchanged. New feedback is read on every
recommendation request.

`initialize-database` intentionally imports reference CSV edits. If you manage
those tables directly in SQLite, export your edits into the CSVs first, because
CSV import replaces their contents. It does not delete old occupation codes when
refreshing the occupation catalog, so historical references can remain intact.

## New assessment and recommendation behavior

Step 3 has **12 questions, two for each RIASEC trait**. The server requires every
answer and averages the two ratings in each category. It retains both the raw
responses and the resulting six averages in assessment history.

The questionnaire uses a 1–5 scale, while the supplied O*NET occupation interest
ratings use a 1–7 scale. Each is normalized to 0–1 before Euclidean nearest-neighbor
comparison. The ranking also considers selected skills, goal, preparation range,
and bounded community feedback. Suitability scores are not success probabilities.

The added questions provide more observations per category. This custom 12-item
questionnaire has **not** been psychometrically validated, and adding questions
alone does not establish improved prediction accuracy. Evaluate it with your
intended learners before making accuracy claims.

Every career's **Why This Fits You** explanation uses its O*NET RIASEC scores,
occupation description, selected-skill keyword overlaps, and preparation needs.
It also points out uncertain interests or a possible remote-work conflict.
These explanations are derived from the ranking inputs, not generated by an
external AI service. O*NET preparation zones are U.S. occupational descriptors;
they do not establish Philippine admission rules, licensing, or job eligibility.

Navigation to a new assessment step, results page, or retake scrolls back to the
top. Answer selection does not deliberately scroll the page. The bottom-right
arrow appears after scrolling down and returns to the top. Reduced-motion settings
are respected. Layouts adapt to mobile and desktop widths.

## Editable reference datasets

All three files are in `data/reference/` and match careers by **exact O*NET code**:

- `college_programs.csv`: college degree/program suggestions.
- `tesda_programs.csv`: qualification/training suggestions.
- `salary_ranges.csv`: minimum/maximum amounts, currency, pay period, and experience level.

Each has **923 occupation mappings** and source/status columns. Edit in a CSV
editor or spreadsheet application and save as UTF-8 CSV. Keep O*NET codes as text.
After edits, run `python manage.py import-reference-data` and refresh the browser.
You do not need to edit Python or JavaScript to change a program or pay range.
Missing mappings display an unavailable message instead of an invented fallback.

**Data quality:** degree/training mappings are advisory pathways using names from
official lists, not eligibility decisions. Salaries identify the PH source role,
year, measure and exact/related match. Advertised-pay percentiles are distinguished
from older PSA industry averages. Missing salary sources remain blank rather than
receiving a generic band. Read the source-methodology documents before making
recommendation-accuracy or salary-coverage claims.

## Use on a phone on the same Wi-Fi

Command Prompt:

```bat
set HOST=0.0.0.0
python serve.py
```

PowerShell:

```powershell
$env:HOST = "0.0.0.0"
python serve.py
```

macOS / Linux:

```sh
HOST=0.0.0.0 python serve.py
```

Find the computer's IPv4 address (`ipconfig` on Windows), then open
`http://YOUR-COMPUTER-IP:8080` on the phone. Both devices must use the same network.
Allow Python through the private-network firewall if prompted. Do not enter
`127.0.0.1` or `0.0.0.0` on the phone.

## Deployment and going live

The project includes a WSGI entry point, Waitress server, health endpoint,
Dockerfile, Compose file with persistent storage, and deployment documentation.
It has not been published to a hosting account or assigned a live URL.

Read [deployment instructions](docs/deployment.md) for Windows/Linux hosting,
Docker, persistent database storage, domain/HTTPS configuration, and upgrades.
The `.env.example` file documents supported environment variables; it is not
loaded automatically. Export variables in the shell or your hosting dashboard.

## Moving or upgrading an existing installation

Keep the old folder as a backup. Extract this version into a new `als_gabay` folder
instead of overlaying renamed files on the old project. Stop the previous server.
If you have added feedback or assessment history since the last download, copy
**your current `database/als_gabay.db`** into this version's `database/` folder
before initializing it. Back up both files first. Then recreate the environment,
install requirements, and run `python manage.py initialize-database`.

This adds reference tables and a raw-question-response column without deleting old
quiz attempts or feedback. Old attempts keep their six-score data and have no raw
12-question response data. Any historical bookmark table in an existing database
is left untouched for preservation, but no application feature or route reads it.
The bundled release database omits that unused, empty table.

The supplied database is preserved exactly from this upload: 28 current feedback
records, seven quiz attempts, and 369 archived legacy events. The archive has no
reliable user/session profile and is not used for profile-specific ranking.
For a brand-new live service, choose a **new database path** as described in the
deployment guide rather than publishing the bundled demo history.

## Backup and brand-new database

Stop the app before copying the DB. To preserve the current installation, back up
`database/als_gabay.db` and the reference CSVs. For a fresh DB, choose an unused path:

```powershell
$env:GABAY_DATABASE_PATH = "C:\GabayData\fresh.db"
python manage.py initialize-database
python serve.py
```

```sh
export GABAY_DATABASE_PATH=/absolute/path/to/fresh.db
python manage.py initialize-database
python serve.py
```

Use the same variable for **both management and serving commands**. Do not copy an
old virtual environment between devices; recreate it.

## Organized project layout

```text
als_gabay/
  app/
    config.py                 Shared paths and environment settings
    db.py                     SQLite connection management
    schema.py                 Safe schema creation/upgrades
    routes.py                 HTTP validation and endpoints
    recommendation/
      constants.py            RIASEC labels, skill keywords, education ranges
      engine.py               Normalized nearest-neighbor ranking
      explanations.py         Career-specific evidence and fit reasons
    services/
      assessment.py           Shared question definitions and scoring
      catalog.py              CSV validation and database imports
      feedback.py             Feedback and summary calculations
      onet_import.py          Raw O*NET evidence import
      assessment_history.py   Assessment history persistence
    templates/                Base page, home, assessment and footer
    static/
      css/                    Utilities, components, responsive layouts
      js/                     API, options, assessment, results, navigation
      images/                 Local homepage assets
  data/
    reference/                Editable pathway/salary CSVs and question JSON
    source/onet/              Three required raw O*NET CSVs
  database/als_gabay.db        Local persistent database
  deployment/                 Compose, startup script, proxy example
  docs/                       Deployment, data dictionary and change notes
  frontend/                   Optional utility-CSS rebuild inputs
  tests/                      Isolated integration tests
  manage.py                   Administrative commands
  serve.py                    Production Waitress server
  wsgi.py                     WSGI application: wsgi:application
  development_server.py       Local debug server only
  requirements.txt            Runtime Python dependencies
  Dockerfile                  Container deployment
```

The unused bulk O*NET datasets and old pickled models are excluded to keep the ZIP
small and reliable. All files needed for the included runtime and O*NET rebuild
command are present.

## Optional utility CSS rebuild

Only developers adding new Tailwind utility classes need Node.js/npm. The compiled
stylesheet is included. From the project folder:

```sh
npm exec --yes --package=tailwindcss@3.4.17 -- tailwindcss -c frontend/tailwind.config.cjs -i frontend/tailwind.input.css -o app/static/css/utilities.css --minify
```

## Troubleshooting

- Missing Python module: activate `.venv`, then install `requirements.txt`.
- Missing tables or occupation catalog: run `python manage.py initialize-database`.
- CSV changes not visible: run `python manage.py import-reference-data`, then refresh.
- Unknown O*NET code in a reference CSV: import the occupation catalog first.
- Port occupied: set `PORT=8081` in the environment and use that port in the URL.
- Missing styles: confirm all files under `app/static/css/` were extracted.
- Phone cannot connect: check HOST, local IP, Wi-Fi isolation, and private firewall.
- Recommendations differ from the previous version: two items now contribute per
  RIASEC category, the distance scales are normalized, and skill/feedback adjustments
  are bounded. The ranking is expected to change.
