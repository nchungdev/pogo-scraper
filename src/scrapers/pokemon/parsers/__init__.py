# AUTO-GENERATED — DO NOT EDIT

from .additional_parser import parse_additional
from .customes_parser import parse_costumes
from .evolution_parser import parse_evolution
from .header_parser import parse_forms, parse_types, parse_weather_boost, parse_availability_flags, parse_official_art
from .max_cp_chart_parser import parse_max_cp_chart
from .mega_boost import parse_mega_boost
from .meta_sections_parser import parse_meta_analysis, parse_faq
from .movesets_parser import parse_movesets
from .overview_parser import parse_overview_stats
from .pokedex_entries_parser import parse_pokedex_entries_table
from .section_extractor import extract_section_html
from .special_cp_parser import parse_special_cp
from .sprites_parser import parse_sprites
from .sprites_parser import parse_sprites

__all__ = [
    "parse_overview_stats",
    "parse_movesets",
    "parse_meta_analysis",
    "parse_faq",
    "parse_max_cp_chart",
    "parse_evolution",
    "parse_sprites",
    "parse_special_cp",
    "parse_forms",
    "parse_types",
    "parse_weather_boost",
    "parse_pokedex_entries_table",
    "parse_mega_boost",
    "parse_additional",
    "parse_costumes",
    "parse_official_art",
    "parse_availability_flags",
    "extract_section_html",
]
