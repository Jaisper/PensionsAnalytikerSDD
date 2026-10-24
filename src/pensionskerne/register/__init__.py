"""Regelregister: alle lovbestemte satser som data (Forfatningens Princip II).

Én TOML-fil pr. satsår (`<år>.toml`) plus `kommuner_<år>.toml`. Kun læsning.
"""
from __future__ import annotations

import tomllib
from dataclasses import dataclass
from functools import lru_cache
from importlib import resources
from typing import Any

from ..model import UgyldigtInput

STATUSSER = ("verificeret", "sekundaer", "uverificeret")
ENHEDER = ("brok", "kr_aar", "aar", "antal", "dato", "tabel")


@dataclass(frozen=True)
class Registerpost:
    id: str
    vaerdi: Any
    enhed: str
    kilde: str
    status: str
    reguleres: bool


@dataclass(frozen=True)
class Kommuneregister:
    satser: dict[str, float]
    kirkeskat: dict[str, float]
    aliaser: dict[str, str]
    kilde: str
    status: str


def normaliser_kommune(navn: str) -> str:
    return (navn.strip().lower()
            .replace("æ", "ae").replace("ø", "o").replace("å", "a")
            .replace("-", "").replace(" ", "").replace(".", ""))


def _filer() -> list[str]:
    return [f.name for f in resources.files(__package__).iterdir() if f.name.endswith(".toml")]


def satsaar() -> list[int]:
    return sorted(int(n.removesuffix(".toml")) for n in _filer() if n.removesuffix(".toml").isdigit())


def _laes(navn: str) -> dict:
    return tomllib.loads(resources.files(__package__).joinpath(navn).read_text(encoding="utf-8"))


@lru_cache(maxsize=None)
def _poster(aar: int) -> dict[str, Registerpost]:
    if aar not in satsaar():
        raise UgyldigtInput("satsaar", f"Satsår {aar} findes ikke i regelregistret (findes: {satsaar()})")
    data = _laes(f"{aar}.toml")
    poster: dict[str, Registerpost] = {}
    for p in data["post"]:
        post = Registerpost(
            id=p["id"], vaerdi=p["vaerdi"], enhed=p["enhed"], kilde=p["kilde"],
            status=p["status"], reguleres=bool(p.get("reguleres", False)),
        )
        if post.status not in STATUSSER:
            raise ValueError(f"{post.id}: ukendt status {post.status}")
        if post.enhed not in ENHEDER:
            raise ValueError(f"{post.id}: ukendt enhed {post.enhed}")
        if post.id in poster:
            raise ValueError(f"{post.id}: dubleret id")
        poster[post.id] = post
    return poster


def post(aar: int, id: str) -> Registerpost:
    poster = _poster(aar)
    if id not in poster:
        raise KeyError(f"Registerpost '{id}' findes ikke for satsår {aar}")
    return poster[id]


def poster(aar: int) -> list[Registerpost]:
    return list(_poster(aar).values())


@lru_cache(maxsize=None)
def kommuneregister(aar: int) -> Kommuneregister:
    _poster(aar)  # validerer satsåret
    data = _laes(f"kommuner_{aar}.toml")
    return Kommuneregister(
        satser=dict(data["satser"]), kirkeskat=dict(data["kirkeskat"]), aliaser=dict(data.get("aliaser", {})),
        kilde=data["kilde"], status=data["status"],
    )


def kommuner(aar: int) -> dict[str, float]:
    reg = kommuneregister(aar)
    return {**reg.satser, **{alias: reg.satser[maal] for alias, maal in reg.aliaser.items()}}


def kommune_noegle(aar: int, navn: str) -> str | None:
    """Kanonisk kommunenøgle (aliaser opløst) eller None, hvis kommunen er ukendt."""
    reg = kommuneregister(aar)
    n = normaliser_kommune(navn)
    n = reg.aliaser.get(n, n)
    return n if n in reg.satser else None
