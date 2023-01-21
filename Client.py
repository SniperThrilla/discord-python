import requests
import aiohttp
import asyncio
import json
import random
import ApplicationCommands
import Message
import logging
import Logger
import InteractionResponder
import string

from typing import (
    List
)

class Client:

    resume_gateway_url = None
    gateway_url = None
    discord_http_api_base = "https://discord.com/api/v10"
    discord_http_oauth_base = "https://discord.com/api/oauth2"
    bot_token = None
    event_loop = None
    heartbeat_interval : int = None
    last_sequence : int = None
    first_heartbeat : bool = True
    heartbeats_sent : bool = False
    session_id = None
    functions = []
    ready_event_occurred : bool = False
    commands : List[ApplicationCommands.ApplicationCommand] = []
    application_id = None
    messageQueue : List[Message.Message] = []
    logger : logging.Logger = None
    message_callbacks : List[ApplicationCommands.MessageComponentCallback] = []

    # Implementing this class will allow users to create a websocket session with discord.
    def __init__(self, debug_level=logging.INFO) -> None:
        """
        Creates a client to be used which the application will centre around.
        Logging levels are also determined here.

        Parameters
        ----------
        debug_level: :class:`int`
            The level at which the debugger will be set. Defaults to `logging.INFO`.
            For debug purposes, set this to `logging.DEBUG`.
        """
        
        self.functions = [self.websocketListener(),
            self.heartbeat(),
            self.identify(),
            self.interactionQueue()]

        self.logger = logging.getLogger("Logging")
        self.logger.setLevel(debug_level)
        ch = logging.StreamHandler()
        ch.setLevel(debug_level)
        ch.setFormatter(Logger.CustomFormatter())
        self.logger.addHandler(ch)

        pass

    def isReady(self) -> bool:
        """
        Returns true if the ready gateway event has occurred.
        This always occurs after identifying.

        Returns
        ----------
        :class:`bool`
            Whether the ready gateway event has occurred or not.
        """
        return self.ready_event_occurred

    async def waitForReady(self) -> None:
        """
        A shorthand coroutine for waiting for the ready event to occur.
        Can be awaited to make a coroutine not send information too early.

        """
        while True:
            if self.isReady():
                return
            await asyncio.sleep(0)

    def syncApplicationCommands(self):
        """
        A shorthand for adding the `syncCommands()` function to `self.functions`. This causes 
        all global commands to be synced when the ready event is received. 

        """
        self.registerAsyncEvent(self.syncCommands())

    def registerAsyncEvent(self, function):
        """
        Registers a coroutine to be run in the event loop with the other main functions,
        such as heartbeat. This should be used mainly for gateway events, such as controlling
        presence, but can be used to make continuous coroutines.

        Parameters
        -------
        function: `function`
            The function you want to register.

        Warning
        -------
        You should always include an `await asyncio.sleep(0)` so that your
        function does not stop the other crucial functions from occurring.

        """
        # Registers a new coroutine to be run.
        self.functions.append(function)

    def getWebsocketInstance(self):
        """
        Simply returns the websocket instance. This should not be used often, but can be used
        to have lower-level control over your bot, allowing you to send custom websocket messages.

        Warning
        -------
        The websocket will not work correctly unless it is in the same event loop as the other main
        functions. You should register your new function using the websocket with `registerAsyncEvent()`.

        """
        return self.ws

    def run(self, bot_token) -> None:
        """
        The function responsible for actually starting your bot. After getting the gateway URL, it
        will run all functions that are currently in `self.functions`. `registerAsyncEvent()` will
        have no effect from this point onwards.

        Parameters
        -------
        bot_token: `str`
            The token for your bot. Get this from the discord developer portal. Never tell anyone this
            token, as it will give them access to your bot.

        Warning
        -------
        All calls to `registerAsyncEvent()` should be called prior to running this. This includes 
        `syncApplicationCommands()`, as it also registers events.

        """
        self.bot_token = bot_token
        self.getGatewayBotURL()
        self.eventHandler(self.gateway_url)

    def eventHandler(self, gateway_url):
        """
        The function responsible for running any coroutines. A new event loop is created, and then after
        a websocket connection is made, all coroutines in `self.functions` are run.

        Parameters
        -------
        gateway_url: `str`
            The URL that will be used for creating the websocket connection.

        Warning
        -------
        If there are no functions present in `self.functions` for whatever reason, or all functions 
        return, the bot will disconnect and your session will be closed.

        """
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())        

        self.event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.event_loop)
        self.event_loop.run_until_complete(self.createWebsocketConnection(gateway_url))
        self.event_loop.run_until_complete(self.runHandler())
        self.event_loop.close()
        self.session.close()

    async def runHandler(self):
        """
        Runs all coroutines in `self.functions` at once.

        """
        self.logger.debug(f"Coroutines to be run: {self.functions}")
        await asyncio.gather(
            *self.functions
        )
        pass

    def getGatewayBotURL(self):
        """
        Retrieves the URL that the bot should connect to for establishing a connection with the gateway.

        """

        # Gets the gateway URL that the program should use.
        response = requests.get(self.discord_http_api_base + "/gateway/bot", headers={'Authorization': f'Bot {self.bot_token}'})
        response_json = response.json()
        self.gateway_url = response_json['url']
        # As per discord documentation, the resume gateway should initially be the same.
        self.resume_gateway_url = response_json['url']

    async def createWebsocketConnection(self, gateway_url):
        """
        Creates the websocket connection that will be used. The http session is also created here.

        Parameters
        -------
        gateway_url: `str`
            The URL that will be used for creating the websocket connection.

        """
        self.session = aiohttp.ClientSession()
        self.ws = await self.session.ws_connect(gateway_url)

    async def websocketListener(self):
        """
        Continuously listens for messages from the websocket server. After receiving a message,
        it will determine how it should be handled, and call the appropriate functions. When a message
        is received, the sequence value is updated for future heartbeats.

        Warning
        -------
        The bot currently cannot reconnect if disconnected. Some operation codes are missing which
        will be implemented in a future version.

        """
        while True:
            async for message in self.ws:
                if message.type == aiohttp.WSMsgType.TEXT:
                    message_data = json.loads(message.data)
                    if message_data['op'] == 0:
                        # The application has received a dispatch event.
                        if message_data['t'] == 'READY':
                            # Ready event received. The application should save the resume gateway url.
                            self.resume_gateway_url = message_data['d']['resume_gateway_url']
                            self.session_id = message_data['d']['session_id']
                            self.ready_event_occurred = True

                        if message_data['t'] == 'INTERACTION_CREATE':
                            if message_data['d']['type'] == 2:
                                # An application command was received! Wahoo!

                                # Determines which function to callback to for this command.
                                for command in self.commands:
                                    if command.name == message_data['d']['data']['name']:
                                        if 'options' in message_data['d']['data']:
                                            command.function(client=self, interaction=InteractionResponder.Interaction(message_data['d']['id'], message_data['d']['token'], bot_token=self.bot_token, options=message_data['d']['data']['options']))
                                        else:
                                            command.function(client=self, interaction=InteractionResponder.Interaction(message_data['d']['id'], message_data['d']['token'], bot_token=self.bot_token))

                            if message_data['d']['type'] == 3:
                                # An message component interaction was received!

                                # Determines which function to callback to for this command.
                                for message_callback in self.message_callbacks:
                                    if message_callback.custom_id == message_data['d']['data']['custom_id']:
                                        #command.function(self, message_data['d']['id'], message_data['d']['token'])
                                        message_callback.function(client=self, interaction=InteractionResponder.Interaction(message_data['d']['id'], message_data['d']['token'], bot_token=self.bot_token))

                    if message_data['op'] == 1:
                        # The application should immediately send a heartbeat.
                        await self.ws.send_json({"op":1, "d":self.last_sequence})
                        self.logger.info(f"Heartbeat requested, and has been sent.")
                    
                    if message_data['op'] == 7:
                        # Reconnect to the websocket server.
                        await self.reconnect()

                    if message_data['op'] == 10:
                        self.heartbeat_interval = message_data['d']['heartbeat_interval']
                        self.logger.info(f"Heartbeat interval: {self.heartbeat_interval}")
                    if message_data['op'] == 11:
                        self.logger.info(f"Heartbeat acknowledged.")
                        self.heartbeats_sent = True
                    
                    if message_data['s'] != None:
                        self.last_sequence = message_data['s']

                    self.logger.debug(message_data)
                if message.type == aiohttp.WSMsgType.CLOSE:
                    self.logger.critical(f"CLOSE PACKET RECEIVED {message.data}")
                if message.type == aiohttp.WSMsgType.ERROR:
                    self.logger.error(f"ERROR PACKET RECEIVED {message.data}")
            await asyncio.sleep(0)

    async def heartbeat(self):
        """
        Sends heartbeats at a regular interval through the websocket connection. This function will
        set `self.first_heartbeat` to False after sending the first heartbeat. When the heartbeat is 
        acknowledged, `self.heartbeats_sent` will also be set to True.

        """
        while True:
            if self.heartbeat_interval != None:
                # This only runs if we have received the heartbeat interval. 
                if self.first_heartbeat:
                    self.first_heartbeat = False
                    interval = random.uniform(0, 1)
                    self.logger.info(f"Sleeping for {interval} * {self.heartbeat_interval} = {interval * self.heartbeat_interval / 1000} seconds...")
                    await asyncio.sleep(interval * self.heartbeat_interval / 1000)
                else:
                    self.logger.info(f"Sleeping for {self.heartbeat_interval / 1000} seconds...")
                    await asyncio.sleep(self.heartbeat_interval / 1000)
                # Send the heartbeat with the previous sequence value to keep the connection alive.
                await self.ws.send_json({"op":1, "d":self.last_sequence})
                
            await asyncio.sleep(0)

    async def identify(self):
        """
        Identifies the bot via the websocket connection. The opcode `2` is used to signify this is an identify
        event. This will only run after the first heartbeat has been both sent and acknowledged.

        """
        # Sends a packet with opcode 2 to identify the bot. Only sent when the first heartbeat has been sent.
        while True:
            if self.heartbeats_sent:
                await self.ws.send_json({"op":2, "d":{"token": self.bot_token, "intents": 0, "properties": {"os": "Windows", "browser": "amongus", "device": "amongus"}}})
                break
            await asyncio.sleep(0)
        
    async def interactionQueue(self):
        """
        The interaction queue is responsible for sending HTTP messages to the discord API. `self.messageQueue` holds
        any messages to be sent, and each iteration of this function sends the oldest message and removes it from the 
        queue.

        Warning
        -------
        This function is for use with the Message class. Attempting to add other classes may cause issues when sending them 
        to the API endpoint. However, if done correctly, you can create a class to provide additional functionality through 
        overwriting the `performHTTPAction()` function.

        """
        # Allows functions registered by the user to send information to discord.
        while not self.isReady():
            await asyncio.sleep(0)
        
        while True:
            if len(self.messageQueue) == 0:
                await asyncio.sleep(0)
                continue

            # Send the first interaction.
            interaction = self.messageQueue[0]

            await interaction.performHTTPAction(self.session)

            self.messageQueue.pop(0)
            await asyncio.sleep(0)

    async def reconnect(self):
        """
        The function responsible for reconnecting to the gateway server in the event that we were 
        disconnected and we are allowed to reconnect.

        Warning
        -------
        This has not been implemented yet.

        """
        pass

    async def syncCommands(self) -> None:
        """
        Syncs the global commands to discord. Iterates through all commands in `self.commands` and 
        uploads them to discord. If your command is not being synced, make sure you have registered it
        with `registerApplicationCommand()` and set a callback function.

        Warning
        -------
        No commands will be available in discord unless this function is called.

        """
        self.logger.debug("Request to sync application commands has been loaded into coroutine list successfully.")
        while not self.isReady():
            await asyncio.sleep(0)
        self.logger.info("Syncing application commands.")
        if not self.application_id:
            await self.getApplicationInfo()
        self.logger.debug(f"Found application_id: {self.application_id}")
        for command in self.commands:
            option_json = command.generateJSON()
            if option_json == []:
                json = {
                    "name": command.name,
                    "type": command.type,
                    "description": command.description,
                }
            else:
                # HAS PARAMETERS
                json = {
                    "name": command.name,
                    "type": command.type,
                    "description": command.description,
                    "options": option_json,
                }
            url = self.discord_http_api_base + f"/applications/{self.application_id}/commands"
            headers={'Authorization': "Bot " + self.bot_token}

            result = await self.session.post(url=url, json=json, headers=headers)
        self.logger.info("Synced all commands successfully.")

    def registerApplicationCommand(self, name, type, description, function, parameters = []) -> None:
        """
        Allows you to register an application command. This does not sync the command,
        so it will not appear in discord. Use `syncCommands()` in addition to this to make
        them usable.

        Parameters
        -------
        name: `str`
            The name of your application command. This is what the user will use to run it, for
            example setting this to "help" will mean that the function will be used via /help if
            it is a slash command.
        type: `int`
            The type of command you are registering. Use the `Enums.ApplicationCommand` enum to 
            see which value you should use.
        description: `str`
            The description of the application command. This is shown as the description of the 
            command when being used in discord.
        function: `function`
            The function that will be run whenever someone uses your command in discord. Your
            function **MUST** have the parameters client and interaction of type Client and 
            Interaction respectively.

        Warning
        -------
        Your function should respond to the interaction in some manner, otherwise discord will
        say that the application did not respond. You can easily do this by creating an `InteractionResponse`
        and then making a `Message` to be added onto the `messageQueue`.

        """
        command = ApplicationCommands.ApplicationCommand(name, type, description, function, parameters)
        self.commands.append(command)

    def getRegisteredCommands(self) -> List[ApplicationCommands.ApplicationCommand]:
        """
        Returns all registered commands. In the event that `syncCommands()` was called, these
        are the commands that would be synced.


        Returns
        -------
        :class:`List[ApplicationCommands.ApplicationCommand]`
            A list of all the application commands that are registered inside of `self.commands`

        """
        return self.commands

    async def getApplicationInfo(self):
        """
        Retrieves the information of the application. The OAuth2 endpoint /applications/@me is called. 
        The only information needed here is the id of the application, but more information is accessible.

        """
        async with self.session.get(self.discord_http_oauth_base + "/applications/@me", headers={'Authorization': "Bot " + self.bot_token}) as response:
            json_message = json.loads(await response.text())
            self.application_id = json_message["id"]

    def generateCustomID(self, custom_id):
        return ''.join(random.choice(string.ascii_lowercase) for i in range(20)) + "_" + custom_id
