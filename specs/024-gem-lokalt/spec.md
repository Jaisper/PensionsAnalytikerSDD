# Feature Specification: Gem og genindlæs lokalt

**Feature Branch**: `024-gem-lokalt`

**Created**: 2026-10-27

**Status**: Draft – modnes

**Input**: Idéliste punkt 10: "En krypteret fil i stedet for en server, så brugeren kan genbruge sin
profil uden at uploade PDF'en igen næste år. Det passer med Princip VII."

**Grundlag**:
- 020d: eksport som JSON (ukrypteret, hele beregningen) findes allerede.
- Princip VII (intet forlader browseren) og XI (ingen persondata til AI).
- Guidens svar (`tilstand.aktuelleSvar`) er hele inputtet.

## Problem

Borgeren skal indtaste alt igen ved hvert besøg eller indlæse PDF'en igen. En gemt fil gør det let
at fortsætte, men filen indeholder persondata (fødselsdato, saldi, løn) og skal beskyttes.

## Forslag til metode

- **Gem**: svarene (ikke resultatet) krypteres i browseren med Web Crypto: AES-GCM med en nøgle
  udledt af en adgangskode (PBKDF2-SHA-256 med mange iterationer og tilfældigt salt). Filen
  indeholder version, salt, nonce og ciffertekst.
- **Indlæs**: filen og adgangskoden giver svarene tilbage. Guiden udfyldes, og der regnes.
- **Version**: filen har et skemanummer. Ældre filer oversættes, så ændringer i guiden ikke bryder
  gamle filer.
- Ingen ny afhængighed: Web Crypto findes i alle moderne browsere.

## Clarifications (forslag i kursiv)

- [NEEDS CLARIFICATION: Skal adgangskoden være påkrævet? *Forslag: ja. Uden kryptering kan man
  bruge den eksisterende JSON-eksport, og det står tydeligt.*]
- [NEEDS CLARIFICATION: Hvad gemmes? *Forslag: kun svarene og valgene (niveau, kroner), ikke
  PDF'en og ikke resultatet. Resultatet regnes igen med årets satser.*]
- [NEEDS CLARIFICATION: Nyt satsår ved indlæsning? *Forslag: regn med det nyeste satsår og vis, at
  tallene kan have ændret sig siden sidst.*]
- [NEEDS CLARIFICATION: Glemt adgangskode? *Forslag: kan ikke genskabes, og det står ved
  gemningen.*]

## Requirements (udvalg)

- **FR-001**: Kryptering og dekryptering sker kun i browseren. Intet sendes ud.
- **FR-002**: Forkert adgangskode eller beskadiget fil giver en klar fejl og intet delvist resultat.
- **FR-003**: Filformatet er dokumenteret og testet med en fil fra hver skemaversion.
- **SC**: Gem → indlæs giver det samme resultat (test). Ingen persondata i klartekst i filen (test).

## Afhængigheder og størrelse

- Uafhængig. Lille. Kan laves når som helst.
