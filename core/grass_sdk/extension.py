import json
import time

import aiohttp
from aiohttp import WSMsgType

import uuid

from aiohttp_socks import ProxyConnector

from core.utils.exception import WebsocketClosedException, ProxyForbiddenException


class GrassWs:
    def __init__(self, user_agent: str = None, proxy: str = None, id: str = None):
        self.user_agent = user_agent
        self.proxy = proxy
        connector = ProxyConnector.from_url(proxy)
        self.session = aiohttp.ClientSession(connector=connector)
        self.websocket = None
        self.id = id

    async def connect(self):
        # 'proxy.wynd.network:4444', 'proxy.wynd.network:4650'
        # uri = ["wss://proxy2.wynd.network:4650/", "wss://proxy2.wynd.network:4444/"]
        uri = "wss://proxy2.wynd.network:4650/"

        headers = {
            'Pragma': 'no-cache',
            'Accept-Language': 'en-US,en;q=0.9,uk;q=0.8,ru-RU;q=0.7,ru;q=0.6,en-GB;q=0.5,pl;q=0.4',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:92.0) Gecko/20100101 Firefox/92.0',
            'Cache-Control': 'no-cache',
            'OS': 'Windows',
            'Platform': 'Desktop',
            'Browser': 'Mozilla',
        }

        try:
            self.websocket = await self.session.ws_connect(uri, proxy_headers=headers)
        except Exception as e:
            if 'status' in dir(e) and e.status == 403:
                raise ProxyForbiddenException(f"Low proxy score. Can't connect. Error: {e}")
            raise e

    async def send_message(self, message):
        # logger.info(f"Sending: {message}")
        await self.websocket.send_str(message)

    async def receive_message(self):
        msg = await self.websocket.receive()
        # logger.info(f"Received: {msg}")

        if msg.type == WSMsgType.CLOSED:
            raise WebsocketClosedException(f"Websocket closed: {msg}")

        return msg.data

    async def get_connection_id(self):
        msg = await self.receive_message()
        return json.loads(msg)['id']

    async def auth_to_extension(self, browser_id: str, user_id: str):
        connection_id = await self.get_connection_id()

        message = json.dumps(
            {
                "id": connection_id,
                "origin_action": "AUTH",
                "result": {
                    "browser_id": browser_id,
                    "user_id": user_id,
                    "user_agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:92.0) Gecko/20100101 Firefox/92.0',
                    "timestamp": int(time.time()),
                    "device_type": "desktop",
                    "version": "4.28.2",
                }
            }
        )

        await self.send_message(message)

    async def send_ping(self):
        message = json.dumps(
            {"id": str(uuid.uuid4()), "version": "1.0.0", "action": "PING", "data": {}}
        )

        await self.send_message(message)

    async def send_pong(self):
        connection_id = await self.get_connection_id()

        message = json.dumps(
            {"id": connection_id, "origin_action": "PONG"}
        )

        await self.send_message(message)
