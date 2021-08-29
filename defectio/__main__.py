from __future__ import annotations

import os
import platform
import sys

from . import __version__


def main() -> None:
    """Print package info and exit."""
    path = os.path.abspath(os.path.dirname(__file__))
    version = __version__
    py_impl = platform.python_implementation()
    py_ver = platform.python_version()
    py_compiler = platform.python_compiler()

    sys.stderr.write(f"defectio {version}\n")
    sys.stderr.write(f"located at {path}\n")
    sys.stderr.write(f"{py_impl} {py_ver} {py_compiler}\n")
    sys.stderr.write(
        " ".join(frag.strip() for frag in platform.uname() if frag and frag.strip())
        + "\n"
    )


main()
