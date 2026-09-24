"""Provider health, usage, and cost accounting primitives.

This module observes provider execution. It does not grant authority,
change policy, authorize actions, or execute providers.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock
from typing import Any


@dataclass(frozen=True)
class ProviderHealthSnapshot:
    provider_id: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    consecutive_failures: int
    total_latency_ms: float
    last_latency_ms: float | None
    last_success_at: str | None
    last_failure_at: str | None

    @property
    def failure_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.failed_requests / self.total_requests

    @property
    def average_latency_ms(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.total_latency_ms / self.total_requests


@dataclass(frozen=True)
class ProviderUsageRecord:
    provider_id: str
    tool_id: str
    tenant_id: str
    execution_id: str
    success: bool
    latency_ms: float
    usage: dict[str, Any] | None
    cost: float
    cost_currency: str
    recorded_at: str


@dataclass
class _ProviderHealthState:
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    consecutive_failures: int = 0
    total_latency_ms: float = 0.0
    last_latency_ms: float | None = None
    last_success_at: str | None = None
    last_failure_at: str | None = None


class ProviderHealthRegistry:
    """Thread-safe in-memory provider health observation registry."""

    def __init__(self) -> None:
        self._states: dict[str, _ProviderHealthState] = {}
        self._lock = Lock()

    def record(
        self,
        *,
        provider_id: str,
        success: bool,
        latency_ms: float,
        recorded_at: str | None = None,
    ) -> None:
        if not isinstance(provider_id, str) or not provider_id.strip():
            raise ValueError("provider_id is required")

        if latency_ms < 0:
            raise ValueError("latency_ms cannot be negative")

        timestamp = recorded_at or datetime.now(timezone.utc).isoformat()

        with self._lock:
            state = self._states.setdefault(
                provider_id,
                _ProviderHealthState(),
            )

            state.total_requests += 1
            state.total_latency_ms += latency_ms
            state.last_latency_ms = latency_ms

            if success:
                state.successful_requests += 1
                state.consecutive_failures = 0
                state.last_success_at = timestamp
            else:
                state.failed_requests += 1
                state.consecutive_failures += 1
                state.last_failure_at = timestamp

    def get(self, provider_id: str) -> ProviderHealthSnapshot:
        if not isinstance(provider_id, str) or not provider_id.strip():
            raise ValueError("provider_id is required")

        with self._lock:
            state = self._states.get(provider_id)

            if state is None:
                return ProviderHealthSnapshot(
                    provider_id=provider_id,
                    total_requests=0,
                    successful_requests=0,
                    failed_requests=0,
                    consecutive_failures=0,
                    total_latency_ms=0.0,
                    last_latency_ms=None,
                    last_success_at=None,
                    last_failure_at=None,
                )

            return ProviderHealthSnapshot(
                provider_id=provider_id,
                total_requests=state.total_requests,
                successful_requests=state.successful_requests,
                failed_requests=state.failed_requests,
                consecutive_failures=state.consecutive_failures,
                total_latency_ms=state.total_latency_ms,
                last_latency_ms=state.last_latency_ms,
                last_success_at=state.last_success_at,
                last_failure_at=state.last_failure_at,
            )


class ProviderUsageLedger:
    """Records provider execution usage and actual reported costs."""

    def __init__(self) -> None:
        self._records: list[ProviderUsageRecord] = []
        self._lock = Lock()

    def record(
        self,
        *,
        provider_id: str,
        tool_id: str,
        tenant_id: str,
        execution_id: str,
        success: bool,
        latency_ms: float,
        usage: dict[str, Any] | None,
        cost: float,
        cost_currency: str,
        recorded_at: str | None = None,
    ) -> ProviderUsageRecord:
        if not isinstance(provider_id, str) or not provider_id.strip():
            raise ValueError("provider_id is required")
        if not isinstance(tool_id, str) or not tool_id.strip():
            raise ValueError("tool_id is required")
        if not isinstance(tenant_id, str) or not tenant_id.strip():
            raise ValueError("tenant_id is required")
        if not isinstance(execution_id, str) or not execution_id.strip():
            raise ValueError("execution_id is required")
        if latency_ms < 0:
            raise ValueError("latency_ms cannot be negative")
        if cost < 0:
            raise ValueError("cost cannot be negative")
        if not isinstance(cost_currency, str) or not cost_currency.strip():
            raise ValueError("cost_currency is required")

        record = ProviderUsageRecord(
            provider_id=provider_id,
            tool_id=tool_id,
            tenant_id=tenant_id,
            execution_id=execution_id,
            success=success,
            latency_ms=latency_ms,
            usage=usage,
            cost=cost,
            cost_currency=cost_currency,
            recorded_at=recorded_at or datetime.now(timezone.utc).isoformat(),
        )

        with self._lock:
            self._records.append(record)

        return record

    def list_all(self) -> tuple[ProviderUsageRecord, ...]:
        with self._lock:
            return tuple(self._records)

    def total_cost(
        self,
        *,
        provider_id: str | None = None,
        tenant_id: str | None = None,
        tool_id: str | None = None,
        cost_currency: str = "ZAR",
    ) -> float:
        if not isinstance(cost_currency, str) or not cost_currency.strip():
            raise ValueError("cost_currency is required")

        with self._lock:
            records = self._records[:]

        return sum(
            record.cost
            for record in records
            if record.cost_currency == cost_currency
            and (provider_id is None or record.provider_id == provider_id)
            and (tenant_id is None or record.tenant_id == tenant_id)
            and (tool_id is None or record.tool_id == tool_id)
        )


__all__ = [
    "ProviderHealthRegistry",
    "ProviderHealthSnapshot",
    "ProviderUsageLedger",
    "ProviderUsageRecord",
]
