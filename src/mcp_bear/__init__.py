#  __init__.py
#
#  Copyright (c) 2025 Junpei Kawamoto
#
#  This software is released under the MIT License.
#
#  http://opensource.org/licenses/mit-license.php

import asyncio
import json
import logging
import signal
import sys
import webbrowser
from asyncio import Queue, Future, QueueEmpty
from copy import deepcopy
from dataclasses import dataclass
from http import HTTPStatus
from typing import cast, Final
from urllib.parse import urlencode, quote, unquote_plus

import click
from fastapi import FastAPI, Request
from mcp.server import FastMCP
from pydantic import Field
from starlette.datastructures import QueryParams
from uvicorn import Config, Server
from uvicorn.config import LOGGING_CONFIG

BASE_URL = "bear://x-callback-url"


@dataclass
class ErrorResponse(Exception):
    errorCode: int
    errorMessage: str

    def __str__(self) -> str:
        return self.errorMessage


def register_callback(api: FastAPI, path: str) -> Queue[Future[QueryParams]]:
    queue = Queue[Future[QueryParams]]()

    @api.get(
        f"/{path}/success", status_code=HTTPStatus.NO_CONTENT, include_in_schema=False
    )
    async def success(request: Request) -> None:
        try:
            future = queue.get_nowait()
            future.set_result(request.query_params)
        except QueueEmpty:
            pass

    @api.get(
        f"/{path}/error", status_code=HTTPStatus.NO_CONTENT, include_in_schema=False
    )
    async def error(request: Request) -> None:
        try:
            future = queue.get_nowait()

            q = request.query_params
            future.set_exception(
                ErrorResponse(
                    errorCode=int(q.get("error-Code") or "0"),
                    errorMessage=q.get("errorMessage") or "",
                )
            )
        except QueueEmpty:
            pass

    return queue


