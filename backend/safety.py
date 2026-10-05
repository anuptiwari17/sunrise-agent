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
    # Cardiovascular & Thoracic
    r"\bseene\s+mein\s+dard\b",
    r"\bchhati\s+mein\s+dard\b",
    r"\bchest\s+pain\b",
    r"\bheart\s+attack\b",
    r"\bangina\b",
    r"\bcrushing\s+pressure\b",
    r"\bseene\s+mein\s+dabav\b",
    # Respiratory Distress
    r"\bsaans\s+(?:thodi\s+|bohot\s+)?phool\b",
    r"\bsaans\s+lene\s+mein\s+(?:takleef|dikkat|pareshani)\b",
    r"\bsaans\s+nahi\s+aa\s+rahi\b",
    r"\bshortness\s+of\s+breath\b",
    r"\bbreathless(?:ness)?\b",
    r"\bchoking\b",
    r"\bgasping\b",
    r"\bdam\s+ghut\b",
    r"\bwheezing\b",
    r"\bcyanosis\b",
    r"\bneela\s+pad\s+gaya\b",
    r"\bblue\s+lips\b",
    # Neurological & Stroke
    r"\bbehosh\b",
    r"\bunconscious\b",
    r"\bfainting\b",
    r"\bpassed\s+out\b",
    r"\bchakkar\b",
    r"\bvertigo\b",
    r"\bblackout\b",
    r"\barm\s+(?:thodi\s+)?numb\b",
    r"\bhaath\s+(?:sunn|numb)\b",
    r"\bchehra\s+tedha\b",
    r"\bfacial\s+droop\b",
    r"\bslurred\s+speech\b",
    r"\bparalysis\b",
    r"\blakwa\b",
    r"\bstroke\b",
    r"\bseizure\b",
    r"\bdaura\s+pad\b",
    r"\bconvulsion\b",
    r"\bmirgi\b",
    # Severe Bleeding & Trauma
    r"\bkhoon\s+(?:bah|nikal)\s+raha\b",
    r"\bsevere\s+bleeding\b",
    r"\bprofuse\s+bleeding\b",
    r"\bkhoon\s+ki\s+ulti\b",
    r"\bvomiting\s+blood\b",
    r"\bhead\s+injury\b",
    r"\bsir\s+phat\s+gaya\b",
    r"\baccident\b",
    r"\bfracture\b",
    # Poisoning & Toxic Ingestion
    r"\bpoison(?:ing)?\b",
    r"\bzehar\b",
    r"\boverdose\b",
    # Acute Abdomen / Severe Pediatric
    r"\bpet\s+mein\s+asahaniya\s+dard\b",
    r"\bunbearable\s+stomach\s+pain\b",
    r"\bbaccha\s+saans\s+nahi\s+le\s+raha\b",
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


def is_symptom_negated(text: str, start: int, end: int) -> bool:
    """Checks if the matched symptom in text[start:end] is negated in its clause."""
    pre_text = text[max(0, start - 50):start].lower()
    clause_pre = re.split(r"[.,;!?\n]", pre_text)[-1]

    post_text = text[end:min(len(text), end + 50)].lower()
    clause_post = re.split(r"[.,;!?\n]", post_text)[0]

    # Check English pre-negation: 'no chest pain', 'without chest pain', 'denies chest pain'
    if re.search(r"\b(?:no|not|without|denies|denied|zero)\b", clause_pre):
        return True

    # Check Hindi pre-negation trigger like 'koi', 'kisi bhi prakar ki'
    has_hindi_prefix = bool(
        re.search(
            r"\b(?:koi|kisi\s+bhi\s+(?:prakar|tarah)\s+(?:ka|ki|ke)|kuchh\s+bhi)\b",
            clause_pre,
        )
    )

    # Check post-negation: 'nahi hai', 'nahi ho raha', 'absent'
    has_post_neg = bool(re.search(r"\b(?:nahi|nahin)\b", clause_post))

    if has_hindi_prefix and has_post_neg:
        return True
    if has_post_neg:
        return True

    return False


def check_clinical_urgent(turns: List[str]) -> bool:
    """Checks if any turn mentions an active acute emergency symptom (ignoring negated symptoms)."""
    for turn in turns:
        clean = turn.lower()
        for pat in CLINICAL_URGENT_PATTERNS:
            for match in re.finditer(pat, clean):
                start, end = match.span()
                # 'saans nahi aa rahi' already includes 'nahi' as the actual respiratory emergency
                if "saans" in pat and "nahi" in pat:
                    return True
                if not is_symptom_negated(clean, start, end):
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
