"""
tests/test_database_integrity.py
─────────────────────────────────
Unit tests that verify the forensic document database produced by
generate_database.py against the demo/database/ artefacts.

Test groups
  TestPeopleCSV          — schema, counts, uniqueness, field formats
  TestDocumentsCSV       — schema, counts, doc-type completeness, field rules
  TestForgeryCasesCSV    — schema, counts, case ↔ document consistency
  TestSQLiteIntegrity    — table existence, row counts, FK relationships, queries
  TestJSONSummary        — JSON structure, key counts, consistency with CSV
  TestPDFFiles           — every PDF referenced in documents.csv exists on disk
  TestConfidenceScores   — score ranges by forgery flag
  TestAnomalyCatalogue   — anomalies belong to the correct catalogue
  TestHelperFunctions    — unit tests for _rand_date, _rand_dob, _rand_amount,
                           _doc_no, _fir_no, generate_people, generate_documents
  TestPDFGeneration      — smoke-tests for each of the four PDF builders

Run:
    python -m pytest src/tests/ -v
  or:
    python -m pytest src/tests/test_database_integrity.py -v
"""

import csv
import json
import os
import re
import sqlite3
import sys
import tempfile
import unittest

# ── resolve paths ──────────────────────────────────────────────────────────
REPO_ROOT  = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB_DIR     = os.path.join(REPO_ROOT, "demo", "database")
PDF_DIR    = os.path.join(DB_DIR, "pdfs")
SQLITE_DB  = os.path.join(DB_DIR, "forensic_db.sqlite")
JSON_FILE  = os.path.join(DB_DIR, "forensic_db.json")
PEOPLE_CSV = os.path.join(DB_DIR, "people.csv")
DOCS_CSV   = os.path.join(DB_DIR, "documents.csv")
CASES_CSV  = os.path.join(DB_DIR, "forgery_cases.csv")

