#!/usr/bin/env python3
"""Validate project JSON files against their declared local schemas."""

import json
from collections import defaultdict
from pathlib import Path
from urllib.parse import unquote, urlsplit

from jsonschema import exceptions, validators
from referencing import Registry, Resource
from referencing.exceptions import CannotDetermineSpecification, Unresolvable


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schema"
IGNORED_DIRS = {".git", ".venv", "venv", "__pycache__"}


def registry_for(schemas):
    """Build a local-only registry from schemas keyed by their basename $id."""
    return Registry().with_resources(
        (schema["$id"], Resource.from_contents(schema)) for schema in schemas
    ).crawl()


def _pointer_token(value):
    return str(value).replace("~", "~0").replace("/", "~1")


def _array_token(index, item):
    if not isinstance(item, dict):
        return str(index)

    item_id = item.get("id")
    name = item.get("name")
    has_id = isinstance(item_id, (int, float, str)) and not isinstance(item_id, bool)
    has_name = isinstance(name, str)
    token = f"#{json.dumps(item_id, ensure_ascii=False)}" if has_id else str(index)
    return f"{token}:{json.dumps(name, ensure_ascii=False)}" if has_name else token


def display_path(document, path):
    """Render a JSON path with id/name labels for array items where available."""
    current = document
    parts = []
    for segment in path:
        if isinstance(segment, int):
            item = current[segment] if isinstance(current, list) and segment < len(current) else None
            parts.append(_array_token(segment, item))
            current = item
        else:
            parts.append(_pointer_token(segment))
            current = current.get(segment) if isinstance(current, dict) else None
    return f"/{'/'.join(parts)}" if parts else "/"


def _one_line(message):
    return str(message).replace("\r", "\\r").replace("\n", "\\n")


def _record(errors, path, location, message):
    errors[path].append(f"{location}: {_one_line(message)}")


def _json_files():
    return sorted(
        path
        for path in ROOT.rglob("*.json")
        if not IGNORED_DIRS.intersection(path.relative_to(ROOT).parts)
    )


def _load_documents(paths, errors):
    documents = {}
    for path in paths:
        try:
            documents[path] = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            _record(
                errors,
                path,
                f"line {error.lineno}, column {error.colno}",
                f"invalid JSON: {error.msg}",
            )
        except OSError as error:
            _record(errors, path, "/", f"cannot read file: {error}")
    return documents


def _load_schemas(documents, errors):
    schemas = {}
    ids = {}
    for path in sorted(SCHEMA_DIR.glob("*.schema.json")):
        schema = documents.get(path)
        if schema is None:
            continue
        if not isinstance(schema, dict):
            _record(errors, path, "/", "schema must be an object")
            continue

        schema_id = schema.get("$id")
        if schema_id != path.name:
            _record(errors, path, "/$id", f"expected {json.dumps(path.name)}")
            continue
        if schema_id in ids:
            _record(errors, path, "/$id", f"duplicates {ids[schema_id].relative_to(ROOT)}")
            continue

        try:
            Resource.from_contents(schema)
            validators.validator_for(schema).check_schema(schema)
        except CannotDetermineSpecification:
            _record(errors, path, "/$schema", "missing or unsupported JSON Schema dialect")
            continue
        except exceptions.SchemaError as error:
            _record(errors, path, display_path(schema, error.absolute_path), error.message)
            continue

        ids[schema_id] = path
        schemas[path] = schema
    return schemas


def _declared_schema_path(path, declaration, errors):
    parsed = urlsplit(declaration)
    if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment:
        _record(errors, path, "/$schema", "expected a local schema path")
        return None

    declared_path = Path(unquote(parsed.path))
    if declared_path.is_absolute():
        _record(errors, path, "/$schema", "expected a relative schema path")
        return None

    schema_path = (path.parent / declared_path).resolve()
    if not schema_path.is_relative_to(ROOT):
        _record(errors, path, "/$schema", "schema path resolves outside the repository")
        return None
    if not schema_path.is_file():
        _record(errors, path, "/$schema", f"schema file not found: {declaration}")
        return None
    return schema_path


def _error_key(error):
    path = tuple(
        (0, segment) if isinstance(segment, int) else (1, str(segment))
        for segment in error.absolute_path
    )
    return path, tuple(str(segment) for segment in error.absolute_schema_path)


def main():
    errors = defaultdict(list)
    paths = _json_files()
    documents = _load_documents(paths, errors)
    schemas = _load_schemas(documents, errors)
    registry = registry_for(schemas.values())
    schema_paths = set(SCHEMA_DIR.glob("*.schema.json"))
    validators_by_path = {
        path: validators.validator_for(schema)(schema, registry=registry)
        for path, schema in schemas.items()
    }
    skipped = []

    for path, document in sorted(documents.items()):
        if path in schema_paths:
            continue
        declaration = document.get("$schema") if isinstance(document, dict) else None
        if declaration is None:
            skipped.append(path)
            continue
        if not isinstance(declaration, str):
            _record(errors, path, "/$schema", "must be a string")
            continue

        schema_path = _declared_schema_path(path, declaration, errors)
        if schema_path is None:
            continue
        validator = validators_by_path.get(schema_path)
        if validator is None:
            _record(errors, path, "/$schema", "referenced schema is invalid or unregistered")
            continue

        validation_errors = []
        try:
            validation_errors.extend(validator.iter_errors(document))
        except Unresolvable as error:
            _record(errors, path, "/", f"unresolvable schema reference: {error.ref}")
        for error in sorted(validation_errors, key=_error_key):
            _record(errors, path, display_path(document, error.absolute_path), error.message)

    for path in skipped:
        print(f"🟡 {path.relative_to(ROOT)}: skipped (no $schema)\n")
    for path in sorted(errors):
        print(path.relative_to(ROOT))
        for error in errors[path]:
            print(f"🔴 {error}")
        print()

    checked = len(paths) - len(skipped)
    error_count = sum(map(len, errors.values()))
    if error_count:
        print(
            f"🔴 FAILED: {error_count} error(s) in {len(errors)} file(s); "
            f"{checked} checked; {len(skipped)} skipped"
        )
        return 1
    print(f"🟢 PASS: {checked} file(s) checked; {len(skipped)} skipped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
