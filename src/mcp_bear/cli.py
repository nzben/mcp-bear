#  cli.py
#
#  Copyright (c) 2025 Junpei Kawamoto
#
#  This software is released under the MIT License.
#
#  http://opensource.org/licenses/mit-license.php
import logging
import socket
import sys

import rich_click as click

from mcp_bear import server


def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Check if a port is currently in use on the given host."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        return result == 0


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

    for port in range(callback_port, callback_port + 10):
        if is_port_in_use(port, callback_host):
            logger.info(f"Port {port} is already in use. Trying another port.")
        else:
            callback_port = port
            break
    else:
        logger.error("No available port found. Please try again.")
        sys.exit(1)

    mcp = server(token, callback_host, callback_port)

    logger.info("Starting MCP server (Press CTRL+D to quit)")
    mcp.run()
    logger.info("MCP server stopped")
