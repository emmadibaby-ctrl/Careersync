from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect
import json
import re

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///careersync.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# The embedding model is downloaded the first time it is available.
# If it cannot load (for example, no internet on first run), a transparent
# keyword-overlap fallback keeps the prototype usable.
_model = None
_model_attempted = False

class StudentProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(160), nullable=False, unique=True)
    branch = db.Column(db.String(80), nullable=False)
    study_year = db.Column(db.String(30), nullable=False)
    skills = db.Column(db.Text, nullable=False, default="[]")
    interests = db.Column(db.Text, nullable=False, default="")
    preferred_location = db.Column(db.String(100), nullable=False, default="Any")
    work_mode = db.Column(db.String(30), nullable=False, default="Any")

class Internship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    company = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    required_skills = db.Column(db.Text, nullable=False, default="[]")
    branches = db.Column(db.Text, nullable=False, default="[]")
    location = db.Column(db.String(100), nullable=False, default="Remote")
    work_mode = db.Column(db.String(30), nullable=False, default="Remote")
    stipend = db.Column(db.String(80), nullable=False, default="Not specified")
    duration = db.Column(db.String(80), nullable=False, default="Not specified")
    apply_url = db.Column(db.String(400), nullable=False, default="#")

SAMPLE_INTERNSHIPS = [
    {
        "title": "Embedded Systems Intern",
        "company": "CircuitWorks Labs",
        "description": "Work with microcontrollers, Embedded C, peripheral interfacing, UART, SPI, I2C, debugging, and firmware testing. Build and test embedded prototypes.",
        "required_skills": ["Embedded C", "C", "Microcontrollers", "Arduino", "UART", "SPI", "I2C", "Debugging"],
        "branches": ["ECE", "EEE", "EIE", "CSE"],
        "location": "Bengaluru",
        "work_mode": "Hybrid",
        "stipend": "₹8,000–₹12,000/month",
        "duration": "3 months",
        "apply_url": "https://internship.aicte-india.org/"
    },
    {
        "title": "IoT Development Intern",
        "company": "ConnectedEdge",
        "description": "Develop Internet of Things prototypes using ESP32, sensors, MQTT, Wi-Fi, Arduino IDE, and Python. Collect sensor data and create simple dashboards.",
        "required_skills": ["ESP32", "IoT", "Arduino", "Sensors", "Python", "MQTT", "Wi-Fi"],
        "branches": ["ECE", "EEE", "CSE", "IT"],
        "location": "Remote",
        "work_mode": "Remote",
        "stipend": "₹6,000–₹10,000/month",
        "duration": "2 months",
        "apply_url": "https://internshala.com/"
    },
    {
        "title": "PCB Design Intern",
        "company": "BoardSmith Electronics",
        "description": "Assist with schematic capture, PCB layout, component footprints, design-rule checks, routing, prototyping, and hardware validation using KiCad or similar EDA tools.",
        "required_skills": ["PCB Design", "KiCad", "Electronics", "Schematic Design", "Hardware Testing"],
        "branches": ["ECE", "EEE", "EIE"],
        "location": "Hyderabad",
        "work_mode": "On-site",
        "stipend": "₹7,000/month",
        "duration": "3 months",
        "apply_url": "https://internship.aicte-india.org/"
    },
    {
        "title": "Python Automation Intern",
        "company": "ByteBridge",
        "description": "Write Python scripts to automate repetitive tasks, process data, call APIs, test software, and document solutions. Basic Git knowledge is useful.",
        "required_skills": ["Python", "Automation", "Git", "APIs", "Testing"],
        "branches": ["CSE", "IT", "ECE", "EEE"],
        "location": "Remote",
        "work_mode": "Remote",
        "stipend": "₹5,000–₹8,000/month",
        "duration": "2 months",
        "apply_url": "https://internshala.com/"
    },
    {
        "title": "VLSI Design Intern",
        "company": "SiliconPath",
        "description": "Learn digital design fundamentals, Verilog HDL, RTL coding, simulation, testbenches, timing concepts, and FPGA prototyping.",
        "required_skills": ["Verilog", "Digital Electronics", "RTL", "FPGA", "Simulation"],
        "branches": ["ECE", "EEE"],
        "location": "Chennai",
        "work_mode": "Hybrid",
        "stipend": "₹10,000/month",
        "duration": "4 months",
        "apply_url": "https://internship.aicte-india.org/"
    },
    {
        "title": "Machine Learning Intern",
        "company": "DataSpring",
        "description": "Prepare datasets, use Python and pandas, train baseline machine-learning models, evaluate results, and communicate findings with visualizations.",
        "required_skills": ["Python", "Machine Learning", "Pandas", "Data Analysis", "Scikit-learn"],
        "branches": ["CSE", "IT", "ECE", "EEE"],
        "location": "Remote",
        "work_mode": "Remote",
        "stipend": "₹8,000/month",
        "duration": "3 months",
        "apply_url": "https://internshala.com/"
    }
]

def get_model():
    global _model, _model_attempted
    if not _model_attempted:
        _model_attempted = True
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        except Exception as exc:
            print(f"[CareerSync] Semantic model unavailable; using keyword fallback. Details: {exc}")
    return _model

