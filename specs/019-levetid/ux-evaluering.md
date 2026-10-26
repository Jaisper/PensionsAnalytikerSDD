# UX-evaluering: Levetid som scenarie

**Dato**: 2026-10-26 · **Metode**: browsertests (`tests/browser/test_usikkerhed.py`), headless Chrome,
og en lokal måling med syntetiske data.

| Måling | Resultat | Krav |
|---|---|---|
| Tabellen har rækkerne "Planen rækker til 85 år" og "Planen rækker til 95 år" og en kolonne for planens slutning | ja (test) | US1 |
| Livrenten er ens i alle planer | ja (golden) | US1, SC-002 |
| Sætningen "Lever du længere …" med indkomsten efter planen. Skjult under "Samlet" | ja (test) | US2 |
| Spændet under hovedtallet gælder kun afkast og inflation | ja (kode og test) | plan |
| Samme resultat i Pyodide og CPython | ja (test) | SC-003 |
| Otte scenarier i browseren | enlig 0,39 s, par 0,91 s | SC-004 < 3 s |

## Heuristik (kort)

- **Forståelse:** "Planen rækker til 95 år" siger, hvad der ændres. Det er en plan, ikke en
  forudsigelse af borgerens levetid.
- **Tryghed:** Sætningen om indkomsten efter planen svarer på den egentlige bekymring: "Hvad har
  jeg, hvis jeg lever længere?"

## Åbne fund

| # | Fund | Alv. |
|---|---|---|
| L1 | Indkomsten efter planen vises kun for én person ad gangen, ikke for parret samlet | 1 |
