"""Wikidata ``P31`` (instance of) → Gonarra category code (DEC-022). Deterministic table.

Matching uses the English label of the class (lower case, exact match) so that the table stays
readable and auditable; an item whose classes map to nothing is skipped (not imported). When an
item has several mapped classes, the most specific category wins (``CATEGORY_PRIORITY``).
"""

from __future__ import annotations

from collections.abc import Iterable

CLASS_LABEL_CATEGORY: dict[str, str] = {
    # Museums
    "museum": "MUSEUM",
    "art museum": "MUSEUM",
    "history museum": "MUSEUM",
    "historic house museum": "MUSEUM",
    "military museum": "MUSEUM",
    "ethnographic museum": "MUSEUM",
    "archaeological museum": "MUSEUM",
    "science museum": "MUSEUM",
    "national museum": "MUSEUM",
    "art gallery": "MUSEUM",
    # Religious sites
    "pagoda": "RELIGIOUS_SITE",
    "buddhist temple": "RELIGIOUS_SITE",
    "buddhist temple in vietnam": "RELIGIOUS_SITE",
    "hindu temple": "RELIGIOUS_SITE",
    "temple": "RELIGIOUS_SITE",
    "church building": "RELIGIOUS_SITE",
    "church": "RELIGIOUS_SITE",
    "catholic church building": "RELIGIOUS_SITE",
    "cathedral": "RELIGIOUS_SITE",
    "mosque": "RELIGIOUS_SITE",
    "shrine": "RELIGIOUS_SITE",
    "chinese temple": "RELIGIOUS_SITE",
    "caodaist temple": "RELIGIOUS_SITE",
    "buddhist monastery": "RELIGIOUS_SITE",
    "monastery": "RELIGIOUS_SITE",
    # Theme parks and attractions
    "amusement park": "THEME_PARK",
    "theme park": "THEME_PARK",
    "water park": "THEME_PARK",
    "aerial lift": "THEME_PARK",
    "aerial tramway": "THEME_PARK",
    "zoo": "THEME_PARK",
    "aquarium": "THEME_PARK",
    "public aquarium": "THEME_PARK",
    # Markets, food, cafés, nightlife
    "market": "MARKET",
    "marketplace": "MARKET",
    "night market": "MARKET",
    "wet market": "MARKET",
    "restaurant": "FOOD",
    "food court": "FOOD",
    "café": "CAFE",
    "cafe": "CAFE",
    "coffeehouse": "CAFE",
    "bar": "NIGHTLIFE",
    "pub": "NIGHTLIFE",
    "nightclub": "NIGHTLIFE",
    "beer garden": "NIGHTLIFE",
    # Craft villages
    "craft village": "CRAFT_VILLAGE",
    "traditional craft village": "CRAFT_VILLAGE",
    "pottery village": "CRAFT_VILLAGE",
    # Beaches
    "beach": "BEACH",
    # Heritage
    "ruins": "HERITAGE",
    "archaeological site": "HERITAGE",
    "monument": "HERITAGE",
    "memorial": "HERITAGE",
    "fort": "HERITAGE",
    "citadel": "HERITAGE",
    "old town": "HERITAGE",
    "historic district": "HERITAGE",
    "assembly hall": "HERITAGE",
    "covered bridge": "HERITAGE",
    "champa tower": "HERITAGE",
    "cham tower": "HERITAGE",
    "gopuram": "HERITAGE",
    "mandapa": "HERITAGE",
    "colossal statue": "HERITAGE",
    "statue": "HERITAGE",
    "communal house": "HERITAGE",
    "đình": "HERITAGE",
    "world heritage site": "HERITAGE",
    "cultural heritage": "HERITAGE",
    "historic site": "HERITAGE",
    "national monument": "HERITAGE",
    "tomb": "HERITAGE",
    "mausoleum": "HERITAGE",
    "lighthouse": "HERITAGE",
    # Viewpoints and landmarks
    "mountain pass": "VIEWPOINT",
    "viewpoint": "VIEWPOINT",
    "scenic viewpoint": "VIEWPOINT",
    "observation tower": "VIEWPOINT",
    "bridge": "VIEWPOINT",
    "road bridge": "VIEWPOINT",
    "suspension bridge": "VIEWPOINT",
    "footbridge": "VIEWPOINT",
    "cable-stayed bridge": "VIEWPOINT",
    "swing bridge": "VIEWPOINT",
    "arch bridge": "VIEWPOINT",
    "pedestrian bridge": "VIEWPOINT",
    # Nature
    "mountain": "NATURE",
    "hill": "NATURE",
    "summit": "NATURE",
    "island": "NATURE",
    "archipelago": "NATURE",
    "peninsula": "NATURE",
    "nature reserve": "NATURE",
    "national park": "NATURE",
    "national park of vietnam": "NATURE",
    "protected area": "NATURE",
    "forest": "NATURE",
    "lake": "NATURE",
    "lagoon": "NATURE",
    "bay": "NATURE",
    "waterfall": "NATURE",
    "cave": "NATURE",
    "hill station": "NATURE",
    "urban park": "NATURE",
    "park": "NATURE",
    "botanical garden": "NATURE",
    "marble mountains": "NATURE",
}

