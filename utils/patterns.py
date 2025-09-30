"""
Regex patterns for Microsoft Jobs Scraper

This module contains all regex patterns used throughout the scraper.
"""

import re

# Job parsing patterns
JOB_ID_FROM_ARIA = re.compile(r"Job item\s+(\d+)")
ISO_DATE_RE = re.compile(r"(20\d{2})-(\d{2})-(\d{2})")

# Pay and salary patterns
USD_RANGE = re.compile(r"USD\s*\$\s*[\d,]+\s*-\s*\$\s*[\d,]+", re.I)
PAY_START = re.compile(
    r"(typical\s+base\s+pay\s+range|base\s+pay\s+range\s+for\s+this\s+role|benefits\s+and\s+pay\s+information|USD\s*\$\s*[\d,]+\s*-\s*\$\s*[\d,]+)",
    re.I
)

# Qualification section patterns
REQ_RE = re.compile(r"\bRequired\s+Qualifications\b", re.I)
PREF_RE = re.compile(r"\bPreferred\s+Qualifications\b", re.I)
OTHER_RE = re.compile(r"\bOther\s+Requirements?\b", re.I)