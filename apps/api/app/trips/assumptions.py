"""Plan assumptions: stored as stable keys in the snapshot, localized at response time.

A preview snapshot keeps only keys (``estimated_legs`` …) so the same revision reads correctly in
either launch locale; :func:`localize_assumptions` renders them for the caller's locale and
de-duplicates by key. Older snapshots stored already-localized text; any value that is not a known
key passes through unchanged.
"""

from collections.abc import Iterable
from typing import Final, Literal

AssumptionLocale = Literal["vi", "en"]

ESTIMATED_LEGS: Final = "estimated_legs"
NO_ROUTES: Final = "no_routes"
RESEARCH_SKIPPED: Final = "research_skipped"

ASSUMPTION_TEXT: Final[dict[str, dict[AssumptionLocale, str]]] = {
    ESTIMATED_LEGS: {
        "en": "Travel times and distances are estimates (demo mode), not measured routes.",
        "vi": "Thời gian và quãng đường di chuyển là ước tính (chế độ demo), chưa đo thực tế.",
    },
    NO_ROUTES: {
        "en": "Travel times are unavailable; the order assumes about 30 minutes between stops.",
        "vi": "Chưa có thời gian di chuyển; thứ tự giả định khoảng 30 phút giữa các điểm.",
    },
    RESEARCH_SKIPPED: {
        "en": "Web research did not finish in time; the plan uses Gonarra's catalog only.",
        "vi": "Tìm kiếm trên web chưa xong kịp; lịch trình chỉ dùng danh mục của Gonarra.",
    },
}


def unique_keys(keys: Iterable[str]) -> list[str]:
    """Order-preserving de-duplication by key."""
    return list(dict.fromkeys(keys))


def localize_assumptions(keys: Iterable[str], locale: AssumptionLocale) -> list[str]:
    """Render stored assumption keys in ``locale``; unknown (legacy text) values pass through."""
    rendered: list[str] = []
    for key in unique_keys(keys):
        text = ASSUMPTION_TEXT.get(key, {}).get(locale, key)
        if text not in rendered:
            rendered.append(text)
    return rendered
