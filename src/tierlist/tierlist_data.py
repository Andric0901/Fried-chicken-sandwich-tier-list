"""Tier-list data and constants used by the image generator.

This module is intentionally lightweight: it does not import discord,
pymongo, dotenv, or any of the bot/GMaps stack, and it does not have
import-time side effects such as generating year-tag images.

Tierlist image generation should import from here rather than from
helper.py (which is coupled to the Discord bot).
"""

from pathlib import Path
import json

_HERE = Path(__file__).resolve().parent

TIER_DICT = json.loads((_HERE / "tier_dict.json").read_text(encoding="utf-8"))

TIERLIST_IMAGE_NAME = _HERE.parent / "tierlist_output" / "tierlist.png"
TIERLIST_IMAGE_NAME_WITH_YEAR_TAG = (
    _HERE.parent / "tierlist_output" / "tierlist_with_year_tag.png"
)
TIERLIST_IMAGE_NAME_WITH_YEAR_FIRST_VISITED_TAG = (
    _HERE.parent / "tierlist_output" / "tierlist_with_year_first_visited_tag.png"
)

TIER_COLOUR_HEX_DICT = {
    "S": "#ff7f7f",
    "A": "#ffbf7f",
    "B": "#ffff7f",
    "C": "#7fff7f",
    "D": "#7fbfff",
    "E": "#7f7fff",
    "F": "#ff7fff",
}
