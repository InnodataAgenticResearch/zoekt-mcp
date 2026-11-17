"""Console entry point for ``zoekt-mcp``.

Supports both running the MCP stdio server (default / ``serve``) and managing
Microsoft 365 Zoekt web gateway authentication (``login``, ``status``, ``logout``).
"""

from __future__ import annotations

import asyncio
import json
import sys
from collections.abc import Callable
from typing import Any

from .auth import (
    check_gateway_whoami,
    clear_stored_session,
    exchange_refresh_token_at_gateway,
    extract_foci_refresh_token,
    load_stored_session,
    resolve_auth_token,
    run_device_code_login,
    save_stored_session,
)
from .config import ZoektConfig, load_config
from .server import build_server


async def _run_login(
    config: ZoektConfig,
    *,
    sleep_fn: Callable[[float], Any] | None = None,
) -> int:
    refresh_tok = extract_foci_refresh_token(config.foci_cache)
    session = None
    if refresh_tok:
        try:
            session = await exchange_refresh_token_at_gateway(
                config.backend_url,
                refresh_tok,
                timeout=config.timeout,
            )
        except Exception:
            session = None

    if session is None:
        session = await run_device_code_login(
            config.backend_url,
            timeout=config.timeout,
            no_browser=config.no_browser,
            sleep_fn=sleep_fn,
        )

    saved_path = save_stored_session(session, config.auth_file)
    print(
        json.dumps(
            {
                "status": "authenticated",
                "backend_url": session.backend_url,
                "email": session.email,
                "name": session.name,
                "tid": session.tid,
                "expires_at": session.expires_at,
                "auth_file": str(saved_path),
            },
            indent=2,
        )
    )
    return 0


async def _run_status(config: ZoektConfig) -> int:
    stored = load_stored_session(config.auth_file)
    token = resolve_auth_token(explicit_token=config.auth_token, auth_file=config.auth_file)
    whoami = await check_gateway_whoami(
        config.backend_url,
        token,
        timeout=config.timeout,
    )
    authenticated = bool(whoami.get("authenticated"))
    print(
        json.dumps(
            {
                "backend_url": config.backend_url,
                "auth_file": str(config.auth_file),
                "has_local_session": stored is not None,
                "gateway": whoami,
            },
            indent=2,
        )
    )
    return 0 if authenticated else 1


def main(
    argv: list[str] | None = None,
    *,
    server_runner: Callable[[Any], None] | None = None,
    sleep_fn: Callable[[float], Any] | None = None,
) -> int:
    config = load_config(argv if argv is not None else sys.argv[1:])
    if config.subcommand == "logout":
        removed = clear_stored_session(config.auth_file)
        print(
            json.dumps(
                {
                    "status": "logged_out",
                    "removed": removed,
                    "auth_file": str(config.auth_file),
                }
            )
        )
        return 0
    if config.subcommand == "login":
        return asyncio.run(_run_login(config, sleep_fn=sleep_fn))
    if config.subcommand == "status":
        return asyncio.run(_run_status(config))

    server = build_server(config)
    if server_runner is not None:
        server_runner(server)
    else:  # pragma: no cover - blocking stdio loop
        server.run(transport="stdio")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI script entrypoint
    raise SystemExit(main())
