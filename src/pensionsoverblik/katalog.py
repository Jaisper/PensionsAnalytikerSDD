"""Tekster og placeringer til brugerfladen: korttyper og advarselskatalog (data-model.md).

Kun ord og placeringer — ingen tal. Satser vises altid fra regelregistret (Princip II).
"""

KORT: dict[str, dict[str, str]] = {
    "folkepension": {
        "titel": "Folkepension",
        "forklaring": "Grundbeløb og pensionstillæg fra staten. Tillægget bliver mindre, jo mere "
                      "anden indkomst du har.",
        "farve": "--kilde-folkepension",
    },
    "atp": {
        "titel": "ATP",
        "forklaring": "Livslang pension fra ATP, som de fleste har betalt til gennem arbejdet.",
        "farve": "--kilde-atp",
    },
    "ratepension": {
        "titel": "Ratepension",
        "forklaring": "Udbetales over et fast antal år. Beløbet stiger lidt hvert år, fordi resten "
                      "af opsparingen fortsat forrentes.",
        "farve": "--kilde-rate",
    },
    "livsvarig": {
        "titel": "Livsvarig pension",
        "forklaring": "Udbetales hver måned resten af livet.",
        "farve": "--kilde-livsvarig",
    },
    "checks": {
        "titel": "Ældrecheck og mediecheck",
        "forklaring": "Ekstra ydelser til folkepensionister med lav indkomst og lille formue. "
                      "Udbetales én gang om året.",
        "farve": "--kilde-checks",
    },
}

ENGANGSKORT = {
    "titel": "Engangsbeløb",
    "forklaring": "Aldersopsparing og kapitalpension udbetales som ét beløb. I det jævne beløb øverst "
                  "er pengene fordelt ud over årene.",
    "farve": "--kilde-engangs",
}

KORT_FOR_KILDETYPE: dict[str, str] = {
    "grundbeloeb": "folkepension",
    "pensionstillaeg": "folkepension",
    "atp": "atp",
    "ratepension": "ratepension",
    "livsvarig": "livsvarig",
    "aeldrecheck": "checks",
    "mediecheck": "checks",
}

# Korttyper, hvor det første år typisk kun er et delår (udbetaling fra måneden efter
# fødselsdagen / checks kræver folkepension pr. 1. januar).
DELAAR_FOERST = {"folkepension", "atp"}

ADVARSLER: dict[str, dict[str, str]] = {
    "ATP_SKOENNET": {"placering": "atp", "ikon": "≈", "titel": "ATP er et skøn"},
    "RATEPENSION_LOFT": {"placering": "ratepension", "ikon": "!", "titel": "Over loftet for ratepension"},
    "750_TIMER": {"placering": "folkepension", "ikon": "!", "titel": "Krav om arbejde"},
    "OPSAT_ANDRE_FORMER": {"placering": "folkepension", "ikon": "≈", "titel": "Andre udbetalingsformer"},
    "MELLEMSKAT_INTERVAL": {"placering": "graf", "ikon": "!", "titel": "Høj skat i nogle år"},
    "BUFFER_SOM_OPSPARING": {"placering": "hovedtal", "ikon": "≈", "titel": "Bufferen er opsparing"},
    "BUFFER_IKKE_KONVERGERET": {"placering": "hovedtal", "ikon": "!", "titel": "Usikkert tal"},
    "UDBETALING_FOER_LOVLIG_ALDER": {"placering": "generel", "ikon": "!", "titel": "Tjek din startalder"},
    "PORTIONER_KRAEVER_AFTALE": {"placering": "generel", "ikon": "≈", "titel": "Kapitalpension i portioner"},
    "OMLAEGNING_KRAEVER_OVERFOERSEL": {"placering": "generel", "ikon": "≈", "titel": "Omlægning af kapitalpension"},
}

UKENDT_ADVARSEL = {"placering": "generel", "ikon": "!", "titel": "Bemærk"}
