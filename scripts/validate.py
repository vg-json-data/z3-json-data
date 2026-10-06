#!/usr/bin/env python3
"""Validate project JSON schemas and references between definitions."""

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


def index_definition(index, key, value, path, document, location, errors):
    rendered_location = display_path(document, location)
    if key in index:
        previous_path, previous_location, _ = index[key]
        _record(
            errors, path, rendered_location,
            f"duplicates definition at {previous_path.relative_to(ROOT)}:{previous_location}",
        )
    else:
        index[key] = (path, rendered_location, value)


def validate_reference(path, document, location, value, definitions, kind, errors):
    if value not in definitions:
        _record(errors, path, display_path(document, location),
                f"unknown {kind} {json.dumps(value)}")


def walk_techs(techs, location):
    for i, tech in enumerate(techs):
        current = location + [i]
        yield tech, current
        yield from walk_techs(tech.get("extensionTechs", []), current + ["extensionTechs"])


def validate_node_world(path, document, location, node, world, errors):
    if node is not None and node[2].get("world") not in {world, "both"}:
        _record(errors, path, display_path(document, location),
                f"node {node[2]['id']} is not present in {world} world")


def collect_references(documents, errors):
    references = {name: {} for name in ["named", "items", "flags", "techs", "enemies", "attacks", "rooms"]}
    for path, document in documents.items():
        if path == ROOT / "items.json":
            for category, definitions in document.items():
                if category in {"$schema", "flags"}:
                    continue
                for i, item in enumerate(definitions):
                    location = [category, i, "name"]
                    index_definition(references["named"], item["name"], item, path, document, location, errors)
                    references["items"][item["name"]] = item
            for i, flag in enumerate(document["flags"]):
                index_definition(references["flags"], flag, flag, path, document, ["flags", i], errors)
        elif path == ROOT / "helpers.json":
            for i, helper in enumerate(document):
                index_definition(references["named"], helper["name"], helper, path, document, [i, "name"], errors)
        elif path == ROOT / "tech.json":
            for i, category in enumerate(document["techCategories"]):
                for tech, location in walk_techs(category["techs"], ["techCategories", i, "techs"]):
                    index_definition(references["named"], tech["name"], tech, path, document,
                                     location + ["name"], errors)
                    references["techs"][tech["name"]] = tech
        elif path.parent == ROOT / "enemies":
            namespace = "attacks" if path.name == "attacks.json" else "enemies"
            for i, enemy in enumerate(document["enemies"]):
                for j, name in enumerate(enemy["names"]):
                    index_definition(references[namespace], name, enemy, path, document,
                                     ["enemies", i, "names", j], errors)
        elif path.is_relative_to(ROOT / "rooms"):
            namespace = "Overworld" if document["roomType"] == "Overworld" else "Underworld"
            index_definition(references["rooms"], (namespace, document["id"]), document,
                             path, document, ["id"], errors)
    return references


def validate_requirements(path, document, requirements, location, references, errors, room=None):
    for i, requirement in enumerate(requirements):
        current = location + [i]
        if isinstance(requirement, str):
            if requirement not in {"free", "never"}:
                validate_reference(path, document, current, requirement, references["named"],
                                   "item, helper, or tech", errors)
            continue
        kind, value = next(iter(requirement.items()))
        current += [kind]
        if kind in {"and", "or"}:
            validate_requirements(path, document, value, current, references, errors, room)
        elif kind in {"flag", "notFlag"}:
            validate_reference(path, document, current, value, references["flags"], "flag", errors)
        elif kind == "damage":
            validate_reference(path, document, current + ["enemy"], value["enemy"],
                               references["enemies"], "enemy or hazard", errors)
            if "attack" in value:
                attack = value["attack"]
                validate_reference(path, document, current + ["attack"], attack,
                                   references["attacks"], "attack", errors)
                enemy = references["enemies"].get(value["enemy"])
                if (
                    enemy is not None
                    and attack in references["attacks"]
                    and attack not in enemy[2].get("attacks", [])
                ):
                    _record(errors, path, display_path(document, current + ["attack"]),
                            f"{json.dumps(value['enemy'])} does not list attack {json.dumps(attack)}")
        elif kind == "unlockDoor":
            validate_reference(path, document, current, value,
                               room["doors"] if room else {}, "room-local door", errors)
        elif kind in {"obstaclesCleared", "obstaclesNotCleared"}:
            for j, name in enumerate(value):
                validate_reference(path, document, current + [j], name,
                                   room["obstacles"] if room else {}, "room-local obstacle", errors)
        elif kind in {"combatProficiency", "bossProficiency", "darkProficiency"}:
            validate_reference(path, document, current, kind, references["techs"], "proficiency tech", errors)


