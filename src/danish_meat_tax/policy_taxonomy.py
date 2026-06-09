from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable


@dataclass(frozen=True)
class TreatmentAssignment:
    commodity: str
    treated: bool
    treatment_group: str
    policy_confidence: str
    matched_terms: tuple[str, ...]
    food_status: str = "food"
    analysis_role: str = "control_food"


GROUP_RULES: tuple[tuple[str, bool, str, str, str, tuple[str, ...]], ...] = (
    ("beef", True, "beef", "core", "treated_livestock_meat", ("beef", "okse", "oksekoed", "kvaeg", "kalv", "kalve", "veal", "entrecote", "roastbeef")),
    ("pork", True, "pork", "core", "treated_livestock_meat", ("pork", "svin", "gris", "flaesk", "bacon", "skinke", "kamsteg", "medister")),
    ("lamb_sheep_goat", True, "lamb_sheep_goat", "livestock_scope", "treated_livestock_meat", ("lamb", "lam", "lamm", "lammekolle", "faar", "sheep", "ged", "goat")),
    ("dairy", True, "dairy_cattle", "livestock_scope", "treated_livestock_dairy", ("milk", "maelk", "cheese", "ost", "yoghurt", "yogurt", "smoer", "butter", "flode", "cream", "skyr")),
    ("poultry", False, "control_poultry", "control", "control_food", ("chicken", "kylling", "hoene", "turkey", "kalkun", "duck", "andebryst")),
    ("fish_seafood", False, "control_fish_seafood", "control", "control_food", ("fish", "fisk", "salmon", "laks", "cod", "torsk", "shrimp", "rejer", "tun")),
    ("eggs", False, "control_animal_products", "control", "control_food", ("egg", "eggs", "aeg")),
    ("fruit_vegetables", False, "control_non_meat", "control", "control_food", ("apple", "aeble", "banana", "banan", "tomat", "tomato", "potato", "kartoffel", "salat", "gulerod", "onion", "loeg", "agurk", "peberfrugt", "frugt", "groent")),
    ("grains_bread", False, "control_non_meat", "control", "control_food", ("bread", "broed", "rugbroed", "pasta", "rice", "ris", "oats", "havre", "flour", "mel", "bolle", "boller", "kage")),
    ("fats_oils", False, "control_non_meat", "control", "control_food", ("oil", "olie", "margarine")),
    ("sweets_snacks", False, "control_non_meat", "control", "control_food", ("chocolate", "chokolade", "chips", "slik", "cookie", "kiks", "is")),
    ("beverages", False, "control_non_meat", "control", "control_food", ("coffee", "kaffe", "tea", "te", "juice", "soda", "cola", "vand", "water", "saft")),
    ("plant_protein", False, "control_non_meat", "control", "control_food", ("tofu", "linser", "beans", "boenner", "falafel", "kikarter")),
)

MIXED_TERMS = ("pizza", "lasagne", "gryderet", "ready meal", "faerdigret", "mix", "sandwich")
NON_FOOD_TERMS = (
    "shampoo",
    "tandpasta",
    "toiletpapir",
    "koekkenrulle",
    "vaskemiddel",
    "opvask",
    "rengoering",
    "saebe",
    "serviet",
    "bleer",
    "kattemad",
    "hundemad",
    "batteri",
    "lighter",
    "deodorant",
    "bodylotion",
    "plaster",
    "vitamin",
)


def _normalize(text: str) -> str:
    normalized = text.casefold()
    replacements = {
        "æ": "ae",
        "ø": "o",
        "å": "aa",
        "ö": "o",
        "ä": "ae",
        "ü": "u",
        "Ã¦": "ae",
        "Ã¸": "o",
        "Ã¥": "aa",
        "Ã¶": "o",
        "Ã¤": "ae",
    }
    for old, new in replacements.items():
        normalized = normalized.replace(old, new)
    return normalized


def _matches(text: str, terms: Iterable[str]) -> tuple[str, ...]:
    found: list[str] = []
    for term in terms:
        normalized_term = _normalize(term)
        if len(normalized_term) <= 3:
            pattern = r"(?<![a-zA-Z])" + re.escape(normalized_term) + r"(?![a-zA-Z])"
            matched = bool(re.search(pattern, text))
        else:
            matched = normalized_term in text
        if matched:
            found.append(term)
    return tuple(found)


def classify_product(name: str, category: str | None = None) -> TreatmentAssignment:
    haystack = _normalize(" ".join(part for part in (name, category or "") if part))
    if not haystack.strip():
        return TreatmentAssignment("unknown", False, "unknown", "unknown", (), "unknown", "exclude_unknown")

    non_food_matches = _matches(haystack, NON_FOOD_TERMS)
    if non_food_matches:
        return TreatmentAssignment(
            "non_food",
            False,
            "exclude_non_food",
            "exclude_non_food",
            non_food_matches,
            "non_food",
            "exclude_non_food",
        )

    mixed = bool(_matches(haystack, MIXED_TERMS))
    matches: list[TreatmentAssignment] = []
    for commodity, treated, group, confidence, role, terms in GROUP_RULES:
        found = _matches(haystack, terms)
        if found:
            if mixed and treated:
                confidence = "ambiguous_mixed"
            matches.append(TreatmentAssignment(commodity, treated, group, confidence, found, "food", role))

    if not matches:
        return TreatmentAssignment("unknown", False, "unknown", "unknown", (), "unknown", "exclude_unknown")

    treated_matches = [match for match in matches if match.treated]
    if len(treated_matches) > 1:
        terms = tuple(term for match in treated_matches for term in match.matched_terms)
        return TreatmentAssignment("mixed_meat", True, "mixed_livestock", "ambiguous_mixed", terms, "food", "treated_livestock_meat")

    return treated_matches[0] if treated_matches else matches[0]
