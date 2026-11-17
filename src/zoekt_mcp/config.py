"""Runtime configuration for the zoekt-mcp server.

Config comes from (in order of precedence):

1. Command-line flags (``--zoekt-url``, ``--timeout``, ``--token``, ``--auth-file``).
2. Environment variables (``ZOEKT_URL``, ``ZOEKT_TIMEOUT``, ``ZOEKT_AUTH_TOKEN``,
   ``ZOEKT_AUTH_FILE``).
3. Hard-coded defaults.
"""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path

from .auth import DEFAULT_AUTH_FILE
from .client import DEFAULT_BACKEND_URL, DEFAULT_TIMEOUT_SECONDS


@dataclass(frozen=True)
class ZoektConfig:
    backend_url: str
    timeout: float
    auth_token: str | None = None
    auth_file: Path = DEFAULT_AUTH_FILE
    subcommand: str = "serve"
    foci_cache: Path | None = None
    no_browser: bool = False


def load_config(argv: list[str] | None = None) -> ZoektConfig:
    """Parse CLI flags and environment variables into a :class:`ZoektConfig`."""
    raw_argv = list(argv) if argv is not None else []
    subcommand = "serve"
    if raw_argv and raw_argv[0] in ("serve", "login", "status", "logout"):
        subcommand = raw_argv[0]
        raw_argv = raw_argv[1:]

    parser = argparse.ArgumentParser(
        prog="zoekt-mcp",
        description=(
            "MCP server exposing Sourcegraph Zoekt code search "
            "(supports 'login', 'status', 'logout', or default stdio MCP server)."
        ),
    )
    parser.add_argument(
        "--zoekt-url",
        dest="zoekt_url",
        default=os.environ.get("ZOEKT_URL", DEFAULT_BACKEND_URL),
        help=(
            "Base URL of a running zoekt-webserver or M365 Zoekt Auth Gate. "
            "Defaults to $ZOEKT_URL or http://localhost:6070."
        ),
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=float(os.environ.get("ZOEKT_TIMEOUT", DEFAULT_TIMEOUT_SECONDS)),
        help="HTTP timeout in seconds for requests to zoekt-webserver.",
    )
    parser.add_argument(
        "--token",
        dest="auth_token",
        default=os.environ.get("ZOEKT_AUTH_TOKEN") or None,
        help="Optional session Bearer token for an authenticated Zoekt gateway.",
    )
    parser.add_argument(
        "--auth-file",
        dest="auth_file",
        default=os.environ.get("ZOEKT_AUTH_FILE", str(DEFAULT_AUTH_FILE)),
        help="Path to persisted Zoekt M365 session credentials JSON.",
    )
    parser.add_argument(
        "--foci-cache",
        dest="foci_cache",
        default=os.environ.get("ZOEKT_FOCI_CACHE") or None,
        help="Optional path to a Microsoft 365 FOCI token cache JSON for zero-prompt login.",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not attempt to open a browser automatically during 'zoekt-mcp login'.",
    )

    args = parser.parse_args(raw_argv)
    return ZoektConfig(
        backend_url=args.zoekt_url,
        timeout=args.timeout,
        auth_token=args.auth_token,
        auth_file=Path(args.auth_file),
        subcommand=subcommand,
        foci_cache=Path(args.foci_cache) if args.foci_cache else None,
        no_browser=bool(args.no_browser),
    )
