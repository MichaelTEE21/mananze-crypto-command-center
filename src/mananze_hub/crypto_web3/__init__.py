"""Crypto & Web3 capability boundary.

Existing MCCC crypto functionality remains the implementation source during
the migration to Mananze Hub. Do not duplicate or reimplement those services
here until their contracts are explicitly migrated.
"""
from __future__ import annotations

CAPABILITY_ID = "mananze:crypto_web3"
CAPABILITY_NAME = "Crypto & Web3"

__all__ = ["CAPABILITY_ID", "CAPABILITY_NAME"]
