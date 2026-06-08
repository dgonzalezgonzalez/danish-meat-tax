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


GROUP_RULES: tuple[tuple[str, bool, str, str, tuple[str, ...]], ...] = (
    ("beef", True, "beef", "core", ("beef", "okse", "kvæg", "kvaeg", "kalv", "veal", "entrecote")),
    ("pork", True, "pork", "core", ("pork", "svin", "gris", "flæsk", "flaesk", "bacon", "skinke")),
    ("lamb_sheep_goat", True, "lamb_sheep_goat", "livestock_scope", ("lamb", "lam", "lamm", "lammekolle", "får", "faar", "sheep", "ged", "goat")),
    ("poultry", True, "poultry_other_livestock", "sensitivity", ("chicken", "kylling", "høne", "hoene", "turkey", "kalkun", "duck", "andebryst")),
    ("fish_seafood", False, "control_fish_seafood", "control", ("fish", "fisk", "salmon", "laks", "cod", "torsk", "shrimp", "rejer")),
    ("eggs", False, "control_animal_products", "control", ("egg", "eggs", "æg", "aeg")),
    ("dairy", False, "control_animal_products", "control", ("milk", "mælk", "maelk", "cheese", "ost", "yoghurt", "yogurt", "smør", "smoer", "butter")),
    ("fruit_vegetables", False, "control_non_meat", "control", ("apple", "æble", "aeble", "banana", "banan", "tomat", "tomato", "potato", "kartoffel", "salat", "gulerod", "onion", "løg", "loeg")),
    ("grains_bread", False, "control_non_meat", "control", ("bread", "brød", "broed", "rugbrød", "rugbroed", "pasta", "rice", "ris", "oats", "havre", "flour", "mel")),
    ("fats_oils", False, "control_non_meat", "control", ("oil", "olie", "margarine")),
    ("sweets_snacks", False, "control_non_meat", "control", ("chocolate", "chokolade", "chips", "slik", "cookie", "kiks")),
    ("beverages", False, "control_non_meat", "control", ("coffee", "kaffe", "tea", "te", "juice", "soda", "cola", "vand", "water")),
    ("plant_protein", False, "control_non_meat", "control", ("tofu", "linser", "beans", "bønner", "boenner", "falafel")),
)

MIXED_TERMS = ("pizza", "lasagne", "gryderet", "ready meal", "færdigret", "faerdigret", "mix")


def _normalize(text: str) -> str:
    normalized = text.casefold()
    replacements = {
        "æ": "ae",
        "ø": "o",
        "å": "aa",
        "ö": "o",
        "ä": "ae",
        "ř": "o",
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
    mixed = bool(_matches(haystack, MIXED_TERMS))
    matches: list[TreatmentAssignment] = []
    for commodity, treated, group, confidence, terms in GROUP_RULES:
        found = _matches(haystack, terms)
        if found:
            if mixed and treated:
                confidence = "ambiguous_mixed"
            matches.append(TreatmentAssignment(commodity, treated, group, confidence, found))

    if not matches:
        return TreatmentAssignment("unknown", False, "unknown", "unknown", ())

    treated_matches = [match for match in matches if match.treated]
    if len(treated_matches) > 1:
        terms = tuple(term for match in treated_matches for term in match.matched_terms)
        return TreatmentAssignment("mixed_meat", True, "mixed_livestock", "ambiguous_mixed", terms)

    return treated_matches[0] if treated_matches else matches[0]