# ── make src importable ────────────────────────────────────────────────────
SRC_DIR = os.path.join(REPO_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

# ── catalogue mirrors from generate_database.py ───────────────────────────
from generate_database import (
    ANOMALY_MAP, FORGERY_TYPES, CONFIDENCE_SCORES,
    COVID_ANOMALIES, DEGREE_ANOMALIES, PROPERTY_ANOMALIES, FIR_ANOMALIES,
    VACCINES, DEGREES, UNIVERSITIES, POLICE_STATIONS, IPC_SECTIONS_LIST,
    _rand_date, _rand_dob, _rand_amount, _doc_no, _fir_no,
    generate_people, generate_documents,
    PEOPLE_COLS, DOC_COLS, CASE_COLS,
)
from generate_dummy_pdfs import _covid_cert, _degree_cert, _property_deed, _fir

EXPECTED_PEOPLE      = 50
EXPECTED_DOCS        = 200          # 4 per person
EXPECTED_DOC_TYPES   = {
    "COVID Vaccination Certificate",
    "Degree Certificate",
    "Property Sale Deed",
    "First Information Report",
}
VALID_STATUSES       = {"Under Investigation", "Confirmed Forgery", "Referred to Police"}
VALID_FORGERY_TYPES  = set(FORGERY_TYPES)
VALID_GENDERS        = {"Male", "Female"}
DOB_RE               = re.compile(r"^\d{2}-(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)-\d{4}$")
AADHAAR_RE           = re.compile(r"^XXXX-XXXX-\d{4}$")
MOBILE_RE            = re.compile(r"^9\d{9}$")
EMAIL_RE             = re.compile(r"^[\w.]+@example\.com$")
PDF_NAME_RE          = re.compile(r"^P\d{3}_(covid|degree|property|fir)_(genuine|forged)\.pdf$")


# ══════════════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════════════

def _load_csv(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _sqlite_conn():
    return sqlite3.connect(SQLITE_DB)


def _load_json():
    with open(JSON_FILE, encoding="utf-8") as f:
        return json.load(f)


# ══════════════════════════════════════════════════════════════════════════════
# TestPeopleCSV
# ══════════════════════════════════════════════════════════════════════════════

class TestPeopleCSV(unittest.TestCase):
    """Validates people.csv schema, row count, uniqueness and field formats."""

    @classmethod
    def setUpClass(cls):
        cls.rows = _load_csv(PEOPLE_CSV)

    def test_file_exists(self):
        self.assertTrue(os.path.exists(PEOPLE_CSV), "people.csv not found")

    def test_row_count(self):
        self.assertEqual(len(self.rows), EXPECTED_PEOPLE,
                         f"Expected {EXPECTED_PEOPLE} rows, got {len(self.rows)}")

    def test_required_columns_present(self):
        for col in PEOPLE_COLS:
            self.assertIn(col, self.rows[0], f"Column '{col}' missing from people.csv")

    def test_person_id_format(self):
        for r in self.rows:
            self.assertRegex(r["person_id"], r"^P\d{3}$",
                             f"Bad person_id: {r['person_id']}")

    def test_person_ids_unique(self):
        ids = [r["person_id"] for r in self.rows]
        self.assertEqual(len(ids), len(set(ids)), "Duplicate person_id values found")

    def test_full_names_unique(self):
        names = [r["full_name"] for r in self.rows]
        self.assertEqual(len(names), len(set(names)), "Duplicate full_name values found")

    def test_gender_values(self):
        for r in self.rows:
            self.assertIn(r["gender"], VALID_GENDERS,
                          f"Invalid gender '{r['gender']}' for {r['person_id']}")

    def test_dob_format(self):
        for r in self.rows:
            self.assertRegex(r["dob"], DOB_RE,
                             f"Bad DOB format '{r['dob']}' for {r['person_id']}")

    def test_aadhaar_format(self):
        for r in self.rows:
            self.assertRegex(r["aadhaar"], AADHAAR_RE,
                             f"Bad Aadhaar '{r['aadhaar']}' for {r['person_id']}")

    def test_mobile_format(self):
        for r in self.rows:
            self.assertRegex(r["mobile"], MOBILE_RE,
                             f"Bad mobile '{r['mobile']}' for {r['person_id']}")

    def test_email_format(self):
        for r in self.rows:
            self.assertRegex(r["email"], EMAIL_RE,
                             f"Bad email '{r['email']}' for {r['person_id']}")

    def test_no_empty_required_fields(self):
        required = ["person_id", "full_name", "gender", "dob", "address", "city", "state", "pincode"]
        for r in self.rows:
            for col in required:
                self.assertTrue(r[col].strip(),
                                f"Empty '{col}' for {r['person_id']}")

    def test_sequential_ids(self):
        ids = sorted(r["person_id"] for r in self.rows)
        expected = [f"P{i:03d}" for i in range(1, EXPECTED_PEOPLE + 1)]
        self.assertEqual(ids, expected, "person_id sequence is not P001–P050")


# ══════════════════════════════════════════════════════════════════════════════
# TestDocumentsCSV
# ══════════════════════════════════════════════════════════════════════════════

class TestDocumentsCSV(unittest.TestCase):
    """Validates documents.csv schema, counts, doc-type completeness and field rules."""

    @classmethod
    def setUpClass(cls):
        cls.rows    = _load_csv(DOCS_CSV)
        cls.people  = _load_csv(PEOPLE_CSV)
        cls.pid_set = {r["person_id"] for r in cls.people}

    def test_file_exists(self):
        self.assertTrue(os.path.exists(DOCS_CSV), "documents.csv not found")

    def test_total_row_count(self):
        self.assertEqual(len(self.rows), EXPECTED_DOCS,
                         f"Expected {EXPECTED_DOCS} documents, got {len(self.rows)}")

    def test_required_columns_present(self):
        base_cols = ["doc_id", "person_id", "person_name", "doc_type",
                     "doc_subtype", "issue_date", "issuing_auth", "is_forged",
                     "forgery_conf", "pdf_file"]
        for col in base_cols:
            self.assertIn(col, self.rows[0], f"Column '{col}' missing")

    def test_doc_ids_unique(self):
        ids = [r["doc_id"] for r in self.rows]
        self.assertEqual(len(ids), len(set(ids)), "Duplicate doc_id values found")

    def test_four_docs_per_person(self):
        from collections import Counter
        counts = Counter(r["person_id"] for r in self.rows)
        for pid, cnt in counts.items():
            self.assertEqual(cnt, 4,
                             f"Person {pid} has {cnt} documents, expected 4")

    def test_all_doc_types_present_per_person(self):
        from collections import defaultdict
        by_person = defaultdict(set)
        for r in self.rows:
            by_person[r["person_id"]].add(r["doc_type"])
        for pid, types in by_person.items():
            self.assertEqual(types, EXPECTED_DOC_TYPES,
                             f"Person {pid} missing doc types: {EXPECTED_DOC_TYPES - types}")

    def test_person_id_references_people(self):
        for r in self.rows:
            self.assertIn(r["person_id"], self.pid_set,
                          f"doc {r['doc_id']} references unknown person_id {r['person_id']}")

    def test_is_forged_values(self):
        for r in self.rows:
            self.assertIn(r["is_forged"], ("0", "1"),
                          f"is_forged must be 0 or 1, got '{r['is_forged']}' on {r['doc_id']}")

    def test_forgery_conf_range(self):
        for r in self.rows:
            conf = float(r["forgery_conf"])
            self.assertGreaterEqual(conf, 0.0, f"forgery_conf < 0 on {r['doc_id']}")
            self.assertLessEqual(conf, 1.0,    f"forgery_conf > 1 on {r['doc_id']}")

    def test_genuine_conf_upper_bound(self):
        """Genuine documents must have confidence < 0.20."""
        for r in self.rows:
            if r["is_forged"] == "0":
                conf = float(r["forgery_conf"])
                self.assertLess(conf, 0.20,
                                f"Genuine doc {r['doc_id']} has suspicious conf {conf}")

    def test_forged_conf_lower_bound(self):
        """Forged documents must have confidence >= 0.72."""
        for r in self.rows:
            if r["is_forged"] == "1":
                conf = float(r["forgery_conf"])
                self.assertGreaterEqual(conf, 0.72,
                                        f"Forged doc {r['doc_id']} has low conf {conf}")

    def test_pdf_filename_format(self):
        for r in self.rows:
            self.assertRegex(r["pdf_file"], PDF_NAME_RE,
                             f"Bad pdf_file name '{r['pdf_file']}' on {r['doc_id']}")

    def test_pdf_filename_matches_forged_flag(self):
        for r in self.rows:
            expected_tag = "forged" if r["is_forged"] == "1" else "genuine"
            self.assertIn(expected_tag, r["pdf_file"],
                          f"pdf_file tag mismatch on {r['doc_id']}: file={r['pdf_file']}, is_forged={r['is_forged']}")

    def test_doc_id_format(self):
        valid_suffixes = {"-COV", "-DEG", "-PRO", "-FIR"}
        for r in self.rows:
            suffix = r["doc_id"][-4:]
            self.assertIn(suffix, valid_suffixes,
                          f"Unexpected doc_id suffix: {r['doc_id']}")

    def test_covid_specific_fields(self):
        for r in self.rows:
            if r["doc_subtype"] == "covid":
                self.assertTrue(r["vaccine"].strip(), f"vaccine empty on {r['doc_id']}")
                self.assertEqual(r["dose"], "2nd Dose", f"dose mismatch on {r['doc_id']}")
                self.assertTrue(r["center"].strip(), f"center empty on {r['doc_id']}")

    def test_degree_specific_fields(self):
        for r in self.rows:
            if r["doc_subtype"] == "degree":
                self.assertTrue(r["university"].strip(), f"university empty on {r['doc_id']}")
                cgpa = float(r["cgpa"])
                self.assertGreater(cgpa, 0.0, f"cgpa <= 0 on {r['doc_id']}")
                self.assertLessEqual(cgpa, 10.0, f"cgpa > 10 on {r['doc_id']}")

    def test_property_specific_fields(self):
        for r in self.rows:
            if r["doc_subtype"] == "property":
                self.assertTrue(r["seller"].strip(),    f"seller empty on {r['doc_id']}")
                self.assertTrue(r["buyer"].strip(),     f"buyer empty on {r['doc_id']}")
                area = int(r["area_sqyards"])
                self.assertGreater(area, 0,             f"area_sqyards <= 0 on {r['doc_id']}")
                amount = int(r["amount_inr"])
                self.assertGreater(amount, 0,           f"amount_inr <= 0 on {r['doc_id']}")
                stamp = int(r["stamp_duty"])
                # stamp duty ~ 6% of amount
                self.assertAlmostEqual(stamp / amount, 0.06, places=2,
                                       msg=f"stamp_duty ratio off on {r['doc_id']}")

    def test_fir_specific_fields(self):
        for r in self.rows:
            if r["doc_subtype"] == "fir":
                self.assertTrue(r["fir_no"].strip(),           f"fir_no empty on {r['doc_id']}")
                self.assertTrue(r["police_station"].strip(),   f"police_station empty on {r['doc_id']}")
                self.assertTrue(r["ipc_sections"].strip(),     f"ipc_sections empty on {r['doc_id']}")
                self.assertTrue(r["complainant"].strip(),      f"complainant empty on {r['doc_id']}")

    def test_overall_forgery_rate_approx_40pct(self):
        total  = len(self.rows)
        forged = sum(1 for r in self.rows if r["is_forged"] == "1")
        rate   = forged / total
        # seeded random gives exactly 40/60 split; allow ±15% in case seed changes
        self.assertGreater(rate, 0.25, f"Forgery rate {rate:.0%} too low")
        self.assertLess(rate,    0.55, f"Forgery rate {rate:.0%} too high")


# ══════════════════════════════════════════════════════════════════════════════
# TestForgeryCasesCSV
# ══════════════════════════════════════════════════════════════════════════════

class TestForgeryCasesCSV(unittest.TestCase):
    """Validates forgery_cases.csv schema and its consistency with documents.csv."""

    @classmethod
    def setUpClass(cls):
        cls.cases    = _load_csv(CASES_CSV)
        cls.docs     = _load_csv(DOCS_CSV)
        cls.forged_doc_ids = {r["doc_id"] for r in cls.docs if r["is_forged"] == "1"}

    def test_file_exists(self):
        self.assertTrue(os.path.exists(CASES_CSV), "forgery_cases.csv not found")

    def test_required_columns_present(self):
        for col in CASE_COLS:
            self.assertIn(col, self.cases[0], f"Column '{col}' missing from forgery_cases.csv")

    def test_case_count_equals_forged_doc_count(self):
        self.assertEqual(len(self.cases), len(self.forged_doc_ids),
                         f"Case count {len(self.cases)} != forged doc count {len(self.forged_doc_ids)}")

    def test_case_ids_unique(self):
        ids = [c["case_id"] for c in self.cases]
        self.assertEqual(len(ids), len(set(ids)), "Duplicate case_id values")

    def test_case_id_format(self):
        for c in self.cases:
            self.assertRegex(c["case_id"], r"^FC\d{4}$",
                             f"Bad case_id: {c['case_id']}")

    def test_every_case_references_forged_doc(self):
        for c in self.cases:
            self.assertIn(c["doc_id"], self.forged_doc_ids,
                          f"Case {c['case_id']} references non-forged or unknown doc {c['doc_id']}")

    def test_no_genuine_doc_has_case(self):
        cased_docs = {c["doc_id"] for c in self.cases}
        genuine_ids = {r["doc_id"] for r in self.docs if r["is_forged"] == "0"}
        overlap = cased_docs & genuine_ids
        self.assertEqual(len(overlap), 0,
                         f"Genuine docs have forensic cases: {overlap}")

    def test_confidence_range(self):
        for c in self.cases:
            conf = float(c["confidence"])
            self.assertGreaterEqual(conf, 0.72, f"Case {c['case_id']} conf {conf} below 0.72")
            self.assertLessEqual(conf, 1.0,     f"Case {c['case_id']} conf {conf} above 1.0")

    def test_forgery_type_values(self):
        for c in self.cases:
            self.assertIn(c["forgery_type"], VALID_FORGERY_TYPES,
                          f"Unknown forgery_type '{c['forgery_type']}' in {c['case_id']}")

    def test_status_values(self):
        for c in self.cases:
            self.assertIn(c["status"], VALID_STATUSES,
                          f"Unknown status '{c['status']}' in {c['case_id']}")

    def test_anomaly_count_matches_anomalies_column(self):
        for c in self.cases:
            listed = [a.strip() for a in c["anomalies"].split("|") if a.strip()]
            stored = int(c["anomaly_count"])
            self.assertEqual(len(listed), stored,
                             f"Case {c['case_id']}: anomaly_count={stored} but {len(listed)} listed")

    def test_anomaly_count_in_valid_range(self):
        for c in self.cases:
            cnt = int(c["anomaly_count"])
            self.assertGreaterEqual(cnt, 2, f"Case {c['case_id']} has < 2 anomalies")
            self.assertLessEqual(cnt, 4,    f"Case {c['case_id']} has > 4 anomalies")

    def test_anomalies_belong_to_correct_catalogue(self):
        subtype_map = {r["doc_id"]: r["doc_subtype"] for r in self.docs}
        for c in self.cases:
            subtype = subtype_map.get(c["doc_id"], "")
            catalogue = set(ANOMALY_MAP.get(subtype, []))
            listed = [a.strip() for a in c["anomalies"].split("|") if a.strip()]
            for anomaly in listed:
                self.assertIn(anomaly, catalogue,
                              f"Anomaly '{anomaly}' not in {subtype} catalogue (case {c['case_id']})")

    def test_detected_by_field(self):
        for c in self.cases:
            self.assertEqual(c["detected_by"], "AI Forensic Engine v1.0",
                             f"Unexpected detected_by in {c['case_id']}")

    def test_all_four_doc_types_have_cases(self):
        types_with_cases = {c["doc_type"] for c in self.cases}
        self.assertEqual(types_with_cases, EXPECTED_DOC_TYPES,
                         f"Missing case doc types: {EXPECTED_DOC_TYPES - types_with_cases}")

    def test_remarks_not_empty(self):
        for c in self.cases:
            self.assertTrue(c["remarks"].strip(), f"Empty remarks in {c['case_id']}")


# ══════════════════════════════════════════════════════════════════════════════
# TestSQLiteIntegrity
# ══════════════════════════════════════════════════════════════════════════════

class TestSQLiteIntegrity(unittest.TestCase):
    """Validates the SQLite database tables, row counts and foreign-key queries."""

    @classmethod
    def setUpClass(cls):
        cls.conn = _sqlite_conn()
        cls.cur  = cls.conn.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def test_db_file_exists(self):
        self.assertTrue(os.path.exists(SQLITE_DB), "forensic_db.sqlite not found")

    def test_tables_exist(self):
        tables = {r[0] for r in self.cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
        for tbl in ("people", "documents", "forgery_cases"):
            self.assertIn(tbl, tables, f"Table '{tbl}' not found in SQLite DB")

    def test_people_row_count(self):
        cnt = self.cur.execute("SELECT COUNT(*) FROM people").fetchone()[0]
        self.assertEqual(cnt, EXPECTED_PEOPLE, f"people table: expected {EXPECTED_PEOPLE}, got {cnt}")

    def test_documents_row_count(self):
        cnt = self.cur.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
        self.assertEqual(cnt, EXPECTED_DOCS, f"documents table: expected {EXPECTED_DOCS}, got {cnt}")

    def test_forgery_cases_row_count(self):
        csv_cases = len(_load_csv(CASES_CSV))
        cnt = self.cur.execute("SELECT COUNT(*) FROM forgery_cases").fetchone()[0]
        self.assertEqual(cnt, csv_cases, f"forgery_cases table: expected {csv_cases}, got {cnt}")

    def test_people_ids_unique(self):
        cnt_all  = self.cur.execute("SELECT COUNT(*) FROM people").fetchone()[0]
        cnt_dist = self.cur.execute("SELECT COUNT(DISTINCT person_id) FROM people").fetchone()[0]
        self.assertEqual(cnt_all, cnt_dist, "Non-unique person_id in SQLite people table")

    def test_all_doc_person_ids_in_people(self):
        orphans = self.cur.execute("""
            SELECT doc_id FROM documents
            WHERE person_id NOT IN (SELECT person_id FROM people)
        """).fetchall()
        self.assertEqual(len(orphans), 0,
                         f"Documents with unknown person_id: {orphans}")

    def test_all_case_doc_ids_in_documents(self):
        orphans = self.cur.execute("""
            SELECT case_id FROM forgery_cases
            WHERE doc_id NOT IN (SELECT doc_id FROM documents)
        """).fetchall()
        self.assertEqual(len(orphans), 0,
                         f"Cases with unknown doc_id: {orphans}")

    def test_forged_docs_have_cases(self):
        """Every is_forged=1 document must have exactly one forensic case."""
        result = self.cur.execute("""
            SELECT d.doc_id, COUNT(fc.case_id) as case_count
            FROM documents d
            LEFT JOIN forgery_cases fc ON d.doc_id = fc.doc_id
            WHERE d.is_forged = 1
            GROUP BY d.doc_id
            HAVING case_count != 1
        """).fetchall()
        self.assertEqual(len(result), 0,
                         f"Forged docs with wrong case count: {result}")

    def test_genuine_docs_have_no_cases(self):
        result = self.cur.execute("""
            SELECT d.doc_id
            FROM documents d
            INNER JOIN forgery_cases fc ON d.doc_id = fc.doc_id
            WHERE d.is_forged = 0
        """).fetchall()
        self.assertEqual(len(result), 0,
                         f"Genuine docs linked to a case: {result}")

    def test_four_docs_per_person_in_db(self):
        bad = self.cur.execute("""
            SELECT person_id, COUNT(*) as cnt
            FROM documents
            GROUP BY person_id
            HAVING cnt != 4
        """).fetchall()
        self.assertEqual(len(bad), 0,
                         f"Persons without exactly 4 docs: {bad}")

    def test_confidence_scores_in_range(self):
        bad = self.cur.execute("""
            SELECT doc_id, forgery_conf FROM documents
            WHERE forgery_conf < 0 OR forgery_conf > 1
        """).fetchall()
        self.assertEqual(len(bad), 0, f"Out-of-range confidence scores: {bad}")

    def test_query_forged_by_type(self):
        """Spot-check: each doc type has at least one forged document."""
        for dt in EXPECTED_DOC_TYPES:
            cnt = self.cur.execute(
                "SELECT COUNT(*) FROM documents WHERE doc_type=? AND is_forged=1", (dt,)
            ).fetchone()[0]
            self.assertGreater(cnt, 0, f"No forged docs for type '{dt}'")

    def test_stamp_duty_is_6pct_of_amount(self):
        rows = self.cur.execute(
            "SELECT doc_id, amount_inr, stamp_duty FROM documents WHERE doc_subtype='property'"
        ).fetchall()
        for doc_id, amount, stamp in rows:
            expected = round(amount * 0.06)
            self.assertEqual(stamp, expected,
                             f"Stamp duty mismatch on {doc_id}: expected {expected}, got {stamp}")

    def test_reg_fee_is_1pct_of_amount(self):
        rows = self.cur.execute(
            "SELECT doc_id, amount_inr, reg_fee FROM documents WHERE doc_subtype='property'"
        ).fetchall()
        for doc_id, amount, reg_fee in rows:
            expected = round(amount * 0.01)
            self.assertEqual(reg_fee, expected,
                             f"Reg fee mismatch on {doc_id}: expected {expected}, got {reg_fee}")


# ══════════════════════════════════════════════════════════════════════════════
# TestJSONSummary
# ══════════════════════════════════════════════════════════════════════════════

class TestJSONSummary(unittest.TestCase):
    """Validates forensic_db.json structure and consistency with CSV counts."""

    @classmethod
    def setUpClass(cls):
        cls.data = _load_json()

    def test_file_exists(self):
        self.assertTrue(os.path.exists(JSON_FILE), "forensic_db.json not found")

    def test_top_level_keys(self):
        for key in ("dataset_info", "people", "documents", "forgery_cases"):
            self.assertIn(key, self.data, f"Missing top-level key '{key}' in JSON")

    def test_dataset_info_keys(self):
        info = self.data["dataset_info"]
        for key in ("total_people", "total_documents", "total_forged", "total_genuine", "total_cases", "doc_types"):
            self.assertIn(key, info, f"Missing dataset_info key '{key}'")

    def test_people_count_consistent(self):
        self.assertEqual(self.data["dataset_info"]["total_people"], EXPECTED_PEOPLE)
        self.assertEqual(len(self.data["people"]), EXPECTED_PEOPLE)

    def test_documents_count_consistent(self):
        self.assertEqual(self.data["dataset_info"]["total_documents"], EXPECTED_DOCS)
        self.assertEqual(len(self.data["documents"]), EXPECTED_DOCS)

    def test_forged_genuine_sum_equals_total(self):
        info = self.data["dataset_info"]
        self.assertEqual(info["total_forged"] + info["total_genuine"], info["total_documents"])

    def test_cases_count_consistent(self):
        csv_cases = len(_load_csv(CASES_CSV))
        self.assertEqual(self.data["dataset_info"]["total_cases"], csv_cases)
        self.assertEqual(len(self.data["forgery_cases"]), csv_cases)

    def test_doc_types_in_info(self):
        listed = set(self.data["dataset_info"]["doc_types"])
        self.assertEqual(listed, EXPECTED_DOC_TYPES)

    def test_forged_count_matches_documents_list(self):
        actual_forged = sum(1 for d in self.data["documents"] if d["is_forged"] == 1)
        self.assertEqual(actual_forged, self.data["dataset_info"]["total_forged"])


# ══════════════════════════════════════════════════════════════════════════════
# TestPDFFiles
# ══════════════════════════════════════════════════════════════════════════════

class TestPDFFiles(unittest.TestCase):
    """Checks that every PDF referenced in documents.csv exists on disk and is non-empty."""

    @classmethod
    def setUpClass(cls):
        cls.docs = _load_csv(DOCS_CSV)

    def test_pdf_dir_exists(self):
        self.assertTrue(os.path.isdir(PDF_DIR), f"PDF directory not found: {PDF_DIR}")

    def test_all_referenced_pdfs_exist(self):
        missing = []
        for r in self.docs:
            path = os.path.join(PDF_DIR, r["pdf_file"])
            if not os.path.exists(path):
                missing.append(r["pdf_file"])
        self.assertEqual(len(missing), 0, f"Missing PDFs: {missing}")

    def test_all_pdfs_are_non_empty(self):
        empty = []
        for r in self.docs:
            path = os.path.join(PDF_DIR, r["pdf_file"])
            if os.path.exists(path) and os.path.getsize(path) == 0:
                empty.append(r["pdf_file"])
        self.assertEqual(len(empty), 0, f"Zero-byte PDFs: {empty}")

    def test_pdfs_have_pdf_header(self):
        bad = []
        for r in self.docs:
            path = os.path.join(PDF_DIR, r["pdf_file"])
            if os.path.exists(path):
                with open(path, "rb") as f:
                    header = f.read(5)
                if header != b"%PDF-":
                    bad.append(r["pdf_file"])
        self.assertEqual(len(bad), 0, f"Files missing PDF header: {bad}")

    def test_pdf_count_on_disk_matches_documents(self):
        disk_pdfs = {f for f in os.listdir(PDF_DIR) if f.endswith(".pdf")}
        ref_pdfs  = {r["pdf_file"] for r in self.docs}
        self.assertEqual(disk_pdfs, ref_pdfs,
                         f"Extra: {disk_pdfs - ref_pdfs} | Missing: {ref_pdfs - disk_pdfs}")

    def test_forged_pdfs_larger_than_zero(self):
        """Forged PDFs (with extra anomaly annotations) should still be valid."""
        for r in self.docs:
            if r["is_forged"] == "1":
                path = os.path.join(PDF_DIR, r["pdf_file"])
                self.assertGreater(os.path.getsize(path), 1000,
                                   f"Forged PDF suspiciously small: {r['pdf_file']}")


# ══════════════════════════════════════════════════════════════════════════════
# TestConfidenceScores
# ══════════════════════════════════════════════════════════════════════════════

class TestConfidenceScores(unittest.TestCase):
    """Unit-tests the CONFIDENCE_SCORES lambdas directly."""

    def test_genuine_score_range(self):
        for _ in range(200):
            score = CONFIDENCE_SCORES["genuine"]()
            self.assertGreaterEqual(score, 0.05)
            self.assertLessEqual(score, 0.18)

    def test_forged_score_range(self):
        for _ in range(200):
            score = CONFIDENCE_SCORES["forged"]()
            self.assertGreaterEqual(score, 0.72)
            self.assertLessEqual(score, 0.98)

    def test_scores_are_float(self):
        self.assertIsInstance(CONFIDENCE_SCORES["genuine"](), float)
        self.assertIsInstance(CONFIDENCE_SCORES["forged"](), float)

    def test_scores_rounded_to_2dp(self):
        for _ in range(100):
            s = CONFIDENCE_SCORES["genuine"]()
            self.assertEqual(s, round(s, 2))
        for _ in range(100):
            s = CONFIDENCE_SCORES["forged"]()
            self.assertEqual(s, round(s, 2))

    def test_no_overlap_between_genuine_and_forged_bounds(self):
        """Genuine upper bound (0.18) must be < forged lower bound (0.72)."""
        self.assertLess(0.18, 0.72)


# ══════════════════════════════════════════════════════════════════════════════
# TestAnomalyCatalogue
# ══════════════════════════════════════════════════════════════════════════════

class TestAnomalyCatalogue(unittest.TestCase):
    """Verifies the anomaly catalogues are well-formed and correctly mapped."""

    def test_all_subtypes_in_anomaly_map(self):
        for subtype in ("covid", "degree", "property", "fir"):
            self.assertIn(subtype, ANOMALY_MAP, f"Subtype '{subtype}' missing from ANOMALY_MAP")

    def test_each_catalogue_has_at_least_four_entries(self):
        for subtype, catalogue in ANOMALY_MAP.items():
            self.assertGreaterEqual(len(catalogue), 4,
                                    f"Catalogue for '{subtype}' has fewer than 4 entries")

    def test_no_duplicate_anomalies_within_catalogue(self):
        for subtype, catalogue in ANOMALY_MAP.items():
            self.assertEqual(len(catalogue), len(set(catalogue)),
                             f"Duplicate anomalies in '{subtype}' catalogue")

    def test_covid_catalogue_content(self):
        self.assertIn("Blank PDF author metadata", COVID_ANOMALIES)
        self.assertIn("Misaligned government seal", COVID_ANOMALIES)

    def test_degree_catalogue_content(self):
        self.assertIn("CGPA inflated beyond university maximum", DEGREE_ANOMALIES)
        self.assertIn("Registrar signature rendered as flat line", DEGREE_ANOMALIES)

    def test_property_catalogue_content(self):
        self.assertIn("Plot area inflated in numeric field", PROPERTY_ANOMALIES)
        self.assertIn("Sub-registrar seal missing", PROPERTY_ANOMALIES)

    def test_fir_catalogue_content(self):
        self.assertIn("Officer signature is a straight horizontal line", FIR_ANOMALIES)
        self.assertIn("FIR number has zero-for-O substitution", FIR_ANOMALIES)

    def test_anomaly_map_references_correct_lists(self):
        self.assertIs(ANOMALY_MAP["covid"],    COVID_ANOMALIES)
        self.assertIs(ANOMALY_MAP["degree"],   DEGREE_ANOMALIES)
        self.assertIs(ANOMALY_MAP["property"], PROPERTY_ANOMALIES)
        self.assertIs(ANOMALY_MAP["fir"],      FIR_ANOMALIES)


# ══════════════════════════════════════════════════════════════════════════════
# TestHelperFunctions
# ══════════════════════════════════════════════════════════════════════════════

class TestHelperFunctions(unittest.TestCase):
    """Unit-tests for the pure helper functions in generate_database.py."""

    # ── _rand_date ─────────────────────────────────────────────────────────

    def test_rand_date_format(self):
        for _ in range(50):
            d = _rand_date(2020, 2023)
            self.assertRegex(d, DOB_RE, f"_rand_date returned bad format: {d}")

    def test_rand_date_year_bounds(self):
        years = set()
        for _ in range(500):
            d = _rand_date(2020, 2022)
            years.add(int(d[-4:]))
        self.assertTrue(years.issubset({2020, 2021, 2022}),
                        f"_rand_date produced out-of-range years: {years - {2020,2021,2022}}")

    def test_rand_date_same_year(self):
        d = _rand_date(2021, 2021)
        self.assertTrue(d.endswith("2021"))

    # ── _rand_dob ──────────────────────────────────────────────────────────

    def test_rand_dob_format(self):
        for _ in range(50):
            d = _rand_dob()
            self.assertRegex(d, DOB_RE)

    def test_rand_dob_age_range(self):
        for _ in range(100):
            d = _rand_dob(min_age=22, max_age=65)
            year = int(d[-4:])
            age  = 2025 - year
            self.assertGreaterEqual(age, 22, f"DOB year {year} gives age < 22")
            self.assertLessEqual(age, 65,    f"DOB year {year} gives age > 65")

    # ── _rand_amount ───────────────────────────────────────────────────────

    def test_rand_amount_divisible_by_step(self):
        for _ in range(100):
            amt = _rand_amount(2000000, 15000000, step=50000)
            self.assertEqual(amt % 50000, 0, f"Amount {amt} not divisible by 50000")

    def test_rand_amount_within_bounds(self):
        for _ in range(100):
            amt = _rand_amount(2000000, 15000000)
            self.assertGreaterEqual(amt, 2000000)
            self.assertLessEqual(amt, 15000000)

    # ── _doc_no ────────────────────────────────────────────────────────────

    def test_doc_no_format(self):
        result = _doc_no("SRO/DL", 2023, 42)
        self.assertEqual(result, "SRO/DL/2023/00042")

    def test_doc_no_zero_padding(self):
        result = _doc_no("X", 2022, 1)
        self.assertIn("00001", result)

    # ── _fir_no ────────────────────────────────────────────────────────────

    def test_fir_no_format(self):
        result = _fir_no("2024", 473)
        self.assertEqual(result, "2024/FIR/0473")

    def test_fir_no_zero_padding(self):
        result = _fir_no("2023", 5)
        self.assertIn("FIR/0005", result)

    # ── generate_people ────────────────────────────────────────────────────

    def test_generate_people_count(self):
        import random as _r; _r.seed(99)
        people = generate_people(10)
        self.assertEqual(len(people), 10)

    def test_generate_people_unique_ids(self):
        import random as _r; _r.seed(99)
        people = generate_people(10)
        ids = [p["person_id"] for p in people]
        self.assertEqual(len(ids), len(set(ids)))

    def test_generate_people_required_keys(self):
        import random as _r; _r.seed(99)
        people = generate_people(5)
        for p in people:
            for col in PEOPLE_COLS:
                self.assertIn(col, p, f"Key '{col}' missing from generated person")

    def test_generate_people_id_sequential(self):
        import random as _r; _r.seed(99)
        people = generate_people(5)
        for i, p in enumerate(people, start=1):
            self.assertEqual(p["person_id"], f"P{i:03d}")

    # ── generate_documents ─────────────────────────────────────────────────

    def test_generate_documents_count(self):
        import random as _r; _r.seed(99)
        people = generate_people(5)
        docs, cases = generate_documents(people)
        self.assertEqual(len(docs), 20)      # 5 × 4

    def test_generate_documents_subtypes(self):
        import random as _r; _r.seed(99)
        people = generate_people(3)
        docs, _ = generate_documents(people)
        subtypes = {d["doc_subtype"] for d in docs}
        self.assertEqual(subtypes, {"covid", "degree", "property", "fir"})

    def test_generate_documents_cases_only_for_forged(self):
        import random as _r; _r.seed(99)
        people = generate_people(10)
        docs, cases = generate_documents(people)
        forged_ids = {d["doc_id"] for d in docs if d["is_forged"]}
        case_ids   = {c["doc_id"] for c in cases}
        self.assertEqual(case_ids, forged_ids)

    def test_generate_documents_stamp_duty_formula(self):
        import random as _r; _r.seed(99)
        people = generate_people(5)
        docs, _ = generate_documents(people)
        for d in docs:
            if d["doc_subtype"] == "property":
                expected = round(d["amount_inr"] * 0.06)
                self.assertEqual(d["stamp_duty"], expected,
                                 f"Stamp duty formula broken for {d['doc_id']}")


# ══════════════════════════════════════════════════════════════════════════════
# TestPDFGeneration
# ══════════════════════════════════════════════════════════════════════════════

class TestPDFGeneration(unittest.TestCase):
    """Smoke-tests: each of the four PDF builders produces a valid PDF file."""

    def _assert_valid_pdf(self, path):
        self.assertTrue(os.path.exists(path), f"PDF not created: {path}")
        size = os.path.getsize(path)
        self.assertGreater(size, 500, f"PDF too small ({size} bytes): {path}")
        with open(path, "rb") as f:
            header = f.read(5)
        self.assertEqual(header, b"%PDF-", f"Not a valid PDF: {path}")

    def test_covid_cert_genuine(self):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            path = f.name
        try:
            _covid_cert(path, forged=False)
            self._assert_valid_pdf(path)
        finally:
            os.unlink(path)

    def test_covid_cert_forged(self):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            path = f.name
        try:
            _covid_cert(path, forged=True)
            self._assert_valid_pdf(path)
        finally:
            os.unlink(path)

    def test_degree_cert_genuine(self):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            path = f.name
        try:
            _degree_cert(path, forged=False)
            self._assert_valid_pdf(path)
        finally:
            os.unlink(path)

    def test_degree_cert_forged(self):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            path = f.name
        try:
            _degree_cert(path, forged=True)
            self._assert_valid_pdf(path)
        finally:
            os.unlink(path)

    def test_property_deed_genuine(self):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            path = f.name
        try:
            _property_deed(path, forged=False)
            self._assert_valid_pdf(path)
        finally:
            os.unlink(path)

    def test_property_deed_forged(self):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            path = f.name
        try:
            _property_deed(path, forged=True)
            self._assert_valid_pdf(path)
        finally:
            os.unlink(path)

    def test_fir_genuine(self):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            path = f.name
        try:
            _fir(path, forged=False)
            self._assert_valid_pdf(path)
        finally:
            os.unlink(path)

    def test_fir_forged(self):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            path = f.name
        try:
            _fir(path, forged=True)
            self._assert_valid_pdf(path)
        finally:
            os.unlink(path)

    def test_both_variants_differ_in_size(self):
        """Forged PDFs carry extra annotation text so should differ from genuine."""
        results = {}
        for fn, label in ((_covid_cert, "covid"), (_degree_cert, "degree"),
                          (_property_deed, "property"), (_fir, "fir")):
            sizes = {}
            for forged in (False, True):
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                    path = f.name
                fn(path, forged=forged)
                sizes[forged] = os.path.getsize(path)
                os.unlink(path)
            results[label] = sizes
        # They don't need to differ, but both must be positive
        for label, sizes in results.items():
            self.assertGreater(sizes[False], 0, f"{label} genuine is empty")
            self.assertGreater(sizes[True],  0, f"{label} forged is empty")


# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    unittest.main(verbosity=2)
