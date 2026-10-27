"""Feature 020 T001 — forenklingsregistret (FR-005, FR-006): hver forenkling i kernen er beskrevet."""
import re
from pathlib import Path

from pensionskerne import register

KERNE = Path(__file__).resolve().parents[2] / "src" / "pensionskerne"
MARKERING = re.compile(r'marker\("forenkling:([a-z0-9_]+)"\)')


def markeringer() -> set[str]:
    return {m for f in KERNE.rglob("*.py") for m in MARKERING.findall(f.read_text(encoding="utf-8"))}


def test_hver_markering_i_kernen_findes_i_registret():
    ids = {f.id for f in register.forenklinger()}
    assert markeringer() and markeringer() <= ids, markeringer() - ids


def test_hver_markeret_post_bruges_af_kernen():
    markerede = {f.id for f in register.forenklinger() if f.omfang == "markeret"}
    assert markerede == markeringer()


def test_alle_felter_er_udfyldt_og_id_er_unikke():
    poster = register.forenklinger()
    assert len({f.id for f in poster}) == len(poster)
    for f in poster:
        assert f.omfang in ("markeret", "altid"), f.id
        for felt in ("titel", "beskrivelse", "begrundelse", "betydning", "kilde"):
            assert getattr(f, felt).strip(), (f.id, felt)
