# Implementation Plan: Indlæsning af PensionsInfo-rapport

**Branch**: `003-pdf-import` | **Date**: 2026-10-24 | **Spec**: [spec.md](spec.md)

## Summary

`POST /api/pdf` modtager PDF-bytes direkte som request-body (ingen multipart-afhængighed) og
headeren `X-Samtykke: ja`. Flowet er:

1. `pdfplumber` udtrækker teksten i hukommelsen.
2. Relevante sider filtreres fra, CPR-numre fjernes, og fødselsdatoen udledes lokalt.
3. Claude Opus 5.5 aflæser teksten med et fast JSON-schema og refusal-fallback.
4. En deterministisk omsætning laver guidedata med kilde og usikkerheder.
5. Frontenden udfylder guiden.

## Technical Context

- **Afhængigheder** (gruppe `app`):
  - `pdfplumber` (tekstudtræk, som i legacy)
  - `anthropic` 2.3 (officielt SDK)
- **Model**: `claude-opus-5-5`, `effort: medium`, adaptiv tænkning (standard),
  `output_config.format` med JSON-schema, `fallbacks: "default"` (beta
  `server-side-fallback-2026-07-01`), timeout 90 s og ét genforsøg.
- **Udskiftelig aflæser**: Protokollen `Aflaeser` med Claude-implementeringen og en falsk
  implementering til test. API'et vælger Claude, når `ANTHROPIC_API_KEY` eller
  `ANTHROPIC_AUTH_TOKEN` er sat. Ellers er funktionen slået fra.

## Constitution Check

| # | Princip | Status |
|---|---|---|
| I | AI'en aflæser kun tekst til formularfelter. Den beregner ingenting, og brugeren tjekker alt før beregning | ✅ |
| II | Folkepensionsalder til udledning af oprettelsesperiode hentes fra registret | ✅ |
| III | Ingen nye regler | ✅ |
| IV | Tests for tekst og CPR, omsætning og API med falsk aflæser skrives før implementeringen | ✅ |
| V | Kilde og usikkerheder pr. ordning | ✅ |
| VI | Kernen er uændret | ✅ |
| VII | CPR fjernes lokalt, samtykke ved handlingen, ingen disk og ingen logs. Test for ingen filer | ✅ |
| VIII | Danske fejlbeskeder | ✅ |
| IX | To afhængigheder (begrundet ovenfor). Ingen multipart-bibliotek | ✅ |
| X | Upload-kort i guiden med samtykke, fremdrift, fejl med næste skridt og usikkerheder ved felterne | ✅ |

## Structure

```text
src/pensionsoverblik/pdfimport/
├── __init__.py
├── tekst.py      # PDF → tekst, sidefilter, CPR-fjernelse og fødselsdato
├── aflaeser.py   # Aflaeser-protokol, skema, ClaudeAflaeser
└── omsaet.py     # aflæsning → guidedata med kilde og usikkerheder
tests/app/
├── test_pdf_tekst.py
├── test_pdf_omsaet.py
└── test_pdf_api.py
```

## Complexity Tracking

Ingen overtrædelser.
