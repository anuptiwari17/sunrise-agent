"""Safety screener and intent classifier.

Provides deterministic detection of:
- Clinical Emergencies (clinical_urgent) - THE HARD RULE
- Medical Advice Requests (medical_advice)
- Prompt Injection / Admin Overrides (refused)
- Abandoned / Empty / Noise Conversations (abandoned)
"""

from __future__ import annotations

import re
from typing import List, Optional, Tuple

# Emergency / Urgent clinical symptoms in Hindi, Hinglish, and English
CLINICAL_URGENT_PATTERNS = [
    r"\bseene\s+mein\s+dard\b",
    r"\bchhati\s+mein\s+dard\b",
    r"\bchest\s+pain\b",
    r"\bheart\s+attack\b",
    r"\bsaans\s+(?:thodi\s+)?phool\b",
    r"\bsaans\s+lene\s+mein\s+(?:takleef|dikkat|pareshani)\b",
    r"\bshortness\s+of\s+breath\b",
    r"\bbreathless(?:ness)?\b",
    r"\bchoking\b",
    r"\bbehosh\b",
    r"\bunconscious\b",
    r"\bfainting\b",
    r"\bkhoon\s+bah\s+raha\b",
    r"\bsevere\s+bleeding\b",
    r"\bprofuse\s+bleeding\b",
    r"\bseizure\b",
    r"\bdaura\s+pad\b",
    r"\bparalysis\b",
    r"\bstroke\b",
    r"\bpoison(?:ing)?\b",
    r"\bzehar\b",
    r"\barm\s+(?:thodi\s+)?numb\b",
    r"\bhaath\s+(?:sunn|numb)\b",
    r"\bchakkar\b",
]

# Medical advice queries (asking for clinical opinion or prescription adjustments)
MEDICAL_ADVICE_PATTERNS = [
    r"\bgoli\s+le\s+lun\b",
    r"\bcrocin\b",
    r"\bparacetamol\b",
    r"\bibuprofen\b",
    r"\bmedicine\s+(?:dose|dosage|should\s+i\s+take)\b",
    r"\bkitni\s+der\s+mein\s+utar\s+jana\s+chahiye\b",
    r"\bkitna\s+ml\b",
    r"\bshould\s+i\s+take\s+another\b",
    r"\bmedical\s+advice\b",
    r"\bdawa\s+kaunsi\b",
    r"\bdawai\s+batao\b",
]

# Prompt injection / jailbreak / system override attempts
PROMPT_INJECTION_PATTERNS = [
    r"\bignore\s+(?:your\s+)?previous\s+instructions\b",
    r"\badministrator\s+mode\b",
    r"\badmin\s+mode\b",
    r"\bcancel\s+every\s+appointment\b",
    r"\bdelete\s+all\b",
    r"\bdrop\s+database\b",
    r"\bprompt\s+injection\b",
    r"\bjailbreak\b",
    r"\bauthorised\s+internal\s+test\b",
    r"\boverride\s+standard\s+validation\b",
    r"\bemergency\s+slot\s+for\s+patient\b",
    r"\bbypass\s+verification\b",
]

# Non-actionable noise turns
NOISE_WORDS = {
    "hello",
    "haan",
    "ji",
    "haan ji",
    "arre",
    "background noise",
    "theek hai",
    "sun rahe ho",
    "kya aap sun rahe hain",
}


def check_clinical_urgent(turns: List[str]) -> bool:
    """Checks if any turn mentions an acute emergency symptom."""
    for turn in turns:
        clean = turn.lower()
        for pat in CLINICAL_URGENT_PATTERNS:
            if re.search(pat, clean):
                return True
    return False


def check_medical_advice(turns: List[str]) -> bool:
    """Checks if caller is asking for clinical advice instead of reception tasks."""
    combined = " ".join(turns).lower()
    for pat in MEDICAL_ADVICE_PATTERNS:
        if re.search(pat, combined):
            return True
    return False


def check_prompt_injection(turns: List[str]) -> bool:
    """Checks for prompt injection or admin override attempts."""
    for turn in turns:
        clean = turn.lower()
        for pat in PROMPT_INJECTION_PATTERNS:
            if re.search(pat, clean):
                return True
    return False


def check_abandoned_call(turns: List[str]) -> bool:
    """Checks if the caller never stated a meaningful request or just hung up."""
    # If all turns are short greetings or filler
    meaningful = False
    combined = " ".join(turns).lower()
    
    # Check if there's any action intent
    action_keywords = [
        "appointment",
        "dr",
        "doctor",
        "milna",
        "dikhana",
        "cancel",
        "reschedule",
        "book",
        "tareekh",
        "baje",
        "subah",
        "shaam",
        "dard",
        "bukhar",
    ]
    for kw in action_keywords:
        if kw in combined:
            meaningful = True
            break

    return not meaningful
