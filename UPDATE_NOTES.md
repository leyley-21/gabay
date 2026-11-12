# Apply this update

This release is based on the design in your uploaded `als_gabay.zip`. It retains
that layout and green color palette, with wording, font-size, button visibility,
response-time and calculation changes only.

The included `database/als_gabay.db` is identical to the uploaded database. It
contains all uploaded assessment/feedback data. A virtual environment is not
included because it should stay local to each computer.

## Update your current working installation

1. Stop the server with Ctrl+C and back up your working folder.
2. Extract the ZIP into a separate folder.
3. Copy its **app** folder into your existing `C:\THESIS\GABAY\als_gabay`,
   replacing matching program files. You may also copy updated tests/docs/README.
4. Keep your existing `.venv`, `database`, and customized CSV data in place.
   If more users have used the app since the upload, do **not** replace the live
   database with the bundled snapshot; your live copy contains newer records.
5. No dependency reinstall, database initialization, or CSV import is needed for
   this update.
6. Restart in PowerShell:

```powershell
cd C:\THESIS\GABAY\als_gabay
$env:HOST = "127.0.0.1"
$env:PORT = "8080"
.\.venv\Scripts\python.exe -u serve.py
```

Open http://127.0.0.1:8080 and press Ctrl+F5 to refresh scripts and styles.

## What you will see

- The uploaded layout and green palette, with a more readable local system font.
- Simpler wording and fewer repeated data-source/ML references.
- The final assessment button says **See Result**.
- A clearly outlined **Back** button, including a way back home from the first step.
- A clearly outlined **Retake Assessment** button on the results page.
- Faster repeat recommendation calculations and complete-catalog reranking.

The 12 questions, circle ratings, SQLite storage, anonymous feedback, and existing
production entry point remain in place. See docs/performance_update.md for the
calculation change and measured timings.
