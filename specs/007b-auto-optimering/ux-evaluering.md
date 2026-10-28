# UX-evaluering: Den bedste plan med det samme (007b)

**Dato**: 2026-10-28 · **Metode**: browsertests (`tests/browser/test_auto_optimering.py`), headless Chrome.

| Måling | Resultat | Krav |
|---|---|---|
| Den bedste plan er hovedtallet efter guiden, med egen plans beløb nedenunder | ja (test) | FR-004 |
| Flyttede ordninger starter tidligst ved folkepensionsalderen (ingen stopalder) | ja (test) | SC-001 |
| Hovedtallet er mindst lige så højt som med egen plan | ja (test) | SC-002 |
| Skift til egen plan og tilbage giver præcis svarene | ja (test) | SC-003 |
| axe med planlinjen og ændringslisten åben | 0 fejl | Princip X |

## Åbne fund

| # | Fund | Alv. |
|---|---|---|
| P1 | Planlinjen vises kun under fanen "Dig"; partnerens ændringer står i listen, men partnerens egen-plan-beløb vises ikke | 2 |
| P2 | Hovedtallet kommer først efter optimeringen (ca. 3–4 s); imens står din egen plans tal med en fremdriftslinje | 1 |
| P3 | "Opdater beregningen" kører ikke optimeringen (borgerens egne valg overskrives ikke); brug "Find bedste plan" | 1 |
