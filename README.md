# CareerSync — Smart Internship Recommendation System

## Features in this starter
- Responsive student profile form
- Flask backend and JSON API
- SQLite persistence for student profiles and internships
- Sample internship dataset seeded automatically
- Semantic matching with Sentence Transformers (`all-MiniLM-L6-v2`)
- Skill overlap, branch eligibility, location, and work-mode signals
- Match scores and missing-skill explanations
- Keyword-overlap fallback if the embedding model cannot load

## Requirements
- Python 3.11 or newer
- VS Code (recommended)
- Internet access for the first Sentence Transformers model download

## Windows PowerShell setup
Open PowerShell in the `CareerSync` folder.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

If PowerShell blocks activation, use this for the current terminal session:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Then open `http://127.0.0.1:5000` in your browser.

## If the `py -3.11` command is unavailable
Use the Python version installed on your machine:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

## Test the API
Open `http://127.0.0.1:5000/api/internships` to view sample internship data.

PowerShell API test:
```powershell
$body = @{
  name = "Demo Student"
  email = "demo@example.com"
  branch = "ECE"
  study_year = "3rd year"
  skills = @("Embedded C", "Arduino", "ESP32", "Python")
  interests = "Embedded systems, IoT, sensors, firmware development"
  preferred_location = "Any"
  work_mode = "Any"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/recommend" -Method Post -ContentType "application/json" -Body $body
```

## Notes
- Sample company names and internship entries are fictional demo data; application URLs lead to general internship portals, not verified individual vacancies.
- The match percentage is a ranking score, not the probability of being selected.
- SQLite database file is created automatically at first run.
- The first AI model download may take a few minutes. If it fails, the app uses a basic keyword-overlap fallback.
- This is a local development prototype. Before public deployment, add authentication, CSRF protections, rate limiting, validation, privacy controls, and production server configuration.
