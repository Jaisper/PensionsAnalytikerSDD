# UX-evaluering: Kør i browseren

**Dato**: 2026-10-25 · **Metode**: headless Chrome mod den byggede `_site/` (serveret med
`Cache-Control: max-age=600` som GitHub Pages), axe-core 4.9.1 og lokal kørsel med en rigtig
rapport. Intet blev gemt.

## Målinger

| Måling | Resultat | Krav |
|---|---|---|
| Første besøg klar til at regne (lokalt) | 2,8 s | SC-002 < 8 s |
| Andet besøg klar (cache) | 2,4 s | SC-002 < 3 s |
| Skyder → nyt hovedtal (inkl. 300 ms debounce, 5 målinger) | 0,36–0,39 s | SC-003 < 1 s |
| Requests efter indlæsning i et helt forløb | 0 | SC-001 |
| Rigtig rapport: aflæsning i browseren mod CPython | identisk (5 ordninger, 6 rækker) | FR-007 |
| axe (resultatside og indlæsningsbanner ved 360 px) | 0 overtrædelser | SC-005 |
| Vandret scroll ved 360 px | nej | SC-005 |

Første besøg over et rigtigt netværk afhænger af forbindelsen (cirka 15 MB komprimeret). Det
måles på den udgivne side.

## Heuristik (kort)

- **Synlighed (1):** Banneret "Gør beregningen klar …" har en statuslinje og `role="status"`,
  og det forsvinder, når motoren er klar.
- **Fleksibilitet (7):** Guiden kan udfyldes, mens motoren indlæses, og "Se min pension" før
  den er klar regner automatisk, når den bliver klar.
- **Fejlhåndtering (9):** Fejl i indlæsningen eller fristen giver en dansk besked og "Prøv
  igen". En browser uden WebAssembly får besked om at bruge en nyere browser.
- **Tillid:** "Vi gemmer dem ikke" er nu bogstaveligt sandt. Data forlader ikke browseren.

## Åbne fund

| # | Fund | Alv. |
|---|---|---|
| C1 | Siden fortæller ikke borgeren, at beregningen sker lokalt. Det kunne styrke tilliden (fx under upload) | 1 |
| C2 | Første besøg på en langsom mobilforbindelse er ikke målt endnu (måles efter udgivelse) | 1 |
