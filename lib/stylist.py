"""Bantagachi character system — Pokemon-style creature portraits.

Uses DiceBear's `bottts` style (robot monsters — Pokemon-adjacent creatures).
Every user gets a unique creature seeded by their email. Type selection changes
the base color palette (Fire / Water / Grass / Electric — RPG type mechanic).
"""
from __future__ import annotations
import json
from pathlib import Path
from urllib.parse import urlencode

PROFILES_PATH = "data/stylist_profiles.json"

# Bantagachi types — a Pokemon-style elemental type system that maps to primary color.
TYPES = {
    "Fire":     "F25022",
    "Water":    "0078D4",
    "Grass":    "D5E547",
    "Electric": "FFB900",
    "Psychic":  "B76E79",
    "Shadow":   "6B4530",
}

# Legacy aliases kept so Me tab imports don't break if anything still references them.
SKIN_TONES = TYPES
HAIR_STYLES = list(TYPES.keys())

DEFAULT_PROFILE = {
    "type":              "Grass",       # default matches Banter's lime accent
    "primary_color":     "D5E547",
    "secondary_color":   "0B0B0B",
    "eye_color":         "F5F3EE",
    "seed":              "banterone",
    "equipped_piercings": [],
    # legacy keys the customizer still reads — kept for backward compat.
    "skin_tone":         "Grass",
    "hair_color":        "#D5E547",
    "hair_style":        "Fire",
    "outfit_color":      "#0B0B0B",
}


# ── Profile persistence ──────────────────────────────────────────────────────
def _load_all() -> dict:
    p = Path(PROFILES_PATH)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except Exception:
        return {}


def _save_all(data: dict) -> None:
    Path(PROFILES_PATH).parent.mkdir(parents=True, exist_ok=True)
    Path(PROFILES_PATH).write_text(json.dumps(data, indent=2))


def load_profile(email: str) -> dict:
    all_profiles = _load_all()
    stored = all_profiles.get(email.lower(), {})
    merged = {**DEFAULT_PROFILE, **stored}
    # Auto-seed by email so each user has a unique creature by default
    if merged.get("seed") == "banterone":
        merged["seed"] = email.split("@")[0]
    return merged


def save_profile(email: str, updates: dict) -> None:
    all_profiles = _load_all()
    current = all_profiles.get(email.lower(), {})
    current.update(updates)
    all_profiles[email.lower()] = current
    _save_all(all_profiles)


# ── DiceBear bottts URL (Pokemon-style robot creatures) ──────────────────────
def dicebear_url(profile: dict, seed_key: str = "banterone") -> str:
    primary = profile.get("primary_color", "D5E547").lstrip("#")
    seed = seed_key or profile.get("seed") or "banterone"
    params = {
        "seed": seed,
        "backgroundColor": "0b0b0b",
        "primaryColor": primary,
        "primaryColorLevel": "600",
    }
    return f"https://api.dicebear.com/9.x/bottts/svg?{urlencode(params)}"


def _fetch_svg(url: str) -> str | None:
    import urllib.request
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "BanterONE/1.0"})
        with urllib.request.urlopen(req, timeout=6) as resp:
            body = resp.read().decode("utf-8", errors="ignore")
            if "<svg" in body:
                return body
    except Exception:
        return None
    return None


try:
    import streamlit as _st
    _fetch_svg = _st.cache_data(ttl=3600, show_spinner=False)(_fetch_svg)
except Exception:
    pass


def render_svg(profile: dict, gender: str = "male", size: int = 420,
               seed_key: str | None = None) -> str:
    """Return an inlined DiceBear bottts creature SVG."""
    seed = seed_key or profile.get("seed") or "banterone"
    url = dicebear_url(profile, seed_key=seed)
    svg = _fetch_svg(url)
    if svg:
        svg_parts = svg.split("<svg", 1)
        if len(svg_parts) == 2:
            svg = "<svg" + svg_parts[1]
        else:
            svg = svg_parts[0]
        return (
            '<div style="width:100%;height:100%;display:flex;align-items:center;'
            'justify-content:center;padding:24px;">'
            + svg +
            '</div>'
        )
    return _fallback_svg(profile)


def _fallback_svg(profile: dict) -> str:
    primary = "#" + profile.get("primary_color", "D5E547").lstrip("#")
    return (
        '<div style="width:100%;height:100%;display:flex;align-items:center;'
        'justify-content:center;flex-direction:column;color:var(--text-dim);'
        'font-family:\'DM Sans\',sans-serif;">'
        f'<svg viewBox="0 0 24 24" style="width:140px;height:140px;color:{primary};" '
        'fill="currentColor" xmlns="http://www.w3.org/2000/svg">'
        '<rect x="4" y="8" width="16" height="12" rx="4"/>'
        '<circle cx="9" cy="13" r="1.5" fill="#000"/>'
        '<circle cx="15" cy="13" r="1.5" fill="#000"/>'
        '<rect x="10" y="4" width="4" height="4"/>'
        '<circle cx="12" cy="3" r="1"/>'
        '</svg>'
        '<div style="margin-top:14px;font-size:11px;letter-spacing:0.22em;font-weight:700;">'
        'BANTAGACHI LOADING'
        '</div>'
        '</div>'
    )
