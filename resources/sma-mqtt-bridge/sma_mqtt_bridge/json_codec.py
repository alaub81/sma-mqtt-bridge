"""JSON decoding without duplicate object keys or non-standard numeric constants."""

import json


def strict_json(text):
    """Decode data only; callers retain their own I/O and error boundaries."""

    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError
            result[key] = value
        return result

    def constant(_):
        raise ValueError

    return json.loads(text, object_pairs_hook=pairs, parse_constant=constant)
