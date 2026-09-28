"""
Local forensic analysis engine.
No external API required — all scoring and classification is rule-based.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Tuple
import re


# ---------------------------------------------------------------------------
# Examination standards mapped to anomaly categories
# ---------------------------------------------------------------------------
STANDARDS_MAP: Dict[str, Dict] = {
    "font_inconsistency": {
        "standard": "ASTM E2285 / OSAC FDE Standard",
        "description": "Examination of typefaces, font metrics, and typographic consistency",
        "indicators": [
            "Mixed font families within a single typed field",
            "Inconsistent character baseline alignment",
            "Non-uniform letter spacing (kerning anomalies)",
            "Pixel-level anti-aliasing mismatch between sections",
            "Resampling or compression artifacts around inserted text",
        ],
    },
    "signature_mismatch": {
        "standard": "SWGMAT / ASTM E2290",
        "description": "Questioned document examination of signatures and handwriting",
        "indicators": [
            "Pen lift inconsistencies compared to reference specimens",
            "Unnatural line quality or tremor suggesting tracing",
            "Proportional anomalies relative to known exemplars",
            "Ink density variation inconsistent with natural writing speed",
            "Misalignment of signature relative to document baseline",
        ],
    },
    "paper_anomaly": {
        "standard": "ISO/IEC 14443 / ASTM E2289",
        "description": "Physical substrate and paper examination",
        "indicators": [
            "Watermark absence or misalignment",
            "Security thread displacement or forgery",
            "Paper grain direction inconsistency",
            "UV-fluorescence anomalies",
            "Indentation analysis revealing prior text",
        ],
    },
    "ink_spread": {
        "standard": "ASTM E2926 / SWGMAT Ink Standards",
        "description": "Ink and toner analysis for alteration detection",
        "indicators": [
            "Ink feathering inconsistent with paper stock",
            "Toner adhesion anomalies suggesting photocopier fraud",
            "Chemical erasure residue detected via ESDA or IR",
            "Obliteration or overwriting patterns",
            "Multiple ink types detected in a single continuous entry",
        ],
    },
    "digital_metadata": {
        "standard": "ISO 32000 / NIST SP 800-86 (Digital Forensics)",
        "description": "Digital metadata and file integrity analysis",
        "indicators": [
            "Creation/modification timestamp discrepancy",
            "Author field inconsistent with stated issuer",
            "Software version metadata mismatch",
            "Embedded thumbnail does not match document content",
            "Hash value mismatch or absent digital signature",
        ],
    },
}

# Anomaly keyword triggers per category
KEYWORD_TRIGGERS: Dict[str, List[str]] = {
    "font_inconsistency": [
        "font", "typeface", "character", "spacing", "kerning", "baseline",
        "bold", "italic", "size", "pixel", "blurry", "artifact", "resampl",
        "compress", "dpi", "resolution", "text block", "inserted text",
    ],
    "signature_mismatch": [
        "signature", "sign", "handwriting", "pen", "tremor", "tracing",
        "traced", "exemplar", "ink flow", "line quality", "lifted", "lift",
        "proportion", "loop", "forgery", "copied", "rubber stamp",
    ],
    "paper_anomaly": [
        "paper", "watermark", "thread", "substrate", "grain", "uv",
        "fluorescence", "indentation", "texture", "fibre", "fiber",
        "security feature", "emboss", "stamp", "seal", "torn", "aged",
    ],
    "ink_spread": [
        "ink", "toner", "feather", "bleed", "spread", "erasure", "erase",
        "obliterat", "overwrite", "chemical", "smear", "correction fluid",
        "white out", "whiteout", "alteration", "altered",
    ],
    "digital_metadata": [
        "metadata", "timestamp", "date", "author", "software", "pdf",
        "hash", "digital signature", "exif", "file", "modified", "created",
        "version", "thumbnail", "header", "embedded",
    ],
}

# Severity signal words that escalate confidence
HIGH_SEVERITY_WORDS = [
    "clear", "obvious", "definite", "confirmed", "multiple", "significant",
    "strong", "evident", "unmistakable", "severe", "several", "numerous",
]
LOW_SEVERITY_WORDS = [
    "slight", "minor", "possible", "potential", "faint", "subtle",
    "uncertain", "unclear", "maybe", "possibly", "could be",
]


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class AnomalyFinding:
    category: str
    label: str
    confidence: float          # 0.0 – 1.0
    confidence_label: str      # Low / Moderate / High / Very High
    matched_keywords: List[str]
    standard: str
    standard_description: str
    relevant_indicators: List[str]
    raw_observation: str


@dataclass
class AnalysisResult:
    document_type: str
    overall_confidence: float
    overall_confidence_label: str
    verdict: str               # "Genuine", "Suspected Forgery", "Confirmed Forgery"
    findings: List[AnomalyFinding]
    anomaly_count: int
    primary_anomaly: str
    examiner_notes: str


# ---------------------------------------------------------------------------
# Core analysis functions
# ---------------------------------------------------------------------------

def _classify_and_score(observation: str, category: str) -> Tuple[float, List[str]]:
    """
    Score a single observation text for a given category.
    Returns (raw_score 0-1, matched_keywords).
    """
    text = observation.lower()
    keywords = KEYWORD_TRIGGERS.get(category, [])
    matched = [kw for kw in keywords if kw in text]

    if not matched:
        return 0.0, []

    # Base score from keyword density
    base = min(len(matched) / max(len(keywords) * 0.25, 1), 1.0)

    # Severity modifiers
    severity_boost = sum(0.08 for w in HIGH_SEVERITY_WORDS if w in text)
    severity_penalty = sum(0.05 for w in LOW_SEVERITY_WORDS if w in text)

    # Observation length bonus (more detail = more confidence)
    length_bonus = min(len(text.split()) / 100, 0.15)

    score = min(base + severity_boost + length_bonus - severity_penalty, 1.0)
    return round(score, 3), matched


def _confidence_label(score: float) -> str:
    if score >= 0.75:
        return "Very High"
    if score >= 0.55:
        return "High"
    if score >= 0.35:
        return "Moderate"
    if score > 0.0:
        return "Low"
    return "None"


def _verdict(overall: float, anomaly_count: int) -> str:
    if overall >= 0.70 or anomaly_count >= 3:
        return "Confirmed Forgery"
    if overall >= 0.40 or anomaly_count >= 2:
        return "Suspected Forgery"
    if overall > 0.0:
        return "Inconclusive — Further Examination Required"
    return "No Anomalies Detected — Appears Genuine"


def _pick_relevant_indicators(category: str, matched_keywords: List[str]) -> List[str]:
    """Return the 3 most relevant standard indicators for the matched keywords."""
    all_indicators = STANDARDS_MAP[category]["indicators"]
    relevant = []
    for indicator in all_indicators:
        ind_lower = indicator.lower()
        if any(kw in ind_lower for kw in matched_keywords):
            relevant.append(indicator)
    # Always return at least 2 indicators
    if len(relevant) < 2:
        relevant = all_indicators[:3]
    return relevant[:4]


def analyze(
    document_type: str,
    font_obs: str,
    signature_obs: str,
    paper_obs: str,
    ink_obs: str,
    metadata_obs: str,
    examiner_notes: str,
) -> AnalysisResult:
    """
    Run local forensic analysis across all five observation categories.
    Returns a fully populated AnalysisResult.
    """
    observations = {
        "font_inconsistency": font_obs,
        "signature_mismatch": signature_obs,
        "paper_anomaly": paper_obs,
        "ink_spread": ink_obs,
        "digital_metadata": metadata_obs,
    }

    findings: List[AnomalyFinding] = []

    for category, obs in observations.items():
        if not obs or not obs.strip():
            continue

        score, matched = _classify_and_score(obs, category)
        if score == 0.0 and obs.strip():
            # Observation was given but no keywords matched — still flag with low confidence
            score = 0.15
            matched = []

        label_map = {
            "font_inconsistency": "Font & Typography Inconsistency",
            "signature_mismatch": "Signature / Handwriting Mismatch",
            "paper_anomaly": "Paper & Substrate Anomaly",
            "ink_spread": "Ink / Toner Alteration",
            "digital_metadata": "Digital Metadata Irregularity",
        }

        std = STANDARDS_MAP[category]
        findings.append(AnomalyFinding(
            category=category,
            label=label_map[category],
            confidence=score,
            confidence_label=_confidence_label(score),
            matched_keywords=matched,
            standard=std["standard"],
            standard_description=std["description"],
            relevant_indicators=_pick_relevant_indicators(category, matched),
            raw_observation=obs.strip(),
        ))

    # Overall confidence = weighted average (higher individual scores count more)
    if findings:
        scores = [f.confidence for f in findings]
        # Weighted: top finding contributes 40%, rest split 60%
        scores_sorted = sorted(scores, reverse=True)
        if len(scores_sorted) == 1:
            overall = scores_sorted[0]
        else:
            overall = scores_sorted[0] * 0.40 + sum(scores_sorted[1:]) / len(scores_sorted[1:]) * 0.60
        overall = round(min(overall, 1.0), 3)
    else:
        overall = 0.0

    anomaly_count = sum(1 for f in findings if f.confidence >= 0.35)
    primary = max(findings, key=lambda f: f.confidence).label if findings else "None"

    return AnalysisResult(
        document_type=document_type or "Unspecified Document",
        overall_confidence=overall,
        overall_confidence_label=_confidence_label(overall),
        verdict=_verdict(overall, anomaly_count),
        findings=findings,
        anomaly_count=anomaly_count,
        primary_anomaly=primary,
        examiner_notes=examiner_notes.strip() if examiner_notes else "",
    )
