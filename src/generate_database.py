"""
generate_database.py
────────────────────
Generates a realistic forensic-testing database for 50 people for the
AI-Powered Document Forgery Detection Assistant.

Outputs (all in demo/database/):
  • people.csv                  — master registry of 50 people
  • documents.csv               — all documents (4 types x 50 people = 200 rows)
  • forgery_cases.csv           — forensic case records with anomaly details
  • forensic_db.sqlite          — SQLite database with all three tables
  • pdfs/                       — 200 individual PDF files (one per document record)

Each person has exactly 4 documents:
  1. COVID Vaccination Certificate
  2. Degree Certificate
  3. Property Sale Deed
  4. First Information Report (FIR)

~40% of documents are marked forged with realistic anomaly annotations.

Run:
    python src/generate_database.py
"""

import csv
import json
import os
import random
import sqlite3
import string
import sys

# Make sure the PDF generators from generate_dummy_pdfs are importable
sys.path.insert(0, os.path.dirname(__file__))
from generate_dummy_pdfs import (
    _covid_cert, _degree_cert, _property_deed, _fir,
    OUT_DIR as SAMPLE_DIR,
)

random.seed(42)

BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "demo", "database")
PDF_DIR  = os.path.join(BASE_DIR, "pdfs")
os.makedirs(PDF_DIR, exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# Seed data pools
# ─────────────────────────────────────────────────────────────────────────────

FIRST_NAMES_M = [
    "Rahul", "Amit", "Suresh", "Ramesh", "Vikas", "Sandeep", "Ajay", "Vijay",
    "Ravi", "Deepak", "Anil", "Mahesh", "Naresh", "Rakesh", "Dinesh", "Mukesh",
    "Rajesh", "Pankaj", "Ashok", "Sanjay", "Pradeep", "Girish", "Kiran", "Sachin",
    "Nikhil", "Rohan", "Arjun", "Mohan",
]
FIRST_NAMES_F = [
    "Priya", "Sunita", "Kavita", "Meena", "Rekha", "Suman", "Anita", "Geeta",
    "Pooja", "Neha", "Ritu", "Asha", "Usha", "Nisha", "Sarita", "Seema",
    "Lalita", "Mamta", "Vandana", "Swati", "Divya", "Komal", "Shweta",
]
LAST_NAMES = [
    "Sharma", "Verma", "Singh", "Gupta", "Patel", "Joshi", "Mehta", "Kumar",
    "Agarwal", "Mishra", "Tiwari", "Yadav", "Dubey", "Pandey", "Shukla",
    "Chauhan", "Srivastava", "Nair", "Reddy", "Iyer", "Pillai", "Menon",
    "Rao", "Bhat", "Desai", "Shah", "Jain", "Saxena", "Trivedi", "Thakur",
]
CITIES = [
    ("New Delhi", "Delhi", "110001"),
    ("Mumbai", "Maharashtra", "400001"),
    ("Bengaluru", "Karnataka", "560001"),
    ("Hyderabad", "Telangana", "500001"),
    ("Chennai", "Tamil Nadu", "600001"),
    ("Kolkata", "West Bengal", "700001"),
    ("Pune", "Maharashtra", "411001"),
    ("Ahmedabad", "Gujarat", "380001"),
    ("Jaipur", "Rajasthan", "302001"),
    ("Lucknow", "Uttar Pradesh", "226001"),
    ("Gurugram", "Haryana", "122001"),
    ("Noida", "Uttar Pradesh", "201301"),
    ("Chandigarh", "Punjab", "160001"),
    ("Bhopal", "Madhya Pradesh", "462001"),
    ("Patna", "Bihar", "800001"),
]
UNIVERSITIES = [
    "University of Delhi", "Mumbai University", "Bangalore University",
    "Anna University", "Osmania University", "Calcutta University",
    "Pune University", "Gujarat University", "Rajasthan University",
    "Lucknow University", "IIT Delhi", "IIT Mumbai", "IIT Madras",
    "NIT Trichy", "BITS Pilani",
]
VACCINES = ["COVISHIELD (AstraZeneca)", "COVAXIN (Bharat Biotech)", "CORBEVAX", "Sputnik V"]
DEGREES = [
    ("Bachelor of Technology", "Computer Science & Engineering"),
    ("Bachelor of Technology", "Electronics & Communication"),
    ("Bachelor of Commerce", "Accounting & Finance"),
    ("Bachelor of Science", "Physics"),
    ("Bachelor of Arts", "Economics"),
    ("Master of Business Administration", "Finance"),
    ("Master of Technology", "Artificial Intelligence"),
    ("Bachelor of Law", "Criminal Law"),
    ("Bachelor of Medicine", "General Medicine"),
    ("Bachelor of Architecture", "Urban Design"),
]
POLICE_STATIONS = [
    "Dwarka Sector 7, South-West Delhi",
    "Andheri (West), Mumbai",
    "Koramangala, Bengaluru",
    "Banjara Hills, Hyderabad",
    "T. Nagar, Chennai",
    "Park Street, Kolkata",
    "Kothrud, Pune",
    "Satellite, Ahmedabad",
    "Vaishali Nagar, Jaipur",
    "Hazratganj, Lucknow",
]
IPC_SECTIONS_LIST = [
    "420, 406, 34 IPC",
    "467, 468, 471 IPC",
    "419, 420 IPC",
    "120B, 420, 467 IPC",
    "406, 420, 506 IPC",
]

# Forgery anomaly catalogue
COVID_ANOMALIES = [
    "Name spelling discrepancy (extra space/transposition)",
    "Zero-for-O substitution in vaccine name (C0VISHIELD)",
    "Zero-for-O substitution in date field",
    "Blank PDF author metadata",
    "Font inconsistency in beneficiary details (Courier vs Helvetica)",
    "QR code placeholder missing/non-functional",
    "Misaligned government seal",
    "Pre-vaccination date on certificate",
    "Dose sequence illogical (2nd dose before 1st)",
    "Vaccination centre name not in official registry",
]
DEGREE_ANOMALIES = [
    "Zero-for-O substitution in student name",
    "CGPA inflated beyond university maximum",
    "Font inconsistency — Times-Italic for name vs Helvetica in original",
    "Zero-for-O in roll number",
    "Year of passing post-dates current year",
    "Registrar signature rendered as flat line",
    "University seal faded/misaligned",
    "Division mismatch with CGPA",
    "Blank PDF author and producer metadata",
    "Certificate number format deviates from university standard",
]
PROPERTY_ANOMALIES = [
    "Plot area inflated in numeric field",
    "Sale consideration altered (amount mismatch)",
    "Stamp duty inconsistent with stated consideration",
    "e-Challan number has zero-for-O substitution",
    "Seller name has double space (copy-paste artefact)",
    "Font inconsistency in value fields (Courier vs Helvetica)",
    "Sub-registrar seal missing",
    "Witness Aadhaar number format irregular",
    "Document number has letter-O for digit-0",
    "Registration date precedes deed execution date",
]
FIR_ANOMALIES = [
    "FIR number has zero-for-O substitution",
    "IPC section uses lowercase-L for uppercase-I (lPC vs IPC)",
    "Date field has zero-for-O substitution",
    "Officer signature is a straight horizontal line",
    "Police station seal faded below detection threshold",
    "Accused name has double space (copy-paste artefact)",
    "Font inconsistency in value fields (Courier vs Helvetica)",
    "Blank author metadata in PDF",
    "Complainant address differs from property deed address",
    "FIR date precedes the stated date of occurrence",
]

ANOMALY_MAP = {
    "covid":    COVID_ANOMALIES,
    "degree":   DEGREE_ANOMALIES,
    "property": PROPERTY_ANOMALIES,
    "fir":      FIR_ANOMALIES,
}

FORGERY_TYPES = [
    "Fabricated Document",
    "Altered Genuine Document",
    "Counterfeit Official Copy",
    "Digitally Manipulated",
    "Impersonation-based Fraud",
]

CONFIDENCE_SCORES = {
    "genuine": lambda: round(random.uniform(0.05, 0.18), 2),
    "forged":  lambda: round(random.uniform(0.72, 0.98), 2),
}


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _rand_dob(min_age=22, max_age=65):
    year  = random.randint(2025 - max_age, 2025 - min_age)
    month = random.randint(1, 12)
    day   = random.randint(1, 28)
    return f"{day:02d}-{['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][month-1]}-{year}"


def _rand_date(y_start=2018, y_end=2024):
    year  = random.randint(y_start, y_end)
    month = random.randint(1, 12)
    day   = random.randint(1, 28)
    return f"{day:02d}-{['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][month-1]}-{year}"


def _rand_aadhaar():
    return f"XXXX-XXXX-{random.randint(1000,9999)}"


def _rand_amount(low, high, step=50000):
    return (random.randint(low // step, high // step)) * step


def _doc_no(prefix, year, serial):
    return f"{prefix}/{year}/{serial:05d}"


def _fir_no(year, serial):
    return f"{year}/FIR/{serial:04d}"


# ─────────────────────────────────────────────────────────────────────────────
# People generation
# ─────────────────────────────────────────────────────────────────────────────

def generate_people(n=50):
    people = []
    used_names = set()
    for i in range(1, n + 1):
        gender = random.choice(["Male", "Female"])
        first  = random.choice(FIRST_NAMES_M if gender == "Male" else FIRST_NAMES_F)
        last   = random.choice(LAST_NAMES)
        # ensure unique full names
        attempt = 0
        while f"{first} {last}" in used_names and attempt < 20:
            last = random.choice(LAST_NAMES)
            attempt += 1
        used_names.add(f"{first} {last}")

        city, state, pin = random.choice(CITIES)
        house_no  = f"{random.randint(1,200)}, Block-{random.choice('ABCDE')}"
        sector    = f"Sector {random.randint(1,25)}"
        address   = f"{house_no}, {sector}, {city} — {pin}"
        father    = f"Shri {random.choice(FIRST_NAMES_M)} {last}"

        people.append({
            "person_id":     f"P{i:03d}",
            "full_name":     f"{first} {last}",
            "gender":        gender,
            "dob":           _rand_dob(),
            "father_name":   father,
            "address":       address,
            "city":          city,
            "state":         state,
            "pincode":       pin,
            "aadhaar":       _rand_aadhaar(),
            "mobile":        f"9{random.randint(100000000, 999999999)}",
            "email":         f"{first.lower()}.{last.lower()}{random.randint(1,99)}@example.com",
        })
    return people


# ─────────────────────────────────────────────────────────────────────────────
# Document records generation
# ─────────────────────────────────────────────────────────────────────────────

def generate_documents(people):
    docs   = []
    cases  = []
    case_no = 1

    # ~40 % forged overall; distribute across doc types
    forged_flags = [random.random() < 0.40 for _ in range(len(people) * 4)]
    flag_idx = 0

    for p in people:
        pid  = p["person_id"]
        name = p["full_name"]
        city, state = p["city"], p["state"]

        # ── 1. COVID Certificate ───────────────────────────────────────────
        is_forged = forged_flags[flag_idx]; flag_idx += 1
        vaccine   = random.choice(VACCINES)
        vacc_date = _rand_date(2021, 2022)
        center    = f"PHC {city}, Ward {random.randint(1,20)}"
        ref_no    = f"{''.join(random.choices(string.digits, k=16))}"
        covid_doc = {
            "doc_id":        f"{pid}-COV",
            "person_id":     pid,
            "person_name":   name,
            "doc_type":      "COVID Vaccination Certificate",
            "doc_subtype":   "covid",
            "issue_date":    vacc_date,
            "issuing_auth":  "Ministry of Health & Family Welfare, CoWIN Portal",
            "is_forged":     int(is_forged),
            "forgery_conf":  CONFIDENCE_SCORES["forged"]() if is_forged else CONFIDENCE_SCORES["genuine"](),
            "pdf_file":      f"{pid}_covid_{'forged' if is_forged else 'genuine'}.pdf",
            # Extra fields
            "vaccine":       vaccine,
            "dose":          "2nd Dose",
            "center":        center,
            "ref_no":        ref_no,
        }
        docs.append(covid_doc)
        if is_forged:
            anomalies = random.sample(COVID_ANOMALIES, k=random.randint(2, 4))
            cases.append({
                "case_id":        f"FC{case_no:04d}",
                "doc_id":         covid_doc["doc_id"],
                "person_id":      pid,
                "person_name":    name,
                "doc_type":       "COVID Vaccination Certificate",
                "forgery_type":   random.choice(FORGERY_TYPES),
                "confidence":     covid_doc["forgery_conf"],
                "anomalies":      " | ".join(anomalies),
                "anomaly_count":  len(anomalies),
                "detected_by":    "AI Forensic Engine v1.0",
                "case_date":      _rand_date(2022, 2024),
                "status":         random.choice(["Under Investigation", "Confirmed Forgery", "Referred to Police"]),
                "remarks":        f"Document submitted by {name}. Cross-verification with CoWIN portal failed.",
            })
            case_no += 1

        # ── 2. Degree Certificate ──────────────────────────────────────────
        is_forged  = forged_flags[flag_idx]; flag_idx += 1
        univ       = random.choice(UNIVERSITIES)
        deg, major = random.choice(DEGREES)
        grad_year  = random.randint(2015, 2023)
        cgpa_real  = round(random.uniform(6.0, 9.5), 1)
        cgpa_disp  = round(cgpa_real + random.uniform(0.5, 1.0), 1) if is_forged else cgpa_real
        cgpa_disp  = min(cgpa_disp, 10.0)
        enroll_no  = f"{univ[:2].upper()}/{grad_year - 4}/{random.randint(10000,99999)}"
        degree_doc = {
            "doc_id":        f"{pid}-DEG",
            "person_id":     pid,
            "person_name":   name,
            "doc_type":      "Degree Certificate",
            "doc_subtype":   "degree",
            "issue_date":    f"15-Jun-{grad_year}",
            "issuing_auth":  univ,
            "is_forged":     int(is_forged),
            "forgery_conf":  CONFIDENCE_SCORES["forged"]() if is_forged else CONFIDENCE_SCORES["genuine"](),
            "pdf_file":      f"{pid}_degree_{'forged' if is_forged else 'genuine'}.pdf",
            "degree":        deg,
            "major":         major,
            "university":    univ,
            "cgpa":          cgpa_disp,
            "enroll_no":     enroll_no,
            "grad_year":     grad_year,
        }
        docs.append(degree_doc)
        if is_forged:
            anomalies = random.sample(DEGREE_ANOMALIES, k=random.randint(2, 4))
            cases.append({
                "case_id":       f"FC{case_no:04d}",
                "doc_id":        degree_doc["doc_id"],
                "person_id":     pid,
                "person_name":   name,
                "doc_type":      "Degree Certificate",
                "forgery_type":  random.choice(FORGERY_TYPES),
                "confidence":    degree_doc["forgery_conf"],
                "anomalies":     " | ".join(anomalies),
                "anomaly_count": len(anomalies),
                "detected_by":   "AI Forensic Engine v1.0",
                "case_date":     _rand_date(2022, 2024),
                "status":        random.choice(["Under Investigation", "Confirmed Forgery", "Referred to Police"]),
                "remarks":       f"CGPA {cgpa_disp} does not match university records ({cgpa_real}). Referred to Education Ministry.",
            })
            case_no += 1

        # ── 3. Property Sale Deed ──────────────────────────────────────────
        is_forged   = forged_flags[flag_idx]; flag_idx += 1
        reg_date    = _rand_date(2018, 2024)
        area_actual = random.randint(80, 300)
        area_disp   = area_actual + random.randint(20, 60) if is_forged else area_actual
        amount_act  = _rand_amount(2000000, 15000000)
        amount_disp = amount_act + _rand_amount(500000, 3000000) if is_forged else amount_act
        sro_code    = f"SRO/{city[:3].upper()}/{_rand_date(2018,2024)[-4:]}/{random.randint(1000,9999)}"
        buyer_first = random.choice(FIRST_NAMES_F + FIRST_NAMES_M)
        buyer_last  = random.choice(LAST_NAMES)
        prop_doc = {
            "doc_id":        f"{pid}-PRO",
            "person_id":     pid,
            "person_name":   name,
            "doc_type":      "Property Sale Deed",
            "doc_subtype":   "property",
            "issue_date":    reg_date,
            "issuing_auth":  f"Sub-Registrar Office, {city}",
            "is_forged":     int(is_forged),
            "forgery_conf":  CONFIDENCE_SCORES["forged"]() if is_forged else CONFIDENCE_SCORES["genuine"](),
            "pdf_file":      f"{pid}_property_{'forged' if is_forged else 'genuine'}.pdf",
            "seller":        name,
            "buyer":         f"{buyer_first} {buyer_last}",
            "area_sqyards":  area_disp,
            "amount_inr":    amount_disp,
            "stamp_duty":    round(amount_disp * 0.06),
            "reg_fee":       round(amount_disp * 0.01),
            "sro_doc_no":    sro_code,
        }
        docs.append(prop_doc)
        if is_forged:
            anomalies = random.sample(PROPERTY_ANOMALIES, k=random.randint(2, 4))
            cases.append({
                "case_id":       f"FC{case_no:04d}",
                "doc_id":        prop_doc["doc_id"],
                "person_id":     pid,
                "person_name":   name,
                "doc_type":      "Property Sale Deed",
                "forgery_type":  random.choice(FORGERY_TYPES),
                "confidence":    prop_doc["forgery_conf"],
                "anomalies":     " | ".join(anomalies),
                "anomaly_count": len(anomalies),
                "detected_by":   "AI Forensic Engine v1.0",
                "case_date":     _rand_date(2022, 2024),
                "status":        random.choice(["Under Investigation", "Confirmed Forgery", "Referred to Police"]),
                "remarks":       f"Stated area {area_disp} sq.yd vs registered {area_actual} sq.yd. Amount discrepancy INR {abs(amount_disp - amount_act):,}.",
            })
            case_no += 1

        # ── 4. FIR ────────────────────────────────────────────────────────
        is_forged  = forged_flags[flag_idx]; flag_idx += 1
        fir_date   = _rand_date(2020, 2024)
        ps         = random.choice(POLICE_STATIONS)
        ipc        = random.choice(IPC_SECTIONS_LIST)
        fir_number = _fir_no(fir_date[-4:], random.randint(100, 999))
        fir_doc = {
            "doc_id":        f"{pid}-FIR",
            "person_id":     pid,
            "person_name":   name,
            "doc_type":      "First Information Report",
            "doc_subtype":   "fir",
            "issue_date":    fir_date,
            "issuing_auth":  f"Delhi Police — {ps}",
            "is_forged":     int(is_forged),
            "forgery_conf":  CONFIDENCE_SCORES["forged"]() if is_forged else CONFIDENCE_SCORES["genuine"](),
            "pdf_file":      f"{pid}_fir_{'forged' if is_forged else 'genuine'}.pdf",
            "fir_no":        fir_number,
            "police_station": ps,
            "ipc_sections":  ipc,
            "complainant":   name,
        }
        docs.append(fir_doc)
        if is_forged:
            anomalies = random.sample(FIR_ANOMALIES, k=random.randint(2, 4))
            cases.append({
                "case_id":       f"FC{case_no:04d}",
                "doc_id":        fir_doc["doc_id"],
                "person_id":     pid,
                "person_name":   name,
                "doc_type":      "First Information Report",
                "forgery_type":  random.choice(FORGERY_TYPES),
                "confidence":    fir_doc["forgery_conf"],
                "anomalies":     " | ".join(anomalies),
                "anomaly_count": len(anomalies),
                "detected_by":   "AI Forensic Engine v1.0",
                "case_date":     _rand_date(2022, 2024),
                "status":        random.choice(["Under Investigation", "Confirmed Forgery", "Referred to Police"]),
                "remarks":       f"FIR number format irregular. Cross-check with PS {ps} pending.",
            })
            case_no += 1

    return docs, cases


# ─────────────────────────────────────────────────────────────────────────────
# PDF generation for each person-document record
# ─────────────────────────────────────────────────────────────────────────────

def generate_pdfs(people, docs):
    """Generate one PDF per document record using person-specific data."""
    people_map = {p["person_id"]: p for p in people}

    # We'll use the generic generator functions (genuine/forged flag)
    # The functions write visually representative docs; for this batch
    # we simply call them with the forged flag per record.
    print(f"  Generating {len(docs)} PDFs...")
    for doc in docs:
        out_path = os.path.join(PDF_DIR, doc["pdf_file"])
        forged   = bool(doc["is_forged"])
        subtype  = doc["doc_subtype"]

        if subtype == "covid":
            _covid_cert(out_path, forged)
        elif subtype == "degree":
            _degree_cert(out_path, forged)
        elif subtype == "property":
            _property_deed(out_path, forged)
        elif subtype == "fir":
            _fir(out_path, forged)


# ─────────────────────────────────────────────────────────────────────────────
# CSV export
# ─────────────────────────────────────────────────────────────────────────────

PEOPLE_COLS = [
    "person_id", "full_name", "gender", "dob", "father_name",
    "address", "city", "state", "pincode", "aadhaar", "mobile", "email",
]
DOC_COLS = [
    "doc_id", "person_id", "person_name", "doc_type", "doc_subtype",
    "issue_date", "issuing_auth", "is_forged", "forgery_conf", "pdf_file",
    # type-specific — will be blank for irrelevant rows
    "vaccine", "dose", "center", "ref_no",               # covid
    "degree", "major", "university", "cgpa", "enroll_no", "grad_year",  # degree
    "seller", "buyer", "area_sqyards", "amount_inr", "stamp_duty", "reg_fee", "sro_doc_no",  # property
    "fir_no", "police_station", "ipc_sections", "complainant",  # fir
]
CASE_COLS = [
    "case_id", "doc_id", "person_id", "person_name", "doc_type",
    "forgery_type", "confidence", "anomalies", "anomaly_count",
    "detected_by", "case_date", "status", "remarks",
]


def write_csv(rows, cols, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


# ─────────────────────────────────────────────────────────────────────────────
# SQLite export
# ─────────────────────────────────────────────────────────────────────────────

def write_sqlite(people, docs, cases, db_path):
    conn = sqlite3.connect(db_path)
    cur  = conn.cursor()

    cur.executescript("""
    DROP TABLE IF EXISTS people;
    DROP TABLE IF EXISTS documents;
    DROP TABLE IF EXISTS forgery_cases;

    CREATE TABLE people (
        person_id   TEXT PRIMARY KEY,
        full_name   TEXT,
        gender      TEXT,
        dob         TEXT,
        father_name TEXT,
        address     TEXT,
        city        TEXT,
        state       TEXT,
        pincode     TEXT,
        aadhaar     TEXT,
        mobile      TEXT,
        email       TEXT
    );

    CREATE TABLE documents (
        doc_id        TEXT PRIMARY KEY,
        person_id     TEXT REFERENCES people(person_id),
        person_name   TEXT,
        doc_type      TEXT,
        doc_subtype   TEXT,
        issue_date    TEXT,
        issuing_auth  TEXT,
        is_forged     INTEGER,
        forgery_conf  REAL,
        pdf_file      TEXT,
        -- covid
        vaccine TEXT, dose TEXT, center TEXT, ref_no TEXT,
        -- degree
        degree TEXT, major TEXT, university TEXT, cgpa REAL, enroll_no TEXT, grad_year INTEGER,
        -- property
        seller TEXT, buyer TEXT, area_sqyards INTEGER, amount_inr INTEGER,
        stamp_duty INTEGER, reg_fee INTEGER, sro_doc_no TEXT,
        -- fir
        fir_no TEXT, police_station TEXT, ipc_sections TEXT, complainant TEXT
    );

    CREATE TABLE forgery_cases (
        case_id       TEXT PRIMARY KEY,
        doc_id        TEXT REFERENCES documents(doc_id),
        person_id     TEXT REFERENCES people(person_id),
        person_name   TEXT,
        doc_type      TEXT,
        forgery_type  TEXT,
        confidence    REAL,
        anomalies     TEXT,
        anomaly_count INTEGER,
        detected_by   TEXT,
        case_date     TEXT,
        status        TEXT,
        remarks       TEXT
    );
    """)

    cur.executemany(
        "INSERT INTO people VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        [[p.get(c, "") for c in PEOPLE_COLS] for p in people],
    )
    cur.executemany(
        f"INSERT INTO documents VALUES ({','.join(['?']*len(DOC_COLS))})",
        [[d.get(c, None) for c in DOC_COLS] for d in docs],
    )
    cur.executemany(
        f"INSERT INTO forgery_cases VALUES ({','.join(['?']*len(CASE_COLS))})",
        [[c.get(col, None) for col in CASE_COLS] for c in cases],
    )

    conn.commit()
    conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# JSON export (summary)
# ─────────────────────────────────────────────────────────────────────────────

def write_json_summary(people, docs, cases, path):
    summary = {
        "dataset_info": {
            "description": "Forensic Document Testing Database — AI Forgery Detection Assistant",
            "total_people": len(people),
            "total_documents": len(docs),
            "total_forged": sum(d["is_forged"] for d in docs),
            "total_genuine": sum(1 - d["is_forged"] for d in docs),
            "total_cases": len(cases),
            "doc_types": ["COVID Vaccination Certificate", "Degree Certificate",
                          "Property Sale Deed", "First Information Report"],
        },
        "people": people,
        "documents": docs,
        "forgery_cases": cases,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print(" Forensic Document Database Generator")
    print("=" * 60)

    print("\n[1/5] Generating 50 people...")
    people = generate_people(50)
    print(f"      {len(people)} people created.")

    print("\n[2/5] Generating document records (4 per person = 200)...")
    docs, cases = generate_documents(people)
    forged_count  = sum(d["is_forged"] for d in docs)
    genuine_count = len(docs) - forged_count
    print(f"      {len(docs)} documents | {forged_count} forged | {genuine_count} genuine")
    print(f"      {len(cases)} forensic cases created.")

    print("\n[3/5] Generating PDFs...")
    generate_pdfs(people, docs)
    print(f"      {len(docs)} PDFs written to {os.path.abspath(PDF_DIR)}")

    print("\n[4/5] Writing CSV files...")
    write_csv(people, PEOPLE_COLS, os.path.join(BASE_DIR, "people.csv"))
    write_csv(docs,   DOC_COLS,    os.path.join(BASE_DIR, "documents.csv"))
    write_csv(cases,  CASE_COLS,   os.path.join(BASE_DIR, "forgery_cases.csv"))
    print("      people.csv, documents.csv, forgery_cases.csv")

    print("\n[5/5] Writing SQLite & JSON...")
    write_sqlite(people, docs, cases, os.path.join(BASE_DIR, "forensic_db.sqlite"))
    write_json_summary(people, docs, cases, os.path.join(BASE_DIR, "forensic_db.json"))
    print("      forensic_db.sqlite, forensic_db.json")

    print("\n" + "=" * 60)
    print(f" Output directory: {os.path.abspath(BASE_DIR)}")
    print("=" * 60)
    print("\nSummary:")
    print(f"  People         : {len(people)}")
    print(f"  Documents      : {len(docs)}")
    print(f"    Genuine      : {genuine_count}  ({genuine_count*100//len(docs)}%)")
    print(f"    Forged       : {forged_count}   ({forged_count*100//len(docs)}%)")
    print(f"  Forensic Cases : {len(cases)}")
    by_type = {}
    for c in cases:
        by_type[c["doc_type"]] = by_type.get(c["doc_type"], 0) + 1
    for dt, cnt in by_type.items():
        print(f"    {dt:<40} {cnt} cases")
    print("\nDone.")
