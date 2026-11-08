"""Command-line entry point: ``orion`` (stdio) or ``orion --transport http``."""

from __future__ import annotations

import argparse
import ipaddress
import logging
import sys

from orion import __version__
from orion.config import get_settings, setup_logging

logger = logging.getLogger(__name__)


def _is_loopback(host: str) -> bool:
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def main(argv: list[str] | None = None) -> None:
    """Run the Orion MCP server."""
    parser = argparse.ArgumentParser(
        prog="orion", description="Orion — per-project memory MCP server."
    )
    parser.add_argument("--transport", choices=["stdio", "http"], default="stdio")
    parser.add_argument("--host", default="127.0.0.1", help="HTTP host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=9099, help="HTTP port (default: 9099)")
    parser.add_argument("--version", action="version", version=f"orion {__version__}")
    args = parser.parse_args(argv)

    settings = get_settings()
    setup_logging(settings)

    from orion.app import mcp

    if args.transport == "stdio":
        mcp.run(show_banner=False)
        return

    if settings.token:
        from fastmcp.server.auth.providers.jwt import StaticTokenVerifier

        mcp.auth = StaticTokenVerifier(
            tokens={settings.token: {"client_id": "orion", "scopes": []}}
        )
    elif not _is_loopback(args.host):
        sys.exit(
            f"orion: refusing to listen on {args.host} without ORION_TOKEN "
            "(anyone on the network could read and delete the memory)."
        )
    logger.info("Serving Orion %s over HTTP on %s:%d", __version__, args.host, args.port)
    mcp.run(transport="http", host=args.host, port=args.port, show_banner=False)


if __name__ == "__main__":
    main()
