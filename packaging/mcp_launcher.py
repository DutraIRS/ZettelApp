"""Entry script for the packaged MCP server (zettelapp-mcp.exe)."""

import sys

from zettelapp.mcp_main import main

if __name__ == "__main__":
    sys.exit(main())
