"""Encoding-safe output for management commands.

Several importers print a destination or business name straight from the
dataset. Most rows are ASCII, but the catalogue also holds Devanagari names,
and a stream whose encoding cannot represent them raises ``UnicodeEncodeError``
*in the middle of an import* -- aborting the command part-way and leaving the
table half-populated.

On a UTF-8 container this never happens, which is why it showed up only on a
Windows console (cp1252) and looked like a data problem rather than an output
problem. These helpers make progress output degrade to replacement characters
instead of killing the run, so an unprintable name can never cost you the
import.
"""
from __future__ import annotations

import sys


def _encodable(text: str, encoding: str | None) -> str:
    """Return ``text`` rendered in ``encoding``, replacing anything unencodable."""
    if not encoding:
        return text
    try:
        text.encode(encoding)
    except UnicodeEncodeError:
        return text.encode(encoding, "replace").decode(encoding, "replace")
    except (LookupError, TypeError):
        return text
    return text


def write(stream, text: str = "", style=None) -> None:
    """Write ``text`` to a management-command stream, never raising.

    ``stream`` may be any file-like object. The encoding is read from the
    stream's own ``encoding`` attribute when it has one, which is what makes
    this correct for a redirected stdout as well as a console.
    """
    if stream is None:
        return
    encoding = getattr(stream, "encoding", None) or getattr(
        getattr(stream, "buffer", None), "encoding", None
    )
    if style is not None:
        try:
            text = style(text)
        except Exception:  # noqa: BLE001 - styling must never break output
            pass
    try:
        stream.write(_encodable(str(text), encoding))
    except UnicodeEncodeError:
        # Last resort: the stream rejected our sanitised text too.
        try:
            stream.buffer.write(_encodable(str(text), "utf-8").encode("utf-8"))
        except Exception:  # noqa: BLE001
            pass
    except Exception:  # noqa: BLE001 - progress output is never load-bearing
        pass


def stdout(command, text: str = "", style=None) -> None:
    write(getattr(command, "stdout", None), text, style)


def stderr(command, text: str = "", style=None) -> None:
    write(getattr(command, "stderr", None), text, style)


def force_utf8_streams() -> None:
    """Best-effort switch of the interpreter's own streams to UTF-8.

    Call at the start of a command that may print dataset text. Does nothing
    when the stream cannot be reconfigured.
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            pass
