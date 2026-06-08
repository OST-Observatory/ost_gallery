from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from gallery.errors import BuildLog


FIELD_PATTERN = re.compile(r"^([A-Za-z_]+)\s*=\s*(.*)$")


@dataclass
class ParsedObject:
    name: str
    description: str


@dataclass
class ParsedMetadata:
    fields: dict[str, str] = field(default_factory=dict)
    objects: list[ParsedObject] = field(default_factory=list)


def parse_objects_line(value: str, log: BuildLog, source: str) -> ParsedObject | None:
    """Parse OBJECT_INFO / OBJECTS value.

    Supported formats:
    - ``Name | description``
    - ``description`` (name omitted; shown as text-only entry)
    """
    value = value.strip()
    if not value:
        log.warning(source, "Empty OBJECT_INFO / OBJECTS line")
        return None

    if "|" in value:
        name, _, description = value.partition("|")
        name = name.strip()
        description = description.strip()
        if not name:
            log.warning(source, f"Invalid OBJECT_INFO line (empty name): {value!r}")
            return None
        if not description:
            log.warning(source, f"Invalid OBJECT_INFO line (empty description): {value!r}")
            return None
        return ParsedObject(name=name, description=description)

    return ParsedObject(name="", description=value)


def parse_txt_file(path: Path, log: BuildLog) -> ParsedMetadata | None:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        log.skip(str(path), f"Cannot read metadata file: {exc}")
        return None
    except UnicodeDecodeError as exc:
        log.skip(str(path), f"Metadata encoding error: {exc}")
        return None

    result = ParsedMetadata()
    for line_no, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        match = FIELD_PATTERN.match(line)
        if not match:
            log.warning(str(path), f"Line {line_no}: malformed field {raw_line!r}")
            continue

        key = match.group(1).upper()
        value = match.group(2).strip()

        if key in ("OBJECTS", "OBJECT_INFO"):
            obj = parse_objects_line(value, log, f"{path}:{line_no}")
            if obj:
                result.objects.append(obj)
        else:
            result.fields[key] = value

    return result


def parse_objects_md(path: Path, log: BuildLog) -> list[ParsedObject]:
    """Parse optional sidecar markdown: ## Name\\n description paragraphs."""
    if not path.is_file():
        return []

    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        log.warning(str(path), f"Cannot read objects sidecar: {exc}")
        return []

    objects: list[ParsedObject] = []
    current_name: str | None = None
    current_lines: list[str] = []

    def flush() -> None:
        nonlocal current_name, current_lines
        if current_name:
            objects.append(
                ParsedObject(name=current_name, description="\n".join(current_lines).strip())
            )
        current_name = None
        current_lines = []

    for line in text.splitlines():
        if line.startswith("## "):
            flush()
            current_name = line[3:].strip()
        elif current_name is not None:
            current_lines.append(line)

    flush()
    return objects
