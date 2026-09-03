"""synaptic_host/cause_line.py

One stderr line naming WHERE a Host failure happened, shared by every caller
that needs it.  Imports nothing from the engine and nothing from
`docker_training`.

Architecture sections 20.11 (the original ruling), 22.14 (#207) and 24.4.

This code used to live in `docker_training.py`, which imports the engine at
module scope.  B-15 is a failure of that very import, so `cli.py` could not
reuse the renderer from there -- least of all to report that importing it
failed.  Moving it here is the whole of the change; the rules it enforces are
unchanged from 20.11:

  * the exception's CLASS is named, its TEXT never is.  The text is not
    authored here: an `OSError` renders an absolute path and the platform's
    message, and several engine errors render a value they were checking, so a
    rule that filtered it would be a rule about strings nobody in this
    repository wrote.
  * a frame identity IS authored here and is stable, so it is rendered,
    relative to the package's parent, and no user directory can appear.
  * the line is length-bounded, and only stderr is written, so stdout stays
    byte-identical and the result JSON remains the last parseable line.

Section 24.4 adds exactly one thing: for a `ModuleNotFoundError` the missing
module name.  CPython produces it as a dotted identifier, never a path and
never operator text, so it passes the same test the class name passes, and it
is the field that distinguishes B-15's real cut (`tuner`) from the shallower
failure a bare import produces (`synaptic_tuner`).
"""

from __future__ import annotations

import sys
from pathlib import Path

_CAUSE_LINE_LIMIT = 400

# The package root is anchored on the PACKAGE, not on this module's own
# `__file__`.  Anchoring on the module would make the rendered frames depend
# on where this file happens to sit: moving it into a subpackage would put
# every real frame outside the anchor and silently degrade both call sites to
# "<unknown>" with nothing failing.  Deriving the top-level package name keeps
# the anchor correct wherever the module is moved to.
_ROOT_PACKAGE = (__package__ or "synaptic_host").split(".")[0]


def _package_root() -> Path:
    """The directory of the top-level `synaptic_host` package."""

    module = sys.modules.get(_ROOT_PACKAGE)
    filename = getattr(module, "__file__", None)
    if filename is None:
        raise RuntimeError
    return Path(filename).resolve().parent


def _innermost_package_frame(error: BaseException) -> str:
    """Render the deepest TWO traceback frames that lie inside this package.

    Section 22.14 (#207).  One frame is not enough because of an idiom this
    package uses in eight modules: a two-line `_fail`/`_platform_fail` helper
    whose whole body is a raise.  The deepest in-package frame for such a
    raise is the helper itself, which is the same frame for all 28 call sites
    behind `_platform_fail` and tells the reader nothing.  The frame that
    DECIDES the failure is the helper's caller, one step out.

    So the deepest two are kept and rendered

        <file>:<line> in <fn>, from <file>:<line> in <fn>

    with the deciding frame last, after the comma.  The `, from ...` clause is
    omitted when there is no second in-package frame, so this degrades to the
    20.11 line exactly where the 20.11 line is already right.  22.14 refused
    the two alternatives on purpose: introspecting a code object to decide
    what counts as a "helper" misfires the moment a helper gains a second
    line, and inlining the idiom at 34 sites deletes a package-wide pattern to
    improve a diagnostic.
    """

    package = _package_root()
    located: list[str] = []
    frames = getattr(error, "__traceback__", None)
    while frames is not None:
        code = frames.tb_frame.f_code
        try:
            filename = Path(code.co_filename).resolve()
            inside = filename.is_relative_to(package)
        except (OSError, ValueError):
            inside = False
        if inside:
            located.append("{}:{} in {}".format(
                filename.relative_to(package.parent).as_posix(),
                frames.tb_lineno, code.co_name,
            ))
        frames = frames.tb_next

    if not located:
        return "<unknown>"
    if len(located) == 1:
        return located[0]
    return "{}, from {}".format(located[-1], located[-2])


def _missing_module_clause(error: BaseException) -> str:
    """The missing module name, and only for a `ModuleNotFoundError`."""

    if not isinstance(error, ModuleNotFoundError):
        return ""
    name = getattr(error, "name", None)
    if type(name) is not str or not name:
        return ""
    return " '{}'".format(name)


def report_cause_line_v1(error: BaseException, code) -> None:
    """Write one line naming WHERE a failure happened, to stderr, and return.

    Never raises: a diagnostic that can fail the path it is diagnosing is
    worse than no diagnostic at all, so every part of the render is guarded
    and an unrenderable frame degrades to "<unknown>".
    """

    try:
        location = _innermost_package_frame(error)
    except BaseException:
        location = "<unknown>"
    try:
        missing = _missing_module_clause(error)
    except BaseException:
        missing = ""
    line = "synaptic-host: {} {}{} at {}".format(
        getattr(code, "value", code), type(error).__name__, missing, location,
    )
    print(line[:_CAUSE_LINE_LIMIT], file=sys.stderr)
