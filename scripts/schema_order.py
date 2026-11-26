"""Order object properties as their JSON schema lists them."""


def resolve_schema(schema, resolver):
    if "$ref" in schema:
        resolved = resolver.lookup(schema["$ref"])
        return {**resolved.contents, **schema}, resolved.resolver
    return schema, resolver


def order_by_schema(obj, schema, resolver):
    """Return `obj` with each object's properties in the order its schema's `properties` lists them.

    Properties the schema does not list are dropped, so callers can detect them by comparing the result with
    the input.
    """
    schema, resolver = resolve_schema(schema, resolver)
    if isinstance(obj, dict):
        ordered = {}
        for key, property_schema in schema.get("properties", {}).items():
            if key in obj:
                ordered[key] = order_by_schema(obj[key], property_schema, resolver)
        return ordered
    if isinstance(obj, list):
        return [order_by_schema(x, schema["items"], resolver) for x in obj]
    return obj