async def run_servers(token: str, callback_host: str, callback_port: int) -> None:
    mcp = FastMCP("Bear")
    callback = FastAPI()

    #
    # /open-note API
    #
    open_note_results = register_callback(callback, "open-note")

    @mcp.tool()
    async def open_note(
        id: str | None = Field(description="note unique identifier", default=None),
        title: str | None = Field(description="note title", default=None),
    ) -> str:
        """Open a note identified by its title or id and return its content."""
        nonlocal open_note_results

        params = {
            "new_window": "no",
            "float": "no",
            "show_window": "no",
            "open_note": "no",
            "selected": "no",
            "pin": "no",
            "edit": "no",
            "x-success": f"http://{callback_host}:{callback_port}/open-note/success",
            "x-error": f"http://{callback_host}:{callback_port}/open-note/error",
        }
        if id is not None:
            params["id"] = id
        if title is not None:
            params["title"] = title

        future = Future[QueryParams]()
        await open_note_results.put(future)

        webbrowser.open(f"{BASE_URL}/open-note?{urlencode(params, quote_via=quote)}")
        res = await future

        return unquote_plus(res.get("note") or "")

    #
    # /create API
    #
    create_results = register_callback(callback, "create")

    @mcp.tool()
    async def create(
        title: str | None = Field(description="note title", default=None),
        text: str | None = Field(description="note body", default=None),
        tags: list[str] | None = Field(description="list of tags", default=None),
        timestamp: bool = Field(
            description="prepend the current date and time to the text", default=False
        ),
    ) -> str:
        """Create a new note and return its unique identifier. Empty notes are not allowed."""
        nonlocal create_results

        params = {
            "open_note": "no",
            "new_window": "no",
            "float": "no",
            "show_window": "no",
            "x-success": f"http://{callback_host}:{callback_port}/create/success",
            "x-error": f"http://{callback_host}:{callback_port}/create/error",
        }
        if title is not None:
            params["title"] = title
        if text is not None:
            params["text"] = text
        if tags is not None:
            params["tags"] = ",".join(tags)
        if timestamp:
            params["timestamp"] = "yes"

        future = Future[QueryParams]()
        await create_results.put(future)

        webbrowser.open(f"{BASE_URL}/create?{urlencode(params, quote_via=quote)}")
        res = await future

        return res.get("identifier") or ""

    #
    # /tags API
    #
    tags_results = register_callback(callback, "tags")

    @mcp.resource("bear://tags")
    async def tags() -> list[str]:
        """Return all the tags currently displayed in Bear’s sidebar."""
        nonlocal tags_results

        params = {
            "token": token,
            "x-success": f"http://{callback_host}:{callback_port}/tags/success",
            "x-error": f"http://{callback_host}:{callback_port}/tags/error",
        }

        future = Future[QueryParams]()
        await tags_results.put(future)

        webbrowser.open(f"{BASE_URL}/tags?{urlencode(params, quote_via=quote)}")
        res = await future

        notes = cast(list[dict], json.loads(res.get("tags") or "[]"))
        return [note["name"] for note in notes if "name" in note]

    #
    # /open-tag API
    #
    open_tag_results = register_callback(callback, "open-tag")

    @mcp.tool()
    async def open_tag(
        name: str = Field(description="tag name or a list of tags divided by comma"),
    ) -> list[str]:
        """Show all the notes which have a selected tag in bear."""
        nonlocal open_tag_results

        params = {
            "name": name,
            "token": token,
            "x-success": f"http://{callback_host}:{callback_port}/open-tag/success",
            "x-error": f"http://{callback_host}:{callback_port}/open-tag/error",
        }

        future = Future[QueryParams]()
        await open_tag_results.put(future)

        webbrowser.open(f"{BASE_URL}/open-tag?{urlencode(params, quote_via=quote)}")
        res = await future

        notes = cast(list[dict], json.loads(res.get("notes") or "[]"))
        return [f"{note.get('title')} (ID: {note.get('identifier')})" for note in notes]

    #
    # /todo API
    #
    todo_results = register_callback(callback, "todo")

    @mcp.tool()
    async def todo(
        search: str | None = Field(description="string to search", default=None),
    ) -> list[str]:
        """Select the Todo sidebar item."""
        nonlocal todo_results

        params = {
            "show_window": "no",
            "token": token,
            "x-success": f"http://{callback_host}:{callback_port}/todo/success",
            "x-error": f"http://{callback_host}:{callback_port}/todo/error",
        }
        if search is not None:
            params["search"] = search

        future = Future[QueryParams]()
        await todo_results.put(future)

        webbrowser.open(f"{BASE_URL}/todo?{urlencode(params, quote_via=quote)}")
        res = await future

        notes = cast(list[dict], json.loads(res.get("notes") or "[]"))
        return [f"{note.get('title')} (ID: {note.get('identifier')})" for note in notes]

    #
    # /today API
    #
    today_results = register_callback(callback, "today")

    @mcp.tool()
    async def today(
        search: str | None = Field(description="string to search", default=None),
    ) -> list[str]:
        """Select the Today sidebar item."""
        nonlocal today_results

        params = {
            "show_window": "no",
            "token": token,
            "x-success": f"http://{callback_host}:{callback_port}/today/success",
            "x-error": f"http://{callback_host}:{callback_port}/today/error",
        }
        if search is not None:
            params["search"] = search

        future = Future[QueryParams]()
        await today_results.put(future)

        webbrowser.open(f"{BASE_URL}/today?{urlencode(params, quote_via=quote)}")
        res = await future

        notes = cast(list[dict], json.loads(res.get("notes") or "[]"))
        return [f"{note.get('title')} (ID: {note.get('identifier')})" for note in notes]

    #
    # /search API
    #
    search_results = register_callback(callback, "search")

    @mcp.tool()
    async def search(
        term: str | None = Field(description="string to search", default=None),
        tag: str | None = Field(description="tag to search into", default=None),
    ) -> list[str]:
        """Show search results in Bear for all notes or for a specific tag."""
        nonlocal search_results

        params = {
            "show_window": "no",
            "token": token,
            "x-success": f"http://{callback_host}:{callback_port}/search/success",
            "x-error": f"http://{callback_host}:{callback_port}/search/error",
        }
        if term is not None:
            params["term"] = term
        if tag is not None:
            params["tag"] = tag

        future = Future[QueryParams]()
        await search_results.put(future)

        webbrowser.open(f"{BASE_URL}/search?{urlencode(params, quote_via=quote)}")
        res = await future

        notes = cast(list[dict], json.loads(res.get("notes") or "[]"))
        return [f"{note.get('title')} (ID: {note.get('identifier')})" for note in notes]

    #
    # /grab-url API
    #
    grab_url_results = register_callback(callback, "grab-url")

    @mcp.tool()
    async def grab_url(
        url: str = Field(description="url to grab"),
        tags: list[str] | None = Field(
            description="list of tags. If tags are specified in the Bear’s web content preferences, this parameter is ignored.",
            default=None,
        ),
    ) -> str:
        """Create a new note with the content of a web page and return its unique identifier."""
        nonlocal grab_url_results

        params = {
            "url": url,
            "x-success": f"http://{callback_host}:{callback_port}/grab-url/success",
            "x-error": f"http://{callback_host}:{callback_port}/grab-url/error",
        }
        if tags is not None:
            params["tags"] = ",".join(tags)

        future = Future[QueryParams]()
        await grab_url_results.put(future)

        webbrowser.open(f"{BASE_URL}/grab-url?{urlencode(params, quote_via=quote)}")
        res = await future

        return res.get("identifier") or ""

    #
    # start servers
    #
    log_config = deepcopy(LOGGING_CONFIG)
    log_config["handlers"]["access"]["stream"] = "ext://sys.stderr"
    logger = logging.getLogger(__name__)

    callback_server = Server(
        Config(
            app=callback, host=callback_host, port=callback_port, log_config=log_config
        )
    )

    async def run_mcp_server() -> None:
        logger.info("Starting MCP server")
        try:
            await mcp.run_stdio_async()
        finally:
            callback_server.should_exit = True
        logger.info("MCP server stopped")

    async def run_callback_server() -> None:
        logger.info("Starting callback server")
        try:
            await callback_server.serve()
        except SystemExit:
            signal.raise_signal(signal.SIGTERM)
        logger.info("Callback server stopped")

    await asyncio.gather(run_mcp_server(), run_callback_server())


@click.command()
@click.option("--token", envvar="BEAR_API_TOKEN", required=True, help="Bear API token")
@click.option(
    "--callback-host",
    default="localhost",
    help="hostname or IP address of the callback server",
    show_default=True,
)
@click.option(
    "--callback-port",
    default=11599,
    help="port number on which the callback server is listening",
    show_default=True,
)
def main(token: str, callback_host: str, callback_port: int) -> None:
    """A MCP server for interacting with Bear note-taking software."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stderr),
        ],
    )

    asyncio.run(run_servers(token, callback_host, callback_port))


__all__: Final = ["main"]
