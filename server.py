"""Orion — CLI entrypoint. Run with stdio or HTTP transport."""

import argparse

from app import mcp


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Orion — MCP server for developer memory and context.",
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
        help="Transport protocol (default: stdio)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=9099,
        help="HTTP port (default: 9099)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="HTTP host (default: 127.0.0.1)",
    )
    args = parser.parse_args()

    if args.transport == "http":
        mcp.run(transport="http", host=args.host, port=args.port)
    else:
        mcp.run()


if __name__ == "__main__":
    main()