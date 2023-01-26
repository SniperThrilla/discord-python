import subprocess
from typing import (
    IO,
    List
)
import aiohttp
import asyncio
import random
import logging
import socket
import time
import nacl.secret
import select

from .OggParser import OggStream

class FFmpegHandler():

    packet_iterator = None
    process: subprocess.Popen = None
    stdout : IO[bytes] = None
    stdin : IO[bytes] = None
    FRAME_SIZE : int = 20
    UDP_socket : socket.socket = None

    def __init__(self, args) -> None:
        self.open_process(args=args)

    def open_process(self, args):
        try:
            self.process = subprocess.Popen(args=args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
            self.stdout = self.process.stdout
            self.stdin = self.process.stdin
        except FileNotFoundError:
            raise FileNotFoundError("FFmpeg executable was not found.")

    def read(self):
        #size = int(48 * self.FRAME_SIZE * 4 / 12.18)
        #data = self.stdout.read(size)
        #if len(data) != size:
        #    return b''
        #return data

        return next(self.packet_iterator, b'')

class FFmpegPCM(FFmpegHandler):

    def __init__(self, source, executable_path = "ffmpeg") -> None:
        args = [
            executable_path, "-i", source, "-f", "s16le", "-ar", "48000", "-ac", "2", "-loglevel", "warning", "pipe:1"
        ]
        super().__init__(args)

class FFmpegOpus(FFmpegHandler):

    def __init__(self, source, executable_path = "ffmpeg") -> None:
        args = [
            executable_path, "-i", source, "-f", "opus", "-c:a", "libopus", "-ar", "48000", "-ac", "2", "-b:a", "128k", "-loglevel", "warning", "pipe:1"
        ]
        super().__init__(args)
        self.packet_iterator = OggStream(self.stdout).iterate_packets()




class VoiceClient():

    heartbeat_interval : int = None
    ssrc : int = None
    ip : str = None
    port : int = None
    modes = None
    ready : bool = False
    logger : logging.Logger = None
    secret_key : List[int] = None
    sock : socket.socket = None
    iteration : int = 0

    voice_ws : aiohttp.ClientWebSocketResponse = None

    sequence : int = 0
    timestamp : int = 0

    is_playing : bool = False

    def __init__(self, guild_id, channel_id, self_mute, self_deaf, client) -> None:
        self.client = client
        self.logger = client.logger
        print(self.logger)
        loop = asyncio.get_running_loop()
        loop.create_task(self.createVoiceWebsocketConnection(guild_id, channel_id, self_mute, self_deaf))
        pass

    async def createVoiceWebsocketConnection(self, guild_id, channel_id, self_mute, self_deaf):

        # TODO: Send websocket packet to get the endpoint to connect to.
        self.logger.debug("Creating voice websocket connection.")

        #await asyncio.sleep(5)

        payload = {"op": 4, "d": {"guild_id": guild_id, "channel_id": channel_id, "self_mute": self_mute, "self_deaf": self_deaf}}
        #payload = {"op": 4, "d": {"guild_id": "828553142604922951", "channel_id": "828553142604922951", "self_mute": self_mute, "self_deaf": self_deaf}}

        self.logger.debug(f"PAYLOAD: {payload}")

        await self.client.ws.send_json(payload)

        # TODO: Receive endpoint information.

        self.logger.debug("Sent VOICE UPDATE request.")

        while True:
            if self.client.voice_endpoint != None:
                break
            await asyncio.sleep(0)

        # TODO: Establish a voice websocket connection.

        self.logger.debug(f"Received voice endpoint: {self.client.voice_endpoint}")

        # TODO: Run asyncio.create_task() to communicate with it.
        asyncio.create_task(self.createVoiceWebsocket(self.client.voice_endpoint))

        self.client.voice_endpoint = None
        pass

    async def voiceWSHeartbeat(self, ws : aiohttp.ClientWebSocketResponse):
        """
        Sends heartbeats at a regular interval through the websocket connection.

        """

        while True:
                payload = {"op":3, "d":random.randint(0, 10000000)}
                self.logger.debug(f"VOICE PAYLOAD: {payload}")
                await ws.send_json(payload)
                self.logger.info(f"Sleeping for {self.heartbeat_interval / 1000} seconds...")
                await asyncio.sleep(self.heartbeat_interval / 1000)
                # Send the heartbeat with the previous sequence value to keep the connection alive.

    async def createVoiceWSListener(self, ws : aiohttp.ClientWebSocketResponse):
        while True:
            async for message in ws:
                self.logger.debug(f"Voice: {message.data}")
                if message.type == aiohttp.WSMsgType.TEXT:
                    message_json = message.json()
                    if message_json['op'] == 2:
                        # Ready event
                        data = message_json['d']
                        self.ssrc = data['ssrc']
                        self.ip = data['ip']
                        self.port = data['port']
                        self.modes = data['modes']
                    if message_json['op'] == 3:
                        self.logger.warning(f"Weird heartbeat acknowledgement?! Are we using the correct API version?")
                    if message_json['op'] == 4:
                        self.logger.debug("Encryption key received.")
                        self.secret_key = message_json['d']['secret_key']
                    if message_json['op'] == 6:
                        self.logger.debug(f"Voice heartbeat acknowledeged")
                    if message_json['op'] == 8:
                        # Heartbeat interval
                        self.logger.debug("Initial heartbeat interval sent.")
                        self.heartbeat_interval = message_json['d']['heartbeat_interval']
                        loop = asyncio.get_running_loop()
                        loop.create_task(self.voiceWSHeartbeat(ws))

    async def createVoiceWebsocket(self, url):
        # TODO: Create a new websocket and save it
        self.voice_ws = await self.client.session.ws_connect("wss://" + url + "?v=4")

        # TODO: Identify
        identify_payload = {
        "op": 0,
        "d": {
            "server_id": self.client.voice_guild,
            "user_id": self.client.voice_user_id,
            "session_id": self.client.voice_session,
            "token": self.client.voice_token
            }
        }

        await self.voice_ws.send_json(identify_payload)

        self.client.voice_guild = None
        self.client.voice_user_id = None
        self.client.voice_session = None
        self.client.voice_token = None

        # TODO: Create a new listener
        loop = asyncio.get_running_loop()
        loop.create_task(self.createVoiceWSListener(self.voice_ws))

        # TODO: Establish UDP connection
        # socket library seems useful
        self.sock = socket.socket(family=socket.AddressFamily.AF_INET, type=socket.SOCK_DGRAM)

        # Wait for identify payload
        while self.ssrc == None:
            await asyncio.sleep(0)

        # TODO: Connect to UDP port provided
        self.sock.connect((self.ip, self.port))
        self.sock.setblocking(0)

        # TODO: Send the IP Discovery package

        byte_array = bytearray(b'\x00\x01')
        byte_array.extend(int(70).to_bytes(2, byteorder="big"))
        byte_array.extend(int(self.ssrc).to_bytes(4, byteorder="big"))
        byte_array.extend(b"\x00" * 64)
        byte_array.extend(b"\x00" * 2)
        
        self.logger.debug(f"SENING UDP PACKET: {byte_array.hex()}")

        result = self.sock.send(byte_array)

        self.logger.debug(f"Sent byte array through UDP socket. RESULT: {result}")

        select.select([self.sock], [], [])

        result = self.sock.recv(2048)
        self.logger.debug(result.hex())

        method = result[:2]
        length = result[2:4]
        ssrc = result[4:8]
        address = result[8:72]
        port = result[72:74]
        local_ip = address.decode('utf-8')
        local_port = int.from_bytes(port, 'big')

        self.logger.debug(f"IP Discovery successful, our External IP and Port: {local_ip}:{local_port}")

        # TODO: Send OP 1 SELECT PROTOCAL with our found external IP and PORT

        select_protocol_payload = {
            "op": 1,
            "d": {
                "protocol": "udp",
                "data": {
                    "address": local_ip,
                    "port": local_port,
                    "mode": "xsalsa20_poly1305"
                }
            }
        }

        await self.voice_ws.send_json(select_protocol_payload)

        self.ready = True

        loop.create_task(self.listen_udp())
        self.logger.debug(f"Select protocol sent.")

    async def listen_udp(self):
        while True:
            while select.select([self.sock], [], [], 0) == ([], [], []):
                await asyncio.sleep(0)
            resp = self.sock.recv(2048)
            await asyncio.sleep(0)
            #print(resp)

    async def do_play(self, source : FFmpegHandler):
        while not self.ready:
            await asyncio.sleep(0)

        self.logger.debug('is playing')

        self.is_playing = True

        await self.start_speaking()

        start_play = True
        data = b''
        start = time.time()
        next_time = time.time()
        self.iteration = 0
        print("Starting audio transmission.")
        while data != b'' or start_play:
            start_play = False
            data = source.read()
            
            self.iteration += 1

            # TODO: Send audio packet
            await self.send_audio_packet(data)
            await asyncio.sleep(max(0, next_time - time.time()))
            next_time = start + 0.02 * self.iteration
        print(f"Played for {time.time()-start} seconds.")

        self.is_playing = False

    async def send_audio_packet(self, data : bytes):

        # TODO: Encrypt audio data with PyNaCl
        while self.secret_key == None:
            await asyncio.sleep(0)

        header = bytearray(b'\x80\x78')
        header.extend(int(self.sequence).to_bytes(2, byteorder="big"))
        header.extend(int(self.timestamp).to_bytes(4, byteorder="big"))
        header.extend(int(self.ssrc).to_bytes(4, byteorder="big"))

        nonce = bytearray(24)
        nonce[:12] = header

        box = nacl.secret.SecretBox(bytes(self.secret_key))
        encrypted_data = box.encrypt(bytes(data), bytes(nonce)).ciphertext

        # TODO: Craft the packet to be sent
        packet = bytearray()
        packet.extend(header)
        packet.extend(encrypted_data)

        # TODO: Send the packet
        result = self.sock.send(packet)
        self.logger.debug(f"Sent voice packet of {result} bytes")

        self.sequence += 1
        self.timestamp += 960
        if self.sequence >= 2 ** 16: self.sequence = 0
        if self.timestamp >= 2 ** 32: self.timestamp = 0
        pass

    async def play(self, source: FFmpegHandler):
        loop = asyncio.get_running_loop()
        loop.create_task(self.do_play(source))
        await asyncio.sleep(1)

    async def start_speaking(self):

        speaking_payload = {
            "op": 5,
            "d": {
                "speaking": 1,
                "delay": 0,
                "ssrc": self.ssrc
            }
        }

        await self.voice_ws.send_json(speaking_payload)

    async def stop_speaking(self):

        speaking_payload = {
            "op": 5,
            "d": {
                "speaking": 0,
                "delay": 0,
                "ssrc": self.ssrc
            }
        }

        await self.voice_ws.send_json(speaking_payload)