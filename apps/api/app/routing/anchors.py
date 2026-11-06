"""Fixed day-start anchors for Đà Nẵng (architecture §3.3, ADR-011).

Days start and end at one of these public points — never at traveler GPS — so the leg cache is
shared across travelers. Cache key: ``anchor:<code>``. Coordinates are public landmarks.
PROVISIONAL: the four codes and points await owner confirmation (reported with M3-B).
"""

from __future__ import annotations

from dataclasses import dataclass

from app.routing.provider import LatLng


@dataclass(frozen=True, slots=True)
class Anchor:
    code: str
    name_vi: str
    name_en: str
    location: LatLng

    @property
    def key(self) -> str:
        return f"anchor:{self.code}"


DA_NANG_ANCHORS: tuple[Anchor, ...] = (
    Anchor("dn-dragon-bridge", "Cầu Rồng", "Dragon Bridge", LatLng(16.0610, 108.2272)),
    Anchor("dn-my-khe", "Bãi biển Mỹ Khê", "My Khe Beach", LatLng(16.0602, 108.2468)),
    Anchor("dn-airport", "Sân bay Đà Nẵng", "Da Nang Airport", LatLng(16.0551, 108.2020)),
    Anchor("hoi-an-old-town", "Phố cổ Hội An", "Hoi An Ancient Town", LatLng(15.8771, 108.3260)),
)


def anchors_by_key() -> dict[str, Anchor]:
    return {anchor.key: anchor for anchor in DA_NANG_ANCHORS}
