# Kontrakt: HTTP-API

| Metode | Sti | Beskrivelse |
|---|---|---|
| GET | `/` | Brugerfladen (statisk HTML) |
| GET | `/api/kommuner` | `[{"noegle": "aarhus", "navn": "Aarhus"}, …]`, sorteret efter navn |
| POST | `/api/beregn` | Guidedata → visningsmodel (data-model.md). 422 ved ugyldigt input |

## Garantier

- **A1**: Ingen persistens. Requesten behandles i hukommelsen, og body logges ikke.
- **A2**: Alle tal i svaret stammer fra `pensionskerne.beregn` og registret (FR-001/002).
- **A3**: `beregningsdato` sættes af serveren (dags dato). Kernen modtager den eksplicit.
- **A4**: Svaret på `POST /api/beregn` kommer på under 1 s for en profil med 10 ordninger
  (SC-005).