def validate_room(path, document, references, errors):
    overworld = document["roomType"] == "Overworld"
    indices = {name: {} for name in [
        "nodes", "items", "doors", "obstacles", "entrances", "teleports", "whirlpools",
    ]}
    for field, namespace in [
        ("nodes", "nodes"), ("items", "items"),
        ("lockedDoors", "doors"), ("obstacles", "obstacles"),
    ]:
        for i, definition in enumerate(document.get(field, [])):
            index_definition(indices[namespace], definition["id"], definition,
                             path, document, [field, i, "id"], errors)
    for i, node in enumerate(document["nodes"]):
        if "killExitNode" in node:
            validate_reference(path, document, ["nodes", i, "killExitNode"],
                               node["killExitNode"], indices["nodes"], "node", errors)
        for field in ["entrances", "teleports", "whirlpools"]:
            for j, endpoint in enumerate(node.get(field, [])):
                index_definition(indices[field], endpoint["id"], endpoint, path, document,
                                 ["nodes", i, field, j, "id"], errors)
                if node.get("world") not in {"both", endpoint["world"]}:
                    _record(errors, path, display_path(document, ["nodes", i, field, j, "world"]),
                            "endpoint world is not present on its node")
    for i, item in enumerate(document.get("items", [])):
        location = display_path(document, ["items", i, "world"])
        if overworld and "world" not in item:
            _record(errors, path, location, "overworld items must specify a world")
        elif not overworld and "world" in item:
            _record(errors, path, location, "interior items must not specify a world")
        validate_reference(path, document, ["items", i, "itemLocation"],
                           item["itemLocation"], indices["nodes"], "node", errors)
        validate_reference(path, document, ["items", i, "item"], item["item"], references["items"], "item", errors)
        if overworld and "world" in item:
            validate_node_world(path, document, ["items", i, "world"],
                                indices["nodes"].get(item["itemLocation"]), item["world"], errors)
    for i, door in enumerate(document.get("lockedDoors", [])):
        validate_reference(path, document, ["lockedDoors", i, "doorLocation"],
                           door["doorLocation"], indices["nodes"], "node", errors)
        if overworld and "world" in door:
            validate_node_world(path, document, ["lockedDoors", i, "world"],
                                indices["nodes"].get(door["doorLocation"]), door["world"], errors)
    for i, strat in enumerate(document["strats"]):
        location = ["strats", i]
        for j, node_id in enumerate(strat["link"]):
            validate_reference(path, document, location + ["link", j], node_id, indices["nodes"], "node", errors)
            if overworld:
                world = strat.get("fromWorld" if j == 0 else "toWorld", strat.get("world"))
                if world in {"light", "dark"}:
                    validate_node_world(path, document, location + ["link", j],
                                        indices["nodes"].get(node_id), world, errors)
        for field, definitions, kind in [
            ("collectsItems", indices["items"], "room-local item"),
            ("setsFlags", references["flags"], "flag"),
            ("clearsObstacles", indices["obstacles"], "room-local obstacle"),
            ("resetsObstacles", indices["obstacles"], "room-local obstacle"),
            ("unlocksDoor", indices["doors"], "room-local door"),
        ]:
            for j, value in enumerate(strat.get(field, [])):
                validate_reference(path, document, location + [field, j], value, definitions, kind, errors)
        validate_requirements(path, document, strat["requires"],
                              location + ["requires"], references, errors, indices)
        for field, link_index in [("entranceState", 0), ("exitState", 1)]:
            event = strat.get(field)
            if event is None or "entranceID" not in event:
                continue
            validate_reference(path, document, location + [field, "entranceID"],
                               event["entranceID"], indices["entrances"], "room-local entrance", errors)
            node = indices["nodes"].get(strat["link"][link_index])
            if node is not None and event["entranceID"] in indices["entrances"]:
                if not any(entrance["id"] == event["entranceID"] for entrance in node[2].get("entrances", [])):
                    _record(errors, path, display_path(document, location + [field, "entranceID"]),
                            "event entrance does not belong to the strat endpoint node")
                world = strat.get("fromWorld" if link_index == 0 else "toWorld", strat.get("world"))
                if world in {"light", "dark"} and indices["entrances"][event["entranceID"]][2]["world"] != world:
                    _record(errors, path, display_path(document, location + [field, "entranceID"]),
                            f"event entrance is not in {world} world")


