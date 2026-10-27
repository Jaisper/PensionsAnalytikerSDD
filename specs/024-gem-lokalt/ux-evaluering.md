# UX-evaluering: Gem og genindlæs lokalt

**Dato**: 2026-10-27 · **Metode**: browsertests (`tests/browser/test_gem.py`), headless Chrome.

| Måling | Resultat | Krav |
|---|---|---|
| Gem → åbn i et nyt vindue giver de samme svar og det samme hovedtal | ja (test) | SC |
| Filen har ingen persondata i klartekst (fødselsdato, kommune, ordninger) | ja (test) | SC, Princip VII |
| Forkert adgangskode giver en klar fejl og intet resultat | ja (test) | FR-002 |
| For kort eller forskellig adgangskode afvises ved feltet | ja (test) | FR-002 |
| axe med formularen åben | 0 fejl | Princip X |

## Heuristik (kort)

- **Ærlighed:** Teksten siger før gemningen, at en glemt adgangskode ikke kan genskabes.
- **Synlighed:** Efter åbning står der, at beregningen er fra en bestemt dato og regnet med årets
  regler.

## Åbne fund

| # | Fund | Alv. |
|---|---|---|
| G1 | Ældre skemaversioner findes endnu ikke. Når guiden ændres, skal der være en oversættelse og en testfil pr. version (FR-003) | 1 |
