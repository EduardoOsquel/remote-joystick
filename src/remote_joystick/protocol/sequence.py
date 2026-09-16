from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class SequenceTracker:
    last_sequence: int | None = None
    last_timestamp_ms: int | None = None

    def accept(self, sequence: int, timestamp_ms: int) -> bool:
        if self.last_sequence is None:
            self.last_sequence = sequence
            self.last_timestamp_ms = timestamp_ms
            return True
        if sequence == self.last_sequence:
            return False
        if sequence < self.last_sequence:
            return False
        if timestamp_ms < (self.last_timestamp_ms or 0):
            return False
        self.last_sequence = sequence
        self.last_timestamp_ms = timestamp_ms
        return True
