"""Mananze OS governed processing-mode decision contract."""

from dataclasses import dataclass
from typing import Literal

from mananze_os.task_scheduler import (
    ProcessingMode,
    is_request_blocking_mode,
)


DecisionReason = Literal[
    "explicit_request_mode",
]


@dataclass(frozen=True)
class ProcessingModeDecision:
    """Auditable decision selecting an existing scheduler processing mode."""

    processing_mode: ProcessingMode
    request_blocking: bool
    reason: DecisionReason = "explicit_request_mode"

    def __post_init__(self) -> None:
        if not self.processing_mode.strip():
            raise ValueError("processing_mode is required")

        if not is_request_blocking_mode(self.processing_mode):
            expected = False
        else:
            expected = True

        if self.request_blocking != expected:
            raise ValueError(
                "request_blocking does not match processing_mode"
            )


class ProcessingModeDecider:
    """Select an existing processing mode without executing or scheduling work."""

    def decide(
        self,
        processing_mode: ProcessingMode,
    ) -> ProcessingModeDecision:
        if not processing_mode.strip():
            raise ValueError("processing_mode is required")

        return ProcessingModeDecision(
            processing_mode=processing_mode,
            request_blocking=is_request_blocking_mode(processing_mode),
        )


__all__ = [
    "DecisionReason",
    "ProcessingModeDecision",
    "ProcessingModeDecider",
]