def tokens(text):
    return set(re.findall(r"[a-zA-Z0-9+#.]+", (text or "").lower()))

def semantic_score(student_text, internship_text):
    model = get_model()
    if model is not None:
        from sentence_transformers import util
        vectors = model.encode([student_text, internship_text], normalize_embeddings=True)
        return max(0.0, float(util.cos_sim(vectors[0], vectors[1]).item()))
    a, b = tokens(student_text), tokens(internship_text)
    return len(a & b) / max(1, len(a | b))

def seed_database():
    if Internship.query.count() == 0:
        for item in SAMPLE_INTERNSHIPS:
            db.session.add(Internship(
                title=item["title"], company=item["company"], description=item["description"],
                required_skills=json.dumps(item["required_skills"]), branches=json.dumps(item["branches"]),
                location=item["location"], work_mode=item["work_mode"], stipend=item["stipend"],
                duration=item["duration"], apply_url=item["apply_url"]
            ))
        db.session.commit()

with app.app_context():
    db.create_all()
    seed_database()

@app.get("/")
def index():
    return render_template("index.html")

@app.get("/api/internships")
def internships():
    items = Internship.query.order_by(Internship.title).all()
    return jsonify([internship_to_dict(i) for i in items])

def internship_to_dict(i):
    return {
        "id": i.id, "title": i.title, "company": i.company, "description": i.description,
        "required_skills": json.loads(i.required_skills), "branches": json.loads(i.branches),
        "location": i.location, "work_mode": i.work_mode, "stipend": i.stipend,
        "duration": i.duration, "apply_url": i.apply_url
    }

@app.post("/api/recommend")
def recommend():
    data = request.get_json(silent=True) or {}
    required = ["name", "email", "branch", "study_year"]
    missing = [key for key in required if not str(data.get(key, "")).strip()]
    if missing:
        return jsonify({"error": "Please complete these fields: " + ", ".join(missing)}), 400

    skills = data.get("skills", [])
    if isinstance(skills, str):
        skills = [s.strip() for s in skills.split(",") if s.strip()]
    skills = list(dict.fromkeys(s for s in skills if s))
    interests = str(data.get("interests", "")).strip()
    location = str(data.get("preferred_location", "Any")).strip() or "Any"
    work_mode = str(data.get("work_mode", "Any")).strip() or "Any"

    email = str(data["email"]).strip().lower()
    profile = StudentProfile.query.filter_by(email=email).first()
    if profile is None:
        profile = StudentProfile(email=email, name=str(data["name"]).strip(),
                                 branch=str(data["branch"]).strip(),
                                 study_year=str(data["study_year"]).strip())
        db.session.add(profile)
    profile.name = str(data["name"]).strip()
    profile.branch = str(data["branch"]).strip()
    profile.study_year = str(data["study_year"]).strip()
    profile.skills = json.dumps(skills)
    profile.interests = interests
    profile.preferred_location = location
    profile.work_mode = work_mode
    db.session.commit()

    student_text = (
        f"Student branch: {profile.branch}. Academic year: {profile.study_year}. "
        f"Skills: {', '.join(skills)}. Interests and career goals: {interests}."
    )
    results = []
    for item in Internship.query.all():
        required_skills = json.loads(item.required_skills)
        branches = json.loads(item.branches)
        internship_text = (
            f"{item.title}. {item.description}. Required skills: {', '.join(required_skills)}. "
            f"Eligible branches: {', '.join(branches)}."
        )
        semantic = semantic_score(student_text, internship_text)
        student_skills = {s.lower() for s in skills}
        required_lower = {s.lower() for s in required_skills}
        exact_matches = sorted([s for s in required_skills if s.lower() in student_skills])
        skill_score = len({s.lower() for s in exact_matches}) / max(1, len(required_lower))
        branch_score = 1.0 if profile.branch.upper() in [b.upper() for b in branches] else 0.0
        location_score = 1.0 if location.lower() in ("any", "no preference", item.location.lower()) or item.location.lower() == "remote" else 0.0
        mode_score = 1.0 if work_mode.lower() in ("any", "no preference", item.work_mode.lower()) else 0.0

        # Weighted ranking: semantic relevance 50%, skills 30%, branch 10%, location/mode 10%.
        score = (0.50 * semantic + 0.30 * skill_score +
                 0.10 * branch_score + 0.05 * location_score + 0.05 * mode_score)
        score_pct = round(max(0, min(1, score)) * 100)
        missing_skills = [s for s in required_skills if s.lower() not in student_skills]
        results.append({
            **internship_to_dict(item),
            "match_score": score_pct,
            "matched_skills": exact_matches,
            "missing_skills": missing_skills,
            "semantic_similarity": round(semantic * 100),
        })

    results.sort(key=lambda x: x["match_score"], reverse=True)
    return jsonify({"student": {"name": profile.name, "branch": profile.branch},
                    "recommendations": results,
                    "matching_method": "sentence-transformers" if get_model() is not None else "keyword fallback"})

if __name__ == "__main__":
    app.run(debug=True)
