"""Format JSON in the project's standard style.

Objects and lists are expanded one item per line, except that short ones (up to `ONE_LINE_LIMIT` characters)
stay on one line when their contents are simple, with at most one level of nesting. Values of the keys in
`NON_ONE_LINE_KEYS` are always expanded.
"""

import json

# Keys whose values, and any object containing them, are always expanded to separate lines.
NON_ONE_LINE_KEYS = {
    "requires", "techRequires", "otherRequires", "and", "or",
    "nodes", "names", "name", "transitions", "attacks",
}

ONE_LINE_LIMIT = 80


def is_simple_value(x):
    if isinstance(x, (str, int, float, bool)) or x is None:
        return True
    return isinstance(x, list) and all(isinstance(y, (str, int, float, bool)) for y in x)


def is_one_liner_dict(obj, nesting_allowed):
    if len(json.dumps(obj)) > ONE_LINE_LIMIT:
        return False
    if any(key in NON_ONE_LINE_KEYS for key in obj):
        return False
    if all(is_simple_value(x) for x in obj.values()):
        return True
    if len(obj) == 1:
        return is_one_liner(next(iter(obj.values())), nesting_allowed)
    return False


def is_one_liner_list(obj, nesting_allowed):
    if len(json.dumps(obj)) > ONE_LINE_LIMIT:
        return False
    if len(obj) == 1:
        return is_one_liner(obj[0], nesting_allowed)
    return all(is_simple_value(x) for x in obj)


def is_one_liner(obj, nesting_allowed):
    # Only one level of nesting is allowed inside a one-line object or list.
    if isinstance(obj, dict):
        return nesting_allowed and is_one_liner_dict(obj, nesting_allowed=False)
    if isinstance(obj, list):
        return nesting_allowed and is_one_liner_list(obj, nesting_allowed=False)
    return True


def format_value(obj, indent, current_indent=0, one_liner_dict_allowed=True, one_liner_list_allowed=True):
    if not isinstance(obj, (dict, list)):
        return json.dumps(obj)
    next_indent = current_indent + indent
    if isinstance(obj, list):
        if len(obj) == 0 or (one_liner_list_allowed and is_one_liner_list(obj, nesting_allowed=True)):
            return json.dumps(obj)
        items = [next_indent * " " + format_value(value, indent, next_indent) for value in obj]
        return "[\n" + ",\n".join(items) + "\n" + current_indent * " " + "]"
    if len(obj) == 0 or (one_liner_dict_allowed and is_one_liner_dict(obj, nesting_allowed=True)):
        return json.dumps(obj)
    if one_liner_dict_allowed and len(obj) == 1:
        # A single-key object wraps its expanded value, e.g. {"or": [ ... ]}.
        key, value = next(iter(obj.items()))
        formatted_value = format_value(value, indent, current_indent, one_liner_dict_allowed=False,
                                       one_liner_list_allowed=key not in NON_ONE_LINE_KEYS)
        return "{" + json.dumps(key) + ": " + formatted_value + "}"
    items = []
    for key, value in obj.items():
        formatted_value = format_value(value, indent, next_indent, one_liner_dict_allowed=False,
                                       one_liner_list_allowed=key not in NON_ONE_LINE_KEYS)
        items.append(next_indent * " " + json.dumps(key) + ": " + formatted_value)
    return "{\n" + ",\n".join(items) + "\n" + current_indent * " " + "}"


def format_json(obj):
    """Return the formatted text of a JSON document, ending with a newline."""
    return format_value(obj, indent=2) + "\n"
