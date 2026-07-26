"""Orion — MCP server for developer context and memory."""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Orion")

# Tools are registered by importing them
from tools.memory import register_memory_tools

register_memory_tools(mcp)


def main():
    """Run Orion. Defaults to stdio; pass --transport http for HTTP mode."""
    import sys

    if "--transport" in sys.argv and "http" in sys.argv:
        port = 9099
        if "--port" in sys.argv:
            port_idx = sys.argv.index("--port")
            port = int(sys.argv[port_idx + 1])
        mcp.run(transport="http", port=port)
    else:
        mcp.run()


if __name__ == "__main__":
    main()
