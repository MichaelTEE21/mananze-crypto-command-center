"""Mananze OS platform identity contract."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PlatformIdentity:
    name: str
    short_name: str
    version: str
    tagline: str


PLATFORM_IDENTITY = PlatformIdentity(
    name="MANANZE OPERATING SYSTEM",
    short_name="MANANZE OS",
    version="0.1.0",
    tagline="YOUR PARTNER IN PROGRESS.",
)