# Most specific first: a pagoda that is also on a mountain is a RELIGIOUS_SITE.
CATEGORY_PRIORITY: tuple[str, ...] = (
    "MUSEUM",
    "RELIGIOUS_SITE",
    "THEME_PARK",
    "MARKET",
    "CAFE",
    "FOOD",
    "NIGHTLIFE",
    "CRAFT_VILLAGE",
    "BEACH",
    "HERITAGE",
    "VIEWPOINT",
    "NATURE",
)


def map_category(class_labels: Iterable[str]) -> str | None:
    found = {
        CLASS_LABEL_CATEGORY[label.strip().lower()]
        for label in class_labels
        if label.strip().lower() in CLASS_LABEL_CATEGORY
    }
    for category in CATEGORY_PRIORITY:
        if category in found:
            return category
    return None


# Deterministic visit-length defaults (minutes) by category: planner parameters, not displayed
# facts. The sheet may override them per place (visit_minutes_min/suggested/max).
VISIT_MINUTES: dict[str, tuple[int, int, int]] = {
    "HERITAGE": (30, 60, 120),
    "MUSEUM": (45, 75, 150),
    "RELIGIOUS_SITE": (20, 40, 90),
    "BEACH": (60, 120, 240),
    "NATURE": (60, 120, 240),
    "VIEWPOINT": (15, 30, 60),
    "MARKET": (30, 60, 120),
    "FOOD": (45, 60, 90),
    "CAFE": (30, 45, 90),
    "NIGHTLIFE": (60, 90, 180),
    "THEME_PARK": (180, 300, 480),
    "CRAFT_VILLAGE": (45, 90, 180),
}


# ---- OpenStreetMap tags (osm.py) ----------------------------------------------------------
# (key, value) -> category; value "*" matches any value of that key. Deterministic, auditable.
OSM_PRIMARY_TAGS: dict[tuple[str, str], str] = {
    ("tourism", "museum"): "MUSEUM",
    ("tourism", "gallery"): "MUSEUM",
    ("tourism", "viewpoint"): "VIEWPOINT",
    ("tourism", "theme_park"): "THEME_PARK",
    ("tourism", "zoo"): "THEME_PARK",
    ("tourism", "aquarium"): "THEME_PARK",
    ("leisure", "water_park"): "THEME_PARK",
    ("amenity", "place_of_worship"): "RELIGIOUS_SITE",
    ("amenity", "restaurant"): "FOOD",
    ("amenity", "cafe"): "CAFE",
    ("amenity", "marketplace"): "MARKET",
    ("shop", "marketplace"): "MARKET",
    ("shop", "mall"): "MARKET",
    ("leisure", "park"): "NATURE",
    ("leisure", "beach_resort"): "BEACH",
    ("natural", "beach"): "BEACH",
    ("natural", "peak"): "NATURE",
    ("natural", "cave_entrance"): "NATURE",
    ("historic", "*"): "HERITAGE",
}

# ``tourism=attraction`` alone says nothing about the kind of place: it maps only through one of
# these companion tags, otherwise the element is skipped (unmapped). Companion tags never qualify
# an element that already has a primary tag (a vegetarian restaurant with ``religion=buddhist``
# stays FOOD).
OSM_ATTRACTION_QUALIFIERS: dict[tuple[str, str], str] = {
    ("man_made", "bridge"): "VIEWPOINT",
    ("bridge", "*"): "VIEWPOINT",
    ("man_made", "tower"): "VIEWPOINT",
    ("building", "temple"): "RELIGIOUS_SITE",
    ("building", "pagoda"): "RELIGIOUS_SITE",
    ("building", "church"): "RELIGIOUS_SITE",
    ("building", "cathedral"): "RELIGIOUS_SITE",
    ("building", "shrine"): "RELIGIOUS_SITE",
    ("religion", "*"): "RELIGIOUS_SITE",
    ("natural", "*"): "NATURE",
    ("craft", "*"): "CRAFT_VILLAGE",
}

# Values of a "*" key that do not describe a visitable place.
_OSM_IGNORED_VALUES = frozenset({"no", "boundary_stone", "milestone"})


def _osm_categories(tags: dict[str, str], table: dict[tuple[str, str], str]) -> set[str]:
    found: set[str] = set()
    for key, raw in tags.items():
        value = raw.strip().lower()
        category = table.get((key, value))
        if category is None and value not in _OSM_IGNORED_VALUES:
            category = table.get((key, "*"))
        if category is not None:
            found.add(category)
    return found


def map_osm_tags(tags: dict[str, str]) -> str | None:
    """OSM tags → Gonarra category (most specific wins, ``CATEGORY_PRIORITY``), else None."""
    found = _osm_categories(tags, OSM_PRIMARY_TAGS)
    if not found and tags.get("tourism", "").strip().lower() == "attraction":
        found = _osm_categories(tags, OSM_ATTRACTION_QUALIFIERS)
    for category in CATEGORY_PRIORITY:
        if category in found:
            return category
    return None
