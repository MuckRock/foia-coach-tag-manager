"""The FOIA Coach tag standard: valid `Type` values and how to reach them from old tags."""

import re
from dataclasses import dataclass, replace
from enum import StrEnum

TYPE_KEY = "Type"
# Older keys that sometimes hold the type when `Type` is missing.
HINT_KEYS = ("_tag", "Tags")


class DocType(StrEnum):
    """The standard `Type` values. Must match the enum in config.yaml."""

    SCHEDULE = "Retention Schedule"
    EMAIL_POLICY = "Email Retention Policy"
    GUIDE = "Guide"
    COURT_OPINION = "Court Opinion"
    ADMIN_OPINION = "Administrative Opinion"
    RECORDS_LOG = "Records Log"
    REQUEST = "Request"
    OTHER = "Other"


ALIASES = {
    "Retention Schedules": DocType.SCHEDULE,
    "Guides": DocType.GUIDE,
    "Court": DocType.COURT_OPINION,
    "Court Opinions": DocType.COURT_OPINION,
    "Court Cases": DocType.COURT_OPINION,
    "AG Opinion": DocType.ADMIN_OPINION,
    "Public Records Logs": DocType.RECORDS_LOG,
    "FOIA Logs": DocType.RECORDS_LOG,
    "Successful Request": DocType.REQUEST,
    "Agency Response": DocType.REQUEST,
}


class Status(StrEnum):
    OK = "ok"
    RENAME = "rename"
    FROM_HINT = "from hint"
    DEFAULTED = "defaulted"
    EMAIL = "email policy"
    UNRESOLVED = "unresolved"


# Must match `is_email_policy` in foia-coach-services, whose importers rely on the same split.
# Every Colorado schedule prints one of these in its opening; no email policy does.
SCHEDULE_HEADER = re.compile(
    r"RETENTION\s+SCHEDULE|RECORDS\s+MANAGEMENT\s+MANUAL", re.IGNORECASE
)
# Policies open with a cover letter or letterhead, so the mention can be well into the text.
EMAIL_MENTION = re.compile(
    r"\be-?\s?mails?\b|electronic\s+mail|24-72-204\.5|23-286", re.IGNORECASE
)


@dataclass
class Resolution:
    status: Status
    current: list[str]
    new: DocType | None = None
    reason: str = ""

    @property
    def changes(self):
        return self.new is not None and self.current != [self.new]


def standardize(value):
    """The standard `Type` for a tag value, or None if it has no known mapping."""
    value = value.strip()
    if value in DocType:
        return DocType(value)
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
    `Status.UNRESOLVED`. `default` is used only when there is no `Type` and no hint key.
    """
    data = data or {}
    current = list(data.get(TYPE_KEY) or [])

    if current:
        new = _single(current)
        if new is None:
            return Resolution(
                Status.UNRESOLVED, current, reason=f"Type values {current}"
            )
        status = Status.OK if current == [new] else Status.RENAME
        return Resolution(status, current, new)

    hints = [v for key in HINT_KEYS for v in data.get(key) or []]
    if hints:
        new = _single(hints)
        if new is None:
            return Resolution(
                Status.UNRESOLVED, current, reason=f"no Type; hints {hints}"
            )
        return Resolution(Status.FROM_HINT, current, new, reason=f"hints {hints}")

    if default:
        return Resolution(Status.DEFAULTED, current, default)
    return Resolution(Status.UNRESOLVED, current, reason="no Type")


def is_email_policy(text):
    """Does this text, all pages joined, read as an email retention policy rather than a schedule?"""
    return not SCHEDULE_HEADER.search(text[:400]) and bool(
        EMAIL_MENTION.search(text[:3000])
    )


def as_email_policy(result, text):
    """
    Retarget a schedule whose text reads as an email policy; anything else is returned as is.

    `text` of None means the document has no text yet, so the schedule comes back `Status.UNRESOLVED`.
    """
    if result.new != DocType.SCHEDULE:
        return result
    if text is None:
        return replace(
            result,
            status=Status.UNRESOLVED,
            new=None,
            reason="no text to check for email policy",
        )
    if not is_email_policy(text):
        return result
    return replace(
        result,
        status=Status.EMAIL,
        new=DocType.EMAIL_POLICY,
        reason="text reads as an email policy",
    )
