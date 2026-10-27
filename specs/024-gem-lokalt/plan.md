# Implementation Plan: 024 Gem og genindlæs lokalt

**Branch**: `024-gem-lokalt` | **Spec**: [spec.md](spec.md) | **Dato**: 2026-10-27

## Tekniske beslutninger

- **Kryptering**: Web Crypto i browseren. AES-GCM (256 bit) med en nøgle udledt af adgangskoden med
  PBKDF2-SHA-256, 600.000 iterationer og 16 bytes tilfældigt salt. Nonce på 12 bytes.
- **Filformat** (JSON): `format` ("pensionsoverblik-gem"), `version` (1), `kdf` (navn, iterationer,
  salt), `cipher` (navn, iv) og `data` (ciffertekst i base64). Intet andet står i klartekst.
- **Indhold** (krypteret): `skema` (1), `gemt` (dato), `felter` (guidens felter id → værdi,
  radioknapper som `radio:<navn>`), ordningerne for dig og partneren, id-tællerne og valgene
  (forklaringsniveau, dagens/årets kroner).
  - Felterne gemmes generelt. Nye felter i guiden kommer med uden at ændre formatet.
  - Resultatet gemmes ikke. Det regnes igen med årets satser, og borgeren får det at vide.
- **Brugerflade**:
  - "Gem til senere" ligger ved eksportknapperne. Der skal skrives en adgangskode på mindst 8 tegn
    to gange, og der står, at den ikke kan genskabes.
  - På startsiden ligger "Har du gemt en beregning før?" med fil, adgangskode og knappen "Åbn".
- **Fejl**: forkert adgangskode, en fil, der ikke er gemt her, eller et ukendt skema giver én klar
  besked og intet delvist resultat.

## Constitution check

- **Princip VII**: kryptering, dekryptering og fil sker kun i browseren. Ingen ny afhængighed.
- **Princip XI**: ingen persondata til AI. Filen har ingen persondata i klartekst (test).
