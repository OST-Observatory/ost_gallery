from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path


class Severity(str, Enum):
    WARNING = "WARNING"
    ERROR = "ERROR"
    FATAL = "FATAL"


@dataclass
class BuildLog:
    log_file: Path | None = None
    indexed: int = 0
    skipped: int = 0
    warnings: int = 0
    fatals: list[str] = field(default_factory=list)
    _messages: list[str] = field(default_factory=list)

    def _emit(self, severity: Severity, path: str, reason: str) -> None:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        line = f"{ts} [{severity.value}] {path}: {reason}"
        self._messages.append(line)
        print(line, file=sys.stderr)

        if self.log_file:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            with self.log_file.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")

        if severity == Severity.WARNING:
            self.warnings += 1
        elif severity == Severity.ERROR:
            self.skipped += 1

    def warning(self, path: str, reason: str) -> None:
        self._emit(Severity.WARNING, path, reason)

    def skip(self, path: str, reason: str) -> None:
        self._emit(Severity.ERROR, path, reason)

    def fatal(self, path: str, reason: str) -> None:
        self._emit(Severity.FATAL, path, reason)
        self.fatals.append(f"{path}: {reason}")

    def record_indexed(self) -> None:
        self.indexed += 1

    def print_summary(self) -> None:
        print(
            f"Indexed {self.indexed} images, skipped {self.skipped}, warnings {self.warnings}"
        )

    @property
    def has_fatal(self) -> bool:
        return bool(self.fatals)
