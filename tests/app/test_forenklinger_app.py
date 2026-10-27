"""Feature 020 T002 — visningen viser forenklingerne: de anvendte markerede først, derefter dem,
der altid gælder."""
import json

from pensionskerne import register
from pensionsoverblik import app
from tests.app.test_husstand_app import IDAG
from tests.app.test_oversaet import GUIDE


def forenklinger(guide):
    return app.beregn(json.dumps(guide), IDAG)["data"]["forenklinger"]


def test_altid_gaeldende_er_med_og_ubrugte_markerede_ikke():
    f = forenklinger(GUIDE)
    altid = {p.id for p in register.forenklinger() if p.omfang == "altid"}
    assert altid <= {x["id"] for x in f}
    assert all(x["anvendt"] or x["omfang"] == "altid" for x in f)
    assert {"titel", "beskrivelse", "begrundelse", "betydning"} <= set(f[0])


def test_anvendt_markering_staar_oeverst():
    # Opsparing og første udbetaling som 65-årig (født 1963): opsparingen vokser frem til da,
    # og skatten af afkastet i de år er ikke regnet med (013).
    guide = {**GUIDE, "person": {**GUIDE["person"], "opsparing": [{"id": "bank", "saldo": 100000}]}}
    f = forenklinger(guide)
    assert f[0]["id"] == "opsparing_skat_foer_udbetaling" and f[0]["anvendt"]
    # Uden opsparing gælder kun "Ingen løn" (borgeren er under folkepensionsalderen, 017).
    assert [x["id"] for x in forenklinger(GUIDE) if x["anvendt"]] == ["ingen_loen"]
