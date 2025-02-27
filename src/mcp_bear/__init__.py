#  __init__.py
#
#  Copyright (c) 2025 Junpei Kawamoto
#
#  This software is released under the MIT License.
#
#  http://opensource.org/licenses/mit-license.php
import logging
import sys
from typing import Final

import click

from mcp_bear.server import create_server


@click.command()
@click.option("--token", envvar="BEAR_API_TOKEN", required=True, help="Bear API token")
@click.option(
    "--callback-host",
    default="127.0.0.1",
    help="hostname or IP address of the callback server",
    show_default=True,
)
@click.option(
    "--callback-port",
    default=11599,
    help="port number on which the callback server is listening",
    show_default=True,
)
@click.version_option()
def main(token: str, callback_host: str, callback_port: int) -> None:
    """A MCP server for interacting with Bear note-taking software."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stderr),
        ],
    )
    logger = logging.getLogger(__name__)

    mcp = create_server(token, callback_host, callback_port)

    logger.info("Starting MCP server (Press CTRL+D to quit)")
    mcp.run()
    logger.info("MCP server stopped")


__all__: Final = ["main"]
