"""Mananze Hub — internal business capability ecosystem.

The Hub contains the services and capabilities Mananze can deploy for tenants.
It is not a customer-facing destination and does not govern execution.
Mananze OS remains the authoritative governance and execution layer.
"""
from __future__ import annotations

HUB_NAME = "MANANZE HUB"
HUB_TAGLINE = "Business capabilities available to Mananze OS."

__all__ = ["HUB_NAME", "HUB_TAGLINE"]
