"""The FOIA Coach tag standard: valid `Type` values and how to reach them from old tags."""

from dataclasses import dataclass

TYPE_KEY = "Type"
# Older keys that sometimes hold the type when `Type` is missing.
HINT_KEYS = ("_tag", "Tags")

TYPES = (
    "Retention Schedule",
    "Guide",
    "Court Opinion",
    "Administrative Opinion",
    "Records Log",
    "Request",
    "Other",
)

ALIASES = {
    "Retention Schedules": "Retention Schedule",
    "Guides": "Guide",
    "Court": "Court Opinion",
    "Court Opinions": "Court Opinion",
    "Court Cases": "Court Opinion",
    "AG Opinion": "Administrative Opinion",
    "Public Records Logs": "Records Log",
    "FOIA Logs": "Records Log",
    "Successful Request": "Request",
    "Agency Response": "Request",
}

OK = "ok"
RENAME = "rename"
FROM_HINT = "from hint"
DEFAULTED = "defaulted"
UNRESOLVED = "unresolved"


@dataclass
class Resolution:
    status: str
    current: list[str]
    new: str | None = None
    reason: str = ""

    @property
    def changes(self):
        return self.new is not None and self.current != [self.new]


def standardize(value):
    """The standard `Type` for a tag value, or None if it has no known mapping."""
    value = value.strip()
    if value in TYPES:
        return value
    return ALIASES.get(value)


def _single(values):
    """The one standard type all values map to, or None if any is unknown or they disagree."""
    mapped = {standardize(v) for v in values}
    if len(mapped) == 1 and None not in mapped:
        return mapped.pop()
    return None


def resolve(data, default=None):
    """
    Work out the standard `Type` for a document's data.

    Never guesses: unknown values, or values that map to different types, come back
    UNRESOLVED. `default` is used only when there is no `Type` and no hint key.
    """
    data = data or {}
    current = list(data.get(TYPE_KEY) or [])

    if current:
        new = _single(current)
        if new is None:
            return Resolution(UNRESOLVED, current, reason=f"Type values {current}")
        status = OK if current == [new] else RENAME
        return Resolution(status, current, new)

    hints = [v for key in HINT_KEYS for v in data.get(key) or []]
    if hints:
        new = _single(hints)
        if new is None:
            return Resolution(UNRESOLVED, current, reason=f"no Type; hints {hints}")
        return Resolution(FROM_HINT, current, new, reason=f"hints {hints}")

    if default:
        return Resolution(DEFAULTED, current, default)
    return Resolution(UNRESOLVED, current, reason="no Type")
