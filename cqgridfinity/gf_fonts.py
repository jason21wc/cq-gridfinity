#! /usr/bin/env python3
#
# Copyright (C) 2026  Jason Collier
#
# Bundled font access.

"""Fonts shipped with the package, and a safe way to reach them.

**Why bundle at all.** Text cut into a printed part is geometry: the same
input must produce the same STEP on any machine. A system font lookup makes
the output depend on what happens to be installed, so every feature that
engraves text takes an explicit path and this module supplies it.

**Why `importlib.resources`.** `__file__` path arithmetic breaks when the
package is installed as a zip or frozen into a bundle. `files()` is the
supported way to reach package data, and `as_file()` materialises a real
filesystem path -- which is what CadQuery's `fontPath` needs.

**Why the existence check matters more than it looks.** CadQuery does NOT
fail on a bad `fontPath`; it silently falls back to a default font and
renders happily. So a font missing from the wheel would not raise, it would
quietly engrave the wrong typeface on every part. `font_path()` therefore
verifies the file is present and really is a font before handing it over.
"""

from contextlib import ExitStack
import atexit
import os

try:  # Python 3.9+
    from importlib.resources import files as _files, as_file as _as_file
except ImportError:  # pragma: no cover - Python 3.8 fallback
    from importlib_resources import files as _files, as_file as _as_file

__all__ = ["font_path", "DEFAULT_FONT", "BUNDLED_FONTS"]

# Open Sans is what Cullenect's own labels use, so tiles generated here match
# the ecosystem. SIL OFL 1.1 -- see cqgridfinity/fonts/OFL.txt, which the
# licence requires be distributed with the font.
DEFAULT_FONT = "OpenSans.ttf"
BUNDLED_FONTS = (DEFAULT_FONT,)

# TrueType/OpenType magic numbers.
_FONT_MAGIC = (b"\x00\x01\x00\x00", b"true", b"ttcf", b"OTTO")

_stack = ExitStack()
atexit.register(_stack.close)
_cache = {}


def font_path(name=DEFAULT_FONT):
    """Absolute path to a bundled font, guaranteed to exist and be a font.

    Raises rather than returning a path CadQuery would silently ignore.
    """
    if name in _cache:
        return _cache[name]
    resource = _files("cqgridfinity") / "fonts" / name
    try:
        path = str(_stack.enter_context(_as_file(resource)))
    except (FileNotFoundError, ModuleNotFoundError) as exc:
        raise FileNotFoundError(
            "bundled font %r is missing from the installed package. CadQuery "
            "would silently fall back to a system font and engrave the wrong "
            "typeface, so this is fatal rather than a warning. Check that "
            "package_data includes cqgridfinity/fonts/*." % name
        ) from exc
    if not os.path.isfile(path):
        raise FileNotFoundError(
            "bundled font %r resolved to %r, which is not a file" % (name, path)
        )
    with open(path, "rb") as fp:
        magic = fp.read(4)
    if magic not in _FONT_MAGIC:
        raise ValueError(
            "bundled font %r does not look like a TrueType/OpenType file "
            "(magic %r). A corrupt or text-encoded font still 'works' in "
            "CadQuery -- it just quietly uses a different typeface." % (name, magic)
        )
    _cache[name] = path
    return path
