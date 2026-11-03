from __future__ import annotations

from dataclasses import dataclass


@dataclass
class GroqProviderError(RuntimeError):
    status_code: int | None
    message: str
    retry_after_seconds: float | None = None

    def __post_init__(self) -> None:
        RuntimeError.__init__(self, self.message)

    @property
    def retryable(self) -> bool:
        return self.status_code in {408, 409, 425, 429} or self.status_code is not None and self.status_code >= 500
