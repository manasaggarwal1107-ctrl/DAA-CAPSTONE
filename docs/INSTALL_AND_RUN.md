# Installation, execution and demonstration

## Requirements (Windows 10/11)
* **Python 3.10 or newer** from python.org (tick *Add python.exe to PATH*). Developed and tested on 3.13.
* Internet access on the first run (pip downloads starlette, uvicorn, pydantic, reportlab, matplotlib).
* **Node.js is optional**: the built frontend is included in `frontend/dist`. Node 18+ is only needed to rebuild it.

## One-command start
Open PowerShell in the project folder and run:
```powershell
.\start.ps1
```
(or double-click `start.bat`, which bypasses the script execution policy). The first run creates `backend\.venv` and installs packages; the app then opens at **http://127.0.0.1:8000**. No login is needed. Stop with Ctrl+C.

Options: `-Port 9000`, `-NoBrowser`, `-Rebuild` (rebuild the frontend; needs Node).

> **Honest note:** `start.ps1`, `start.bat` and `run-tests.ps1` were written but **never executed** (the build environment had no PowerShell). If one fails, use the manual commands below, which are exactly what the scripts do and which were run on Linux.

## Manual commands
```powershell
cd backend
py -3 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m uvicorn app.main:app --port 8000
```

## Run the tests
```powershell
.\run-tests.ps1
# or manually
cd backend
.venv\Scripts\python -m pip install -r requirements-dev.txt
.venv\Scripts\python -m pytest
```
Expected: **128 passed** (this was the result in the build environment, Linux).

## Rebuild the frontend (optional)
```powershell
.\scripts\build-frontend.ps1      # or: cd frontend; npm install; npm run build
```

## Regenerate sample data and benchmarks
```powershell
cd backend
.venv\Scripts\python ..\scripts\make_sample_data.py
.venv\Scripts\python ..\scripts\run_benchmark.py
```

## Data location
State is stored in `backend\data\state.json` (created on first run with a sample city network and 24 sample parcels). Use the **reset** API (`POST /api/reset`) or delete that file to return to the sample data.

## Login-free demonstration workflow (about 10 minutes)
1. **Dashboard**: note the KPIs; press **Run optimisation**; watch the KPIs, utilisation and stage timings update.
2. **Parcels**: add a parcel (try an invalid weight such as 12.5 to see the validation message), edit it, filter by priority and destination, sort by deadline, export CSV.
3. **Parcels → Import**: import `sample_data/parcels_50.csv`; then import `sample_data/invalid_examples.csv` to see row-by-row error messages while valid rows still load.
4. **Prioritisation**: compare original vs sorted order, read the sort time and comparison count, step through the Merge Sort trace.
5. **Load planning**: change the capacity (e.g. 60, 0, 500) and press *Solve*; review selected/rejected parcels, the DP table and its reconstruction path.
6. **Road network**: add a location and a road, try a negative length (rejected), find a shortest path and read the hop table; remove a road (or add a location with no road) to create an unreachable destination, then optimise: its parcels appear under *Undeliverable parcels* and are not loaded or routed.
7. **Route planner**: save settings and optimise; read the legs, ETAs and on-time checks; note the approximation notice and any unreachable warning.
8. **Benchmark lab**: run sizes 10-1,000 (5,000 takes longer); read the charts and table; export CSV.
9. **Learning centre**: for each algorithm, run the interactive trace and open the viva questions.
10. **Reports & export**: download the PDF report and CSV files.

## Troubleshooting
| Symptom | Fix |
|---|---|
| "running scripts is disabled" | use `start.bat`, or `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| Port in use | `.\start.ps1 -Port 9000` |
| Browser shows an API notice instead of the UI | `frontend\dist` is missing: run `.\start.ps1 -Rebuild` (needs Node) |
