"""Shared typography rules for editable poster and slide sources."""
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
TYPOGRAPHY = json.loads((ROOT/'design-system/typography.json').read_text(encoding='utf-8'))
PALETTE = json.loads((ROOT/'design-system/palette.json').read_text(encoding='utf-8'))
ICONS = json.loads((ROOT/'design-system/icons.json').read_text(encoding='utf-8'))
PATTERN = TYPOGRAPHY['cjk_pattern']
THEME = {'dk1':'ink','lt1':'white','dk2':'navy','lt2':'gray','accent1':'blue','accent2':'gold',
         'accent3':'teal','accent4':'blue','accent5':'navy','accent6':'muted','hlink':'blue','folHlink':'navy'}


def resolve_color(value):
    """Resolve previous authoring literals through the shared semantic palette."""
    role = PALETTE['legacy_roles'].get(value.lstrip('#').upper())
    result = PALETTE[role] if role else value
    return result if value.startswith('#') else result.lstrip('#')


def resolve_colors(svg):
    return re.sub(r'#[0-9a-fA-F]{6}\b', lambda match: resolve_color(match[0]), svg)


def font_runs(value):
    for token in re.split('('+PATTERN+'+)', str(value)):
        if token:
            yield token, TYPOGRAPHY['cjk'] if re.fullmatch(PATTERN+'+', token) else TYPOGRAPHY['latin']


def icon_fragment(name):
    return re.sub(r'\{\{(\w+)\}\}', lambda match: PALETTE[match[1]], ICONS[name])
