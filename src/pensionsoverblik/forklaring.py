"""Forklaringskataloget (feature 020): tekster pr. emne på tre niveauer.

Kun ord og pladsholdere. Brugerfladen udfylder pladsholderne med kernens tal (Princip I og II).
Kataloget må gerne bruges af en senere AI-funktion, fordi det ikke indeholder borgerens tal
(Princip XI); de udfyldte tekster må ikke.
"""
from __future__ import annotations

import tomllib
from functools import lru_cache
from importlib import resources


@lru_cache(maxsize=None)
def katalog() -> dict:
    data = tomllib.loads(resources.files(__package__).joinpath("forklaringer.toml").read_text(encoding="utf-8"))
    return {"inventar": data["inventar"], "emner": data["emne"]}