def validate_definitions(path, document, references, errors):
    if path == ROOT / "helpers.json":
        for i, helper in enumerate(document):
            validate_requirements(path, document, helper["requires"], [i, "requires"], references, errors)
    elif path == ROOT / "tech.json":
        for i, category in enumerate(document["techCategories"]):
            for tech, location in walk_techs(category["techs"], ["techCategories", i, "techs"]):
                for field in ["techRequires", "otherRequires"]:
                    validate_requirements(path, document, tech.get(field, []),
                                          location + [field], references, errors)
    elif path.parent == ROOT / "enemies":
        for i, enemy in enumerate(document["enemies"]):
            for j, attack in enumerate(enemy.get("attacks", [])):
                validate_reference(path, document, ["enemies", i, "attacks", j],
                                   attack, references["attacks"], "attack", errors)


def validate_connections(path, document, references, errors):
    for i, connection in enumerate(document["connections"]):
        for field in ["overworld", "overworld2", "underworld"]:
            if field not in connection:
                continue
            endpoint = connection[field]
            location = ["connections", i, field]
            namespace = "Underworld" if field == "underworld" else "Overworld"
            room_key = (namespace, endpoint["roomId"])
            if room_key not in references["rooms"]:
                _record(errors, path, display_path(document, location + ["roomId"]),
                        f"unknown {namespace.lower()} room {endpoint['roomId']}")
                continue
            room = references["rooms"][room_key][2]
            if namespace == "Underworld":
                nodes = {node["id"] for node in room["nodes"]}
                validate_reference(path, document, location + ["nodeId"],
                                   endpoint["nodeId"], nodes, "node", errors)
            else:
                for id_field, definitions in [
                    ("entranceId", "entrances"), ("teleportId", "teleports"),
                    ("whirlpoolId", "whirlpools"),
                ]:
                    if id_field not in endpoint:
                        continue
                    targets = {}
                    for node in room["nodes"]:
                        for target in node.get(definitions, []):
                            targets[target["id"]] = target
                    validate_reference(path, document, location + [id_field],
                                       endpoint[id_field], targets, definitions[:-1], errors)
                    target = targets.get(endpoint[id_field])
                    world = connection.get("toWorld", connection.get("world"))
                    if target is not None and target["world"] != world:
                        _record(errors, path, display_path(document, location + [id_field]),
                                f"endpoint is in {target['world']} world, connection uses {world}")


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
    reference_documents = {}

    for path, document in sorted(documents.items()):
        if path in schema_paths:
            continue
        declaration = document.get("$schema") if isinstance(document, dict) else None
        if declaration is None:
            skipped.append(path)
            if path == ROOT / "helpers.json":
                reference_documents[path] = document
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

        if not validation_errors and path not in errors:
            reference_documents[path] = document

    references = collect_references(reference_documents, errors)
    for path, document in reference_documents.items():
        if path.is_relative_to(ROOT / "rooms"):
            validate_room(path, document, references, errors)
        elif path.parent == ROOT / "connections":
            validate_connections(path, document, references, errors)
        else:
            validate_definitions(path, document, references, errors)

    for path in skipped:
        note = "no $schema; references checked" if path in reference_documents else "no $schema"
        print(f"🟡 {path.relative_to(ROOT)}: skipped schema validation ({note})\n")
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
