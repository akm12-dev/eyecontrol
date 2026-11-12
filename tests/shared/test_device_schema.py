"""The shared device schema is the contract between server and all agents (Windows, Linux, Android, iOS)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker

PROTOCOL = Path(__file__).resolve().parents[2] / "shared" / "protocol"
SCHEMA = json.loads((PROTOCOL / "device.schema.json").read_text(encoding="utf-8"))
VALIDATOR = Draft202012Validator(SCHEMA, format_checker=FormatChecker())


def test_schema_itself_is_valid() -> None:
    Draft202012Validator.check_schema(SCHEMA)


@pytest.mark.parametrize("path", sorted((PROTOCOL / "examples").glob("*.json")), ids=lambda p: p.stem)
def test_examples_are_valid(path: Path) -> None:
    VALIDATOR.validate(json.loads(path.read_text(encoding="utf-8")))


@pytest.mark.parametrize("path", sorted((PROTOCOL / "invalid").glob("*.json")), ids=lambda p: p.stem)
def test_impossible_capabilities_are_rejected(path: Path) -> None:
    assert list(VALIDATOR.iter_errors(json.loads(path.read_text(encoding="utf-8"))))


def test_unknown_fields_are_rejected() -> None:
    doc = json.loads((PROTOCOL / "examples" / "windows-pc.json").read_text(encoding="utf-8"))
    doc["capabilities"]["hidden_capture"] = True
    assert list(VALIDATOR.iter_errors(doc))
