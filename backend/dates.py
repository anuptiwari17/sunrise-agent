"""Deterministic date and Hinglish time resolver.

ALL calculations are anchored to the request's 'today' date string (YYYY-MM-DD).
NEVER uses datetime.now() or date.today().
"""

from __future__ import annotations

import datetime
import re
from typing import Dict, List, Optional, Tuple

WEEKDAYS_HINDI_MAP = {
    "somwar": 0,
    "somvaar": 0,
    "monday": 0,
    "mon": 0,
    "mangalwar": 1,
    "mangalvaar": 1,
    "tuesday": 1,
    "tue": 1,
    "budhwar": 2,
    "budhvaar": 2,
    "wednesday": 2,
    "wed": 2,
    "guruwar": 3,
    "guruvaar": 3,
    "veerwar": 3,
    "veervaar": 3,
    "thursday": 3,
    "thu": 3,
    "shukrawar": 4,
    "shukravaar": 4,
    "friday": 4,
    "fri": 4,
    "shanivaar": 5,
    "shaniwar": 5,
    "saturday": 5,
    "sat": 5,
    "ravivar": 6,
    "ravivaar": 6,
    "itwar": 6,
    "itvaar": 6,
    "sunday": 6,
    "sun": 6,
}

HINDI_NUMBERS = {
    "ek": 1,
    "do": 2,
    "teen": 3,
    "chaar": 4,
    "char": 4,
    "paanch": 5,
    "panch": 5,
    "chheh": 6,
    "che": 6,
    "saat": 7,
    "sat": 7,
    "aath": 8,
    "ath": 8,
    "nau": 9,
    "no": 9,
    "das": 10,
    "dus": 10,
    "gyarah": 11,
    "gyara": 11,
    "barah": 12,
    "bara": 12,
}


def parse_reference_date(today_str: str) -> datetime.date:
    """Parses reference today string 'YYYY-MM-DD'."""
    return datetime.datetime.strptime(today_str, "%Y-%m-%d").date()


def resolve_relative_date(text: str, today_str: str) -> Optional[str]:
    """Resolves relative date words ('kal', 'parso', 'aaj', 'Shanivaar', '3 tareekh')
    anchored to today_str.
    """
    clean_text = text.lower()
    ref_date = parse_reference_date(today_str)

    # 1. Direct explicit dates YYYY-MM-DD
    iso_match = re.search(r"\b(202\d-\d{2}-\d{2})\b", clean_text)
    if iso_match:
        return iso_match.group(1)

    # 2. Mind changes: if text contains "nahi nahi, <date>" or "nahi ... <date>"
    # E.g. "Mangalwar 6 tareekh ko... nahi nahi, budhwar kar dijiye, 7 tareekh."
    # If there's a correction phrase, prioritize the text AFTER the correction!
    correction_split = re.split(r"\bnahi\s+nahi\b|\bnahi\b", clean_text)
    if len(correction_split) > 1 and correction_split[-1].strip():
        # Check if the tail contains date info
        tail_date = resolve_relative_date(correction_split[-1], today_str)
        if tail_date:
            return tail_date

    # 3. Explicit day of month: e.g. "3 tareekh", "6 tareekh", "7 tareekh", "8 tareekh", "3rd", "3 October"
    tareekh_match = re.search(r"\b(\d{1,2})\s*(?:tareekh|tarikh|st|nd|rd|th|october|oct)?\b", clean_text)
    # Be careful not to treat clock times like "10 baje" or phone numbers as tareekh
    tareekh_explicit = re.search(r"\b(\d{1,2})\s*(?:tareekh|tarikh)\b", clean_text)
    if tareekh_explicit:
        day_num = int(tareekh_explicit.group(1))
        # Keep same year and month as today
        try:
            target = ref_date.replace(day=day_num)
            # If target day is before today in the same month, could be next month or same month
            return target.strftime("%Y-%m-%d")
        except ValueError:
            pass

    # 4. Check for Hindi / English weekday names first if used as target day (e.g. "use Saturday karwana hai")
    target_weekday_found = None
    for word, target_weekday in WEEKDAYS_HINDI_MAP.items():
        if re.search(rf"\b{word}\b", clean_text):
            current_weekday = ref_date.weekday()
            days_ahead = (target_weekday - current_weekday) % 7
            if days_ahead == 0 and not re.search(r"\baaj\b|\btoday\b", clean_text):
                days_ahead = 7  # Next week if today is same weekday and not referring to today
            elif days_ahead == 0:
                days_ahead = 0
            target = ref_date + datetime.timedelta(days=days_ahead)
            target_weekday_found = target.strftime("%Y-%m-%d")
            break

    if target_weekday_found:
        return target_weekday_found

    # 5. Check for 'parso' (day after tomorrow = +2 days)
    if re.search(r"\bparso\b|\bparson\b|\bday after tomorrow\b", clean_text):
        target = ref_date + datetime.timedelta(days=2)
        return target.strftime("%Y-%m-%d")

    # 6. Check for 'kal' (tomorrow = +1 day)
    if re.search(r"\bkal\b|\btomorrow\b", clean_text):
        target = ref_date + datetime.timedelta(days=1)
        return target.strftime("%Y-%m-%d")

    # 7. Check for 'aaj' (today)
    if re.search(r"\baaj\b|\btoday\b", clean_text):
        return ref_date.strftime("%Y-%m-%d")

    # 8. Check for explicit "N October"
    oct_match = re.search(r"\b(\d{1,2})\s*(?:october|oct)\b", clean_text)
    if oct_match:
        day_num = int(oct_match.group(1))
        try:
            target = ref_date.replace(month=10, day=day_num)
            return target.strftime("%Y-%m-%d")
        except ValueError:
            pass

    return None


