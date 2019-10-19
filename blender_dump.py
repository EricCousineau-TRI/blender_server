"""
Hacky way to dump information on Blender objects to then compare.

For example, download the Race Spaceship blend file, set up Blender, and
execute this script.
Example for Ubuntu Bionic can be seen in `setup_bionic.py`.
"""

import json

import numpy as np

# Blender.
import bpy
from mathutils import Color, Euler, Matrix, Quaternion, Vector


_PRIMITIVE_CLS_LIST = (bool, int, float, str, type(None))
_REPR_CLS_LIST = (Color, Euler, Matrix, Quaternion, Vector)
_SKIP_FIELDS = (
    "bl_rna", "rna_type", "node", "internal_links", "keying_sets_all")
_SKIP_FIELD_PREFIXES = ("_", "users_", "active_")


def _reorder(fields):
    # Tries to visit certain fields last (e.g. so "nodes" has the data
    # declared, and then "links" just has references).
    fields = list(fields)
    f = "links"
    if f in fields:
        fields.remove(f)
        fields.append(f)
    return fields


# Token to indicate value (and/or key) should be ignored / filtered out.
class _Ignore:
    @staticmethod
    def filter_values(values):
        for value in values:
            if value is not _Ignore:
                yield value

    @staticmethod
    def filter_items(items):
        for k, v in items:
            if k is not _Ignore and v is not _Ignore:
                yield (k, v)


def _id_bpy(o):
    # Some blender objects get new IDs, even if they may refer to the same
    # underlying data. Memoize using this pointer.
    if hasattr(o, "as_pointer"):
        return o.as_pointer()
    else:
        return id(o)


def _norm_str(s):
    # Ensure single quotes (easier for JSON / YAML formatting).
    if s is None:
        return None
    else:
        return s.replace('"', "'")


def dump(
        # For user.
        obj, max_len=500,
        # State.
        memo=None,
        # - For debugging.
        add_debug_info=True, depth=0, path=None, relpath=None,
        ):
    """Dumps a blender object to a dict to be formatted by JSON / YAML."""
    assert depth < 400  # Healthy constraint.
    if memo is None:
        memo = dict()
    if path is None:
        path = repr(obj)

    def recurse(x, relpath="?"):
        return dump(
            x, max_len=max_len,
            memo=memo,
            add_debug_info=add_debug_info,
            depth=depth+1, relpath=relpath, path=path + relpath)

    if isinstance(obj, _PRIMITIVE_CLS_LIST):
        return obj
    elif isinstance(obj, np.ndarray) and obj.dtype != np.object:
        if obj.size >= max_elem:
            return f"<len >= {max_len}>"
        return obj.tolist()
    elif isinstance(obj, Matrix):
        return np.array(obj).tolist()
    elif isinstance(obj, _REPR_CLS_LIST):
        return repr(obj)
    elif hasattr(obj, "__len__") and len(obj) > max_len:
        return f"<len = {len(obj)} >= {max_len}>"
    elif isinstance(obj, type) or hasattr(obj, "__call__"):
        # Do not print out types or functions.
        return _Ignore

    obj_id = _id_bpy(obj)
    if obj_id in memo:
        return f"<visited: {obj_id}>"
    # Record raw object (just in case it's ID may get reused otherwise).
    memo[obj_id] = obj
    if isinstance(obj, dict):
        items = obj.items()
        gen = ((recurse(k), recurse(v, _norm_str(f"[{repr(k)}]")))
               for k, v in items)
        gen = _Ignore.filter_items(gen)
        return dict(gen)
    elif hasattr(obj, "__iter__"):
        gen = (recurse(x, _norm_str(f"[{repr(i)}]"))
               for i, x in enumerate(obj))
        gen = _Ignore.filter_values(gen)
        return list(gen)
    else:
        # Iterate through attributes.
        d = dict()
        for k in _reorder(dir(obj)):
            if not hasattr(obj, k):
                continue
            if k.startswith(_SKIP_FIELD_PREFIXES) or k in _SKIP_FIELDS:
                continue
            v = recurse(getattr(obj, k), _norm_str(f".{k}"))
            if v is _Ignore:
                continue
            d[k] = v
        if add_debug_info:
            d["_type"] = repr(type(obj))
            d["_path"] = _norm_str(path)
            d["_relpath"] = _norm_str(relpath)
            d["_obj_id"] = obj_id
        return d
    assert False


def pretty(d):
    return json.dumps(d, sort_keys=True, indent=2)


# Example usage:
text = pretty(dump(bpy.data.scenes, path="scenes"))
with open("/tmp/output.txt", "w") as f:
   f.write(text + "\n")
print(text)
