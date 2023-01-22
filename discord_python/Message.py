# Messages to be sent to discord should be in this form for the queue to handle.

from enum import Enum, IntEnum
import aiohttp
import asyncio
import logging

class HTTPMethods(Enum):
    GET = 1
    POST = 2
    PUT = 3
    PATCH = 4

class InteractionCallbackType(IntEnum):
    PONG = 1
    CHANNEL_MESSAGE_WITH_SOURCE = 4
    DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE = 5
    DEFERRED_UPDATE_MESSAGE = 6
    UPDATE_MESSAGE = 7
    APPLICATION_COMMAND_AUTOCOMPLETE_RESULT = 8
    MODAL = 9

class Message:
    url : str = None
    method = None
    json = None
    client = None
    logger = None

    def __init__(self, url, method, json, client) -> None:
        self.url = url
        self.method = method
        self.json = json
        self.client = client
        self.logger = logging.getLogger("Logging")

    async def performHTTPAction(self, http : aiohttp.ClientSession):
        self.headers = {
        "Authorization": "Bot " + self.client.bot_token
        }

        if self.method == HTTPMethods.GET:
            return
        if self.method == HTTPMethods.POST:
            self.logger.debug(f"Sending JSON: {self.json} to {self.url}")
            result = await http.post(url=self.url, json=self.json, headers=self.headers)
            self.logger.debug(f"Posting from queue - Response: {result.status}")
            self.logger.debug(f"Text received: f{await result.text()}")
            return
        if self.method == HTTPMethods.PUT:
            return
        if self.method == HTTPMethods.PATCH:
            return