def resolve_clock_time(text: str) -> Optional[str]:
    """Resolves clock times ('10 baje', '9:30', 'gyarah baje', 'shaam 5 baje')."""
    clean_text = text.lower()

    # 1. Corrections mid-sentence: prioritize text after 'nahi'
    correction_split = re.split(r"\bnahi\s+nahi\b|\bnahi\b", clean_text)
    if len(correction_split) > 1 and correction_split[-1].strip():
        tail_time = resolve_clock_time(correction_split[-1])
        if tail_time:
            return tail_time

    # 2. Look for explicit HH:MM pattern (e.g. 09:30, 9:30, 10:00, 17:00)
    time_match = re.search(r"\b([012]?\d):([0-5]\d)\b", clean_text)
    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2))
        return f"{hour:02d}:{minute:02d}"

    # 3. Look for "N baje" or "N:00"
    is_shaam = bool(re.search(r"\bshaam\b|\bevening\b|\bdopahar\b|\bafternoon\b", clean_text))
    is_subah = bool(re.search(r"\bsubah\b|\bmorning\b", clean_text))

    baje_match = re.search(r"\b(\d{1,2})\s*baje\b", clean_text)
    if baje_match:
        hour = int(baje_match.group(1))
        # If shaam/evening and hour < 12, add 12 (e.g. 5 baje -> 17:00, 8 baje -> 20:00)
        if is_shaam and hour < 12:
            hour += 12
        return f"{hour:02d}:00"

    # 4. Look for Hindi word numbers + "baje" or alone in time context
    for word, hour in HINDI_NUMBERS.items():
        if re.search(rf"\b{word}\s+baje\b", clean_text):
            if is_shaam and hour < 12:
                hour += 12
            return f"{hour:02d}:00"

    # 5. Look for "parso gyarah baje" or "gyarah baje" without spaces
    for word, hour in HINDI_NUMBERS.items():
        if re.search(rf"\b{word}\b", clean_text) and ("aa sakta hoon" in clean_text or "time" in clean_text or "milna" in clean_text):
            return f"{hour:02d}:00"

    return None
