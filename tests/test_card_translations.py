"""Guard against untranslated card text slipping in from upstream.

This fork keeps the Lovelace card Dutch. Every upstream release adds strings,
and finding them by hand is unreliable: in v2.3.0 the `Close details` and
`Reset view` buttons were nearly missed because they are button text rather
than the `<span>` labels the other options use.

So the rule is mechanical instead: every user-visible string in the card must
appear in APPROVED below. A new upstream string fails this test, and the fix is
to translate it and add it here - never to add the English original.
"""

from pathlib import Path
import re

CARD = (
    Path(__file__).parent.parent
    / 'custom_components'
    / 'flightradar24'
    / 'frontend'
    / 'flightradar24-card.js'
)

# Each pattern captures one user-visible string. Together they cover the ways
# the card emits text: element bodies, option labels, direct property writes
# and template literals.
PATTERNS = (
    re.compile(r'<(?:span|label)>\s*([^<>{][^<>]*?)\s*</(?:span|label)>'),
    re.compile(r'<button[^>]*>\s*([^<>{][^<>]*?)\s*</button>'),
    re.compile(r'<option[^>]*>\s*([A-Za-z][^<>{]*?)\s*</option>'),
    re.compile(r'label:\s*"([^"]+)"'),
    re.compile(r'(?:textContent|title)\s*=\s*"([^"]+)"'),
    re.compile(r'(?:textContent|title)\s*=\s*`([^`]+)`'),
    re.compile(r'(?:title|aria-label|placeholder)="([^"{]+)"'),
    re.compile(r'new Error\("([^"]+)"\)'),
    re.compile(r'\?\s*`([A-Za-z][^`]*?)\s*\$\{'),
)

INTERPOLATION = re.compile(r'\$\{[^}]*\}')

# Dutch text this fork owns.
TRANSLATED = {
    'Geef een entiteit op',
    'Openen op Flightradar24',
    'Geen vliegtuigen in de buurt',
    'Deze entiteit heeft nog geen geldig bounds-attribuut.',
    'Entiteit niet gevonden:',
    'Kaart kon niet laden:',
    'in de buurt',
    'Entiteit',
    'Titel (optioneel)',
    'Koptekst tonen',
    'Vluchtenlijst tonen',
    'Vluchtpaden tonen',
    'Middelpunt van het gebied tonen',
    'Kaart slepen en knijpzoomen toestaan',
    'Kaartstijl',
    'Zoom (optioneel, 1–19)',
    'Grootte vliegtuigicoon (optioneel, 12–64 px)',
    'Details sluiten',
    'Weergave herstellen',
    'Satelliet (Esri)',
    'Topografisch',
    'Afst',
    'Dichtstbij',
}

# Text that stays as it is, and why.
UNTRANSLATED_ON_PURPOSE = {
    'OpenStreetMap',    # proper name
    'Flightradar24',    # proper name
    'Auto',             # identical in Dutch
    'Min',              # upstream's abbreviation in the popup's cramped stats
                        # line; reads as "minimaal" in Dutch, and the full
                        # "Dichtstbij" does not fit there
    '28',               # numeric placeholder
    '→',                # symbol
}

APPROVED = TRANSLATED | UNTRANSLATED_ON_PURPOSE


def visible_strings() -> set[str]:
    """Return every user-visible literal the card renders."""
    source = CARD.read_text(encoding='utf-8')
    found: set[str] = set()
    for pattern in PATTERNS:
        for raw in pattern.findall(source):
            # Compare the literal text only: the interpolated expression is an
            # implementation detail that upstream renames freely.
            text = ' '.join(INTERPOLATION.sub('', raw).split())
            if text:
                found.add(text)
    return found


def test_every_visible_string_is_approved() -> None:
    unknown = visible_strings() - APPROVED
    assert not unknown, (
        'Untranslated or unknown card text: '
        + ', '.join(repr(text) for text in sorted(unknown))
        + '. Translate it into Dutch and add it to TRANSLATED in this file '
          '(or to UNTRANSLATED_ON_PURPOSE, with the reason).'
    )


def test_the_extractor_still_finds_text() -> None:
    """A regex that silently stops matching would make the guard useless."""
    found = visible_strings()
    assert len(found) >= len(APPROVED), (
        f'Only {len(found)} strings extracted, expected at least {len(APPROVED)}; '
        'the patterns no longer match how the card emits text.'
    )


def test_approved_list_has_no_leftovers() -> None:
    """Keep the list honest: an entry upstream dropped must not linger."""
    stale = APPROVED - visible_strings()
    assert not stale, (
        'Approved text no longer present in the card: '
        + ', '.join(repr(text) for text in sorted(stale))
        + '. Remove it from this file.'
    )